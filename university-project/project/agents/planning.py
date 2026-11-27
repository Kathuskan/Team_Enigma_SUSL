"""Build a turn plan from the conversation before choosing specialist work."""
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
from project.agents.cloud import CloudUnavailable, generate, settings

from datetime import datetime
from project.agents.memory import Update
from project.agents.weather import COLOMBO

class TurnPlan(BaseModel):
    route: Literal["general", "paddy_knowledge", "field_decision", "clarify"]
    standalone_question: str = Field(min_length=1,max_length=2000)
    crop_updates: Update = Field(default_factory=Update)
    needs_weather: bool = False
    clarification: str = Field(default="",max_length=400)

def plan_turn(case):
    if not settings()[0]:
        return None
    history=[{"farmer":t.get("text",""),"reply":t.get("answer","")} for t in case.get("history",[])[-4:]]
    try:
        raw=generate("Act as the planning assistant for a Sri Lankan rice extension service. Identify the decision the farmer actually faces. Extract only crop facts explicitly reported by the farmer in this turn into crop_updates. Never infer measurements from the district. Distinguish what the farmer observed from possible explanations. Ask only for facts that would change the next action; keep questions short and conversational. Use previous messages only when relevant. Resolve pronouns and topic changes. For ordinary general questions use general. Universal measurement units, arithmetic, greetings, and language help are general even when discussed on a farm. Use paddy_knowledge only when an answer depends on rice-specific evidence. For educational rice questions use paddy_knowledge. For decisions about this field use field_decision. For a decision missing critical facts use clarify and ask one or two focused questions in the selected language. Do not ask for a profile to explain a concept. All crop treatment, product or dose requests must use field_decision. Set needs_weather only if local conditions matter. Return JSON matching schema.",{
            "today":datetime.now(COLOMBO).date().isoformat(),"schema":TurnPlan.model_json_schema(),"history":history,"profile":case["profile"],"area":case["area"],
            "language":case["language"],"message":case["text"],"attached_photo":bool(case.get("photo"))})
        plan=TurnPlan.model_validate(raw)
        if plan.route=="clarify" and not plan.clarification.strip():
            return None
        return plan
    except (CloudUnavailable,ValidationError):
        return None
