from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

from agent import agent

app = FastAPI()

class Query(BaseModel):
    message: str

@app.post("/generate")
async def chat(query: Query):
    result = agent.invoke({
        "messages": [
            {"role": "user", "content": query.message}
        ]
    })

    return {
        "response": result["messages"][-1].content
    }

@app.get("/")
async def root():
    return {"status": "Fitness AI agent"}


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )