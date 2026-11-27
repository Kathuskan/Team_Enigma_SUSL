"""Accept only explicit, validated crop details from the current message."""
from datetime import date, datetime, timedelta
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from project.agents.cloud import generate, settings, CloudUnavailable
from project.agents.weather import COLOMBO

class Update(BaseModel):
    water: Literal["irrigated","rainfed"] | None = None
    season_name: Literal["maha","yala"] | None = None
    duration_months: Literal[2.5,3,3.5,4,4.5] | None = None
    planted: date | None = None
    last_fertilizer: date | None = None
    crop_day: int | None = Field(default=None,ge=1,le=365)

def update(text, profile):
    if not settings()[0]:
        return
    today = datetime.now(COLOMBO).date()
    try:
        raw = generate("Extract only crop facts explicitly stated or corrected by the farmer. Read Sinhala, Tamil or English. Unknown fields must be omitted. Return a JSON object matching the supplied schema. Resolve relative dates against today. Never infer water source or season from district.",{"message":text,"today":str(today),"schema":Update.model_json_schema()})
        fields=Update.model_validate(raw).model_dump(exclude_none=True, mode="json")
        age=fields.pop("crop_day",None)
        if age:
            fields.setdefault("planted",str(today-timedelta(days=age-1)))
        for key in ("planted","last_fertilizer"):
            if fields.get(key,"")>str(today):
                fields.pop(key)
        profile.update(fields)
    except (CloudUnavailable,ValidationError):
        return

