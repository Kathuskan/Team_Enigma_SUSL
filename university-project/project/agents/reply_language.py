"""Recognize explicit reply-language requests, including common romanized forms."""
import re

NAMES = {"tamil":"ta-LK","thamizh":"ta-LK","tamizh":"ta-LK","தமிழ்":"ta-LK",
         "english":"en-LK","sinhala":"si-LK","සිංහල":"si-LK"}
NAME = "(?P<name>"+"|".join(NAMES)+")"
COMMANDS = [
    re.compile(NAME+r"(?:\s*(?:la|le|il|in|ல|இல்))?\s+(?:reply|answer|respond|pesu|sollu|பதில்)(?:\s+(?:pannu|pannunga|please|sollunga))?\b", re.I),
    re.compile(r"(?:reply|answer|respond|speak|continue)\s+(?:to me\s+)?in\s+"+NAME+r"\b",re.I),
]
CAPABILITY=re.compile(r"(?:do you (?:speak|know|understand)\s+(?:tamil|thamizh|tamizh)|(?:tamil|tamizh|thamizh)\s+the?ri(?:yu|u)ma+)[?!.\s]*$",re.I)

def preference(text):
    for rule in COMMANDS:
        match=rule.search(text)
        if match:
            remainder=text[:match.start()]+" "+text[match.end():]
            only=not re.sub(r"\b(?:apa|appa|appo|please|ok|okay|then|yes|pls)\b|[\s,.!?]","",remainder,flags=re.I)
            return NAMES[match["name"].lower()],only
    return None,False

ACK={"ta-LK":"சரி, இனி தமிழில் பதில் சொல்கிறேன்.","en-LK":"Sure, I’ll reply in English.","si-LK":"හරි, මම සිංහලෙන් පිළිතුරු දෙන්නම්."}
