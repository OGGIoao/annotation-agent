from fastapi import FastAPI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel


class SmokePayload(BaseModel):
    task_id: str


def test_core_dependencies_import_and_contract() -> None:
    assert FastAPI is not None
    assert StateGraph is not None
    assert START == "__start__"
    assert END == "__end__"
    assert SmokePayload(task_id="smoke").task_id == "smoke"
