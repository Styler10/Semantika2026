import asyncio
import os
from typing import Optional

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient

from schemas import AgentResponse
from skills import build_system_prompt

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=GROQ_API_KEY,
    temperature=0,
)


class AgentManager:

    def __init__(self):

        self._agent: Optional[object] = None
        self._lock = asyncio.Lock()

    async def build_agent(self):

        client = MultiServerMCPClient(
            {
                "fitness": {
                    "command": "python",
                    "args": ["mcp_server.py"],
                    "transport": "stdio",
                }
            }
        )

        tools = await client.get_tools()

        if not tools:
            raise RuntimeError(
                "MCP tools not loaded"
            )

        model = llm.bind_tools(tools)

        structured_model = (
            model.with_structured_output(
                AgentResponse
            )
        )

        return structured_model

    async def get_agent(self):

        if self._agent is not None:
            return self._agent

        async with self._lock:

            if self._agent is None:

                self._agent = (
                    await self.build_agent()
                )

        return self._agent

    async def run(
        self,
        message: str,
    ) -> AgentResponse:

        message = message.strip()

        model = await self.get_agent()

        system_prompt = build_system_prompt(
            message
        )

        response = await model.ainvoke(
            [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": message,
                }
            ]
        )

        return response


agent_manager = AgentManager()
