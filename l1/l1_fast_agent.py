from dotenv import load_dotenv
from dataclasses import dataclass
from langchain_community.utilities import SQLDatabase
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from langgraph.runtime import get_runtime
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

load_dotenv()


db = SQLDatabase.from_uri("sqlite:///Chinook.db")


@dataclass
class RuntimeContext:
    db:SQLDatabase
    
@tool
def execute_sql(query: str) -> str:
    """Execute a SQLite command and return results"""
    
    runtime = get_runtime(RuntimeContext)
    db = runtime.context.db
    
    try:
        return db.run(query)
    except Exception as e:
        return f"Error executing SQL: {e}"




SYSTEM_PROMPT = """You are a careful SQLite analyst.

Rules:
- Think step-by-step.
- When you need data, call the tool `execute_sql` with ONE SELECT query.
- Read-only only; no INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/TRUNCATE.
- Limit to 5 rows of output unless the user explicitly asks otherwise.
- If the tool returns 'Error:', revise the SQL and try again.
- Prefer explicit column lists; avoid SELECT *.
"""

agent = create_agent(
    model= ChatOllama(
    model="qwen3.5:9b",
    temperature=0,
    num_ctx=8192,
    num_predict=-1,
    reasoning=False, #Needed this to output the full text, as the <thinking> tokens stopped the final ouput to be full printed in the notebook
),
    tools=[execute_sql],
    system_prompt=SYSTEM_PROMPT,
    context_schema=RuntimeContext,
)

question = " Which table has the fewest number of entries?"
for step in agent.stream(
    {"messages": question},
    context=RuntimeContext(db=db),
    stream_mode="values",
    


):
    step["messages"][-1].pretty_print()
    

