from pydantic import BaseModel, Field
from typing import Any

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)

class OptimizeRequest(BaseModel):
    actions: list[str] = []

class ReelOut(BaseModel):
    id: int
    filename: str
    status: str
    duration: str | None = None
    transcript: str = ""
    analysis: dict[str, Any] = {}
    optimized_url: str | None = None
