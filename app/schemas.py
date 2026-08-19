"""
Pydantic schemas — define what a valid API request/response looks like.
Kept separate from DB models on purpose: the API shape and the storage
shape will diverge as we add fields (e.g. we won't let clients set
`category` directly — that's set by the NLU pipeline in a later step).
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class CitizenRequestCreate(BaseModel):
    raw_text: str = Field(..., min_length=3, description="The citizen's request, in their own words")
    channel: str = Field(default="web", description="web | sms | whatsapp | ivr")
    location_text: Optional[str] = Field(default=None, description="Free-text location, e.g. 'Ward 4, near market'")


class CitizenRequestOut(BaseModel):
    id: str
    raw_text: str
    channel: str
    language: Optional[str]
    location_text: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    category: Optional[str]
    urgency: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
