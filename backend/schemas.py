from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class CandidateBox(BaseModel):
    id: str
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    corner_radius: int = Field(ge=0)
    score: float = Field(ge=0.0)
    selected: bool = True


class DetectResponse(BaseModel):
    image_width: int = Field(gt=0)
    image_height: int = Field(gt=0)
    candidates: List[CandidateBox]
    message: Optional[str] = None
