from typing import Optional, List
from pydantic import BaseModel
from datetime import date


class Umthes(BaseModel):
    id: int
    label: Optional[str]


class Organisation(BaseModel):
    name: str
    role: str


class Coordinates(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    min: Coordinates
    max: Coordinates


class Item(BaseModel):
    id: str
    title: str
    score: Optional[float] = None
    description: Optional[str] = None
    bounding_boxes: Optional[List[BoundingBox]] = None
    source_url: Optional[str] = None
    organisations: Optional[List[Organisation]] = None
    issued: Optional[date] = None
    umthes: Optional[List[Umthes]] = None
