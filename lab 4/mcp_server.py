import os

import httpx

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

API_FITNESS = os.getenv("API_FITNESS")

mcp = FastMCP("fitness-mcp")

ACTIVITY_MAP = {
    "low": 1.2,
    "medium": 1.55,
    "high": 1.9,
}

GOAL_MAP = {
    "lose": -500,
    "maintain": 0,
    "gain": 300,
}


MUSCLE_MAP = {
    "грудь": "chest",
    "грудная мышца": "chest",
    "спина": "back",
    "ноги": "legs",
    "руки": "arms",
    "плечи": "shoulders",
}

TRANSLATIONS = {
    "Push-Up": "Отжимания",
    "Bench Press": "Жим лёжа",
    "Pull Up": "Подтягивания",
    "Squat": "Приседания",
}

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

    return mapping.get(
        value.lower().strip(),
        value.lower().strip(),
    )

@mcp.tool()
def calculate_calories(
    weight: float,
    height: float,
    age: int,
    gender: str,
    activity: str,
    goal: str,
) -> dict:

    if weight <= 0:
        raise ValueError("Weight must be > 0")

    if height <= 0:
        raise ValueError("Height must be > 0")

    if age <= 0:
        raise ValueError("Age must be > 0")

    gender = normalize(gender)
    activity = normalize(activity)
    goal = normalize(goal)

    if gender == "male":

        bmr = (
            10 * weight +
            6.25 * height -
            5 * age + 5
        )

    else:

        bmr = (
            10 * weight +
            6.25 * height -
            5 * age - 161
        )

    calories = (
        bmr *
        ACTIVITY_MAP.get(activity, 1.2) +
        GOAL_MAP.get(goal, 0)
    )

    protein = weight * 2
    fat = weight * 0.8

    carbs = (
        calories -
        (protein * 4 + fat * 9)
    ) / 4

    return {
        "calories": round(calories),
        "protein": round(protein),
        "fat": round(fat),
        "carbs": round(carbs),
    }


@mcp.tool()
async def find_exercises(
    muscle: str
) -> list[dict]:

    muscle = MUSCLE_MAP.get(
        muscle.lower().strip(),
        muscle.lower().strip(),
    )

    url = (
        "https://api.api-ninjas.com/v1/exercises"
        f"?muscle={muscle}"
    )

    headers = {
        "X-Api-Key": API_FITNESS
    }


    async with httpx.AsyncClient() as client:

        response = await client.get(
            url,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

    result = []

    for item in data[:5]:

        result.append({
            "name": TRANSLATIONS.get(
                item.get("name", ""),
                item.get("name", "")
            ),
            "difficulty": item.get(
                "difficulty",
                "unknown"
            ),
            "equipment": item.get(
                "equipment",
                "body"
            ),
            "sets": 4,
            "reps": "10-12",
        })

    return result


@mcp.tool()
def calculate_bmi(
    weight: float,
    height: float
) -> dict:

    if weight <= 0:
        raise ValueError("Weight must be > 0")

    if height <= 0:
        raise ValueError("Height must be > 0")

    bmi = weight / (
        (height / 100) ** 2
    )

    return {
        "bmi": round(bmi, 2)
    }

if __name__ == "__main__":
    mcp.run("stdio")