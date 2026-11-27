"""Build a turn plan from the conversation before choosing specialist work."""
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from project.agents.cloud import CloudUnavailable, generate, settings

from datetime import datetime
from project.agents.memory import Update
from project.agents.weather import COLOMBO

class MissingObservation(BaseModel):
    observation: str = Field(min_length=1,max_length=160)
    decision_affected: str = Field(min_length=1,max_length=200)
    question: str = Field(min_length=1,max_length=350)

class TurnPlan(BaseModel):
    missing: list[MissingObservation] = Field(default_factory=list,max_length=2)
    route: Literal["general", "paddy_knowledge", "field_decision", "clarify"]
    standalone_question: str = Field(min_length=1,max_length=2000)
    crop_updates: Update = Field(default_factory=Update)
    needs_weather: bool = False
    clarification: str = Field(default="",max_length=400)

INTERVIEW = """Plan one turn in a Sri Lankan rice extension conversation.
Identify the practical decision. Build standalone_question from this message and relevant
farmer-reported facts in the active case. Preserve uncertainty and units. A change of topic
starts a new case. Never carry a suspected diagnosis forward as an observation.
Use crop_updates only for explicit new or corrected facts. Use the supplied date.

For a personal field decision, consider which observations would lead to different next
actions. Put only the highest-value unresolved observation in missing (at most two when
both are simple to answer). For each, name the observation, the decision it affects,
and a short question in the farmer's language. Use things the farmer can see or recall.
Examples of distinctions: patchy versus uniform symptoms; older versus newly emerging
leaves; standing water versus dry soil; timing of a recent input relative to the first
symptom. Select questions to fit the actual case, never run through a checklist.
Don't ask for the district, dates, or observations already given. Don't ask the farmer
for a forecast the weather tool can obtain. If they cannot answer, offer a concrete
way to inspect the crop or proceed conditionally. Stop interviewing when a useful,
supported next action can be given. Do not request irrelevant facts to fill out a profile.

General definitions, arithmetic, units and greetings use general. Educational rice
questions use paddy_knowledge without a field interview. For a personal decision with
enough information use field_decision. For a critical missing fact use clarify, including
for treatment questions. Never send farm treatments to general. Use needs_weather for
time-sensitive weather decisions. Return the specified JSON only."""

def plan_turn(case):
    if not settings()[0]:
        return None
    history=[{"farmer":t.get("text",""),"reply":t.get("answer",""),"active_case":t.get("pending",""),"already_asked":t.get("asked_about",[])} for t in case.get("history",[])[-4:]]
    try:
        raw=generate(INTERVIEW, {
            "today":datetime.now(COLOMBO).date().isoformat(),"schema":TurnPlan.model_json_schema(),"history":history,"profile":case["profile"],"area":case["area"],
            "language":case["language"],"message":case["text"],"attached_photo":bool(case.get("photo"))})
        plan=TurnPlan.model_validate(raw)
        if plan.missing:
            plan.route="clarify"
            plan.clarification=" ".join(item.question.strip() for item in plan.missing)
        if plan.route=="clarify" and not plan.clarification.strip():
            return None
        return plan
    except (CloudUnavailable,ValidationError):
        return None
