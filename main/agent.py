import os
import json
import requests
from typing import Dict, Any
from dotenv import load_dotenv

from pydantic import BaseModel
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from langchain.agents import create_agent

load_dotenv()

class CalorieInput(BaseModel):
    weight: float
    height: float
    age: int
    gender: str
    activity: str
    goal: str

class ExerciseInput(BaseModel):
    muscle: str 

def normalize(value: str) -> str:
    mapping = {
        "мужской": "male",
        "женский": "female",

        "низкая": "low",
        "средняя": "medium",
        "высокая": "high",

        "сброс веса": "lose",
        "похудение": "lose",
        "поддержание": "maintain",
        "набор": "gain",
    }
    return mapping.get(value.lower(), value)

def normalize_muscle(muscle: str) -> str:
    mapping = {
        "грудь": "chest",
        "грудная мышца": "chest",
        "спина": "back",
        "ноги": "legs",
        "руки": "arms",
        "плечи": "shoulders",
    }
    return mapping.get(muscle.lower(), muscle)

def calculate_calories(data: Dict[str, Any]) -> Dict[str, Any]:
    activity_map = {"low": 1.2, "medium": 1.55, "high": 1.9}
    goal_map = {"lose": -500, "maintain": 0, "gain": 300}

    gender = normalize(data["gender"])
    activity = normalize(data["activity"])
    goal = normalize(data["goal"])

    if gender == "male":
        bmr = 10 * data["weight"] + 6.25 * data["height"] - 5 * data["age"] + 5
    else:
        bmr = 10 * data["weight"] + 6.25 * data["height"] - 5 * data["age"] - 161

    calories = bmr * activity_map.get(activity, 1.2) + goal_map.get(goal, 0)

    protein = data["weight"] * 2
    fat = data["weight"] * 0.8
    carbs = (calories - (protein * 4 + fat * 9)) / 4

    return {
        "calories": round(calories),
        "protein": round(protein),
        "fat": round(fat),
        "carbs": round(carbs),
    }

@tool(args_schema=CalorieInput)
def calorie_calculator(weight, height, age, gender, activity, goal) -> str:
    """Calculate daily calories and macronutrients (protein, fat, carbs)."""

    data = {
        "weight": weight,
        "height": height,
        "age": age,
        "gender": gender,
        "activity": activity,
        "goal": goal,
    }

    result = calculate_calories(data)
    return json.dumps(result, ensure_ascii=False)

@tool(args_schema=ExerciseInput)
def exercise_finder(muscle: str) -> str:
    """Find exercises for a given muscle group."""

    muscle = normalize_muscle(muscle)

    url = f"https://api.api-ninjas.com/v1/exercises?muscle={muscle}"
    headers = {"X-Api-Key": os.getenv("API_FITNESS")}

    res = requests.get(url, headers=headers)
    data = res.json()

    result = [
        {
            "name": e.get("name"),
            "difficulty": e.get("difficulty"),
            "equipment": e.get("equipment"),
        }
        for e in data[:5]
    ]

    return json.dumps(result, ensure_ascii=False)


tools = [calorie_calculator, exercise_finder]

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KeY"),
    temperature=0,
)

system_prompt="""
Ты — профессиональный фитнес AI-ассистент.

ТВОЯ РОЛЬ:
- Ты составляешь программы тренировок
- Ты используешь инструменты (tools) как источник данных
- Ты адаптируешь результаты tools для пользователя

ПРАВИЛА:
- Используй tools, если нужны упражнения или расчёты
- НЕ придумывай упражнения, если можно получить их через exercise_finder
- После получения данных из tool — ОБРАБОТАЙ их перед ответом

КРИТИЧЕСКОЕ:
1. Все упражнения сначала получаются через exercise_finder
2. Затем ты ОБЯЗАН:
   - перевести названия упражнений на русский
   - при необходимости адаптировать (понятно для пользователя)
3. После этого ты формируешь итоговый ответ
4. Если запрос НЕ относится к фитнесу, питанию или тренировкам,
  ты ОБЯЗАН ответить ТОЛЬКО:
  "Команда неизвестна"

    - НЕ объясняй
    - НЕ дополняй
    - НЕ пытайся ответить
    - НЕ давай советов
    - Просто верни строку: "Команда неизвестна"

ПЕРЕВОД:
- Переводи названия упражнений на русский язык
- НЕ оставляй английские названия
- НЕ смешивай русский и английский в одном слове
- Если не уверен в переводе — дай понятное описание упражнения на русском

ФОРМАТ:
- Ответ на русском
- Структурированный план тренировок
- Указывай подходы и повторения
- Можно добавить краткие пояснения

ДОПОЛНИТЕЛЬНО:
- Ты МОЖЕШЬ добавить рекомендации от себя (разминка, отдых, советы)
- Но упражнения должны приходить из tools
"""

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt
)