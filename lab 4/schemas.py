from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ExerciseResult(BaseModel):
    name: str
    difficulty: str
    equipment: str
    sets: int = 4
    reps: str = "10-12"


class NutritionResult(BaseModel):
    calories: int
    protein: int
    fat: int
    carbs: int


class AgentResponse(BaseModel):
    success: bool
    message: str

    exercises: List[ExerciseResult] = Field(
        default_factory=list
    )

    nutrition: Optional[NutritionResult] = None