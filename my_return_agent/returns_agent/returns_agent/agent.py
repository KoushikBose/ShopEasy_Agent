"""The Returns Agent = LLM + tools + prompt + memory + a limit on the loop."""

import warnings
from datetime import date

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolCallLimitMiddleware
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver

from prompts import PROMPTS, CURRENT
from tools import get_orders, search_knowledge, book_return, book_exchange

load_dotenv()                                                              # reads GROQ_API_KEY from .env
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")  # hides a harmless warning


# Builds the agent with one prompt version (evals.py tries both)
def build_agent(version=CURRENT):
    today = date.today().strftime("%d %B %Y")
    return create_agent(
        model=ChatGroq(model="openai/gpt-oss-120b", max_retries=8),     # the LLM (retries if Groq is busy)
        tools=[get_orders, search_knowledge, book_return, book_exchange],
        system_prompt=PROMPTS[version].format(today=today),
        checkpointer=InMemorySaver(),                                    # remembers the conversation
        middleware=[ToolCallLimitMiddleware(run_limit=10)],              # at most 10 tool calls per message
    )


agent = build_agent()