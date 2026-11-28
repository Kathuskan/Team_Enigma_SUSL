"""Accept only explicit, validated crop details from the current message."""
from datetime import date, datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field
from project.agents.weather import COLOMBO

class Update(BaseModel):
    water: Literal["irrigated","rainfed"] | None = None
    season_name: Literal["maha","yala"] | None = None
    variety_name: str | None = Field(default=None,max_length=80)
    duration_months: Literal[2.5,3,3.5,4,4.5] | None = None
    planted: date | None = None
    last_fertilizer: date | None = None
    crop_day: int | None = Field(default=None,ge=1,le=365)

def apply_update(update, profile):
    today = datetime.now(COLOMBO).date()
    fields=update.model_dump(exclude_none=True, mode="json")
    age=fields.pop("crop_day",None)
    if age:
        fields.setdefault("planted",str(today-timedelta(days=age-1)))
    for key in ("planted","last_fertilizer"):
        if fields.get(key,"")>str(today):
            fields.pop(key)
    return {**profile,**fields}
