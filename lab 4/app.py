from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from pydantic import Field

import uvicorn

from agent import agent_manager
from schemas import AgentResponse


class Query(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=2000,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):

    await agent_manager.get_agent()

    yield


app = FastAPI(
    title="Fitness MCP Agent",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post(
    "/generate",
    response_model=AgentResponse,
)
async def generate(
    query: Query
):

    response = await agent_manager.run(
        query.message
    )

    return response


if __name__ == "__main__":

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
