"""Focused questions for incomplete harvest, crop-health and spraying requests."""
from datetime import date, timedelta
import re

PATTERNS = {
    "spray": r"\bspray\w*|fungicide|pesticide|தெளி|ඉසි|ඉසී",
    "fertilizer": r"fertili|urea|உரம்|පොහොර",
    "harvest": r"\bharvest\w*|\breap\w*|\bcut\b(?!\s+(?:leaf|leaves|weeds?))|அறுவடை|අස්වනු|කපන්න",
    "disease": r"diseas|sick|infect|நோய்|රෝග",
}
SIGNS = r"spots?|lesions?|yellow|wilt|rot|brown|white|black|fold|holes?|drying|புள்ளி|மஞ்சள்|அழுகல்|පැල්ලම්|කහ|දුඹුරු"
PARTS = r"lea(?:f|ves)|stem|sheath|panicle|root|grain|இலை|தண்டு|கதிர்|පත්‍ර|කඳ|කරල"
LANG = {"en-LK":0,"ta-LK":1,"si-LK":2}
PROMPTS = {
 "age": ("When did you plant this crop, or how many days old is it?","இந்தப் பயிரை எப்போது நட்டீர்கள் அல்லது அதன் வயது எத்தனை நாட்கள்?","වගාව ආරම්භ කළේ කවදාද, නැත්නම් දැන් වගාවට දින කීයක්ද?"),
 "variety": ("How long does your variety usually take to mature (for example, 3 or 3.5 months)?","உங்கள் நெல் வகை முதிர எத்தனை மாதங்கள் ஆகும் (3 அல்லது 3.5 மாதங்கள் போன்றவை)?","ඔබේ ප්‍රභේදය පරිණත වීමට මාස කීයක් ගත වෙනවාද (මාස 3 හෝ 3.5 වැනි)?"),
 "signs": ("What changes can you see, such as spots, yellowing or wilting?","புள்ளிகள், மஞ்சள் நிறம் அல்லது வாடுதல் போன்ற என்ன மாற்றங்களைக் காண்கிறீர்கள்?","පැල්ලම්, කහ වීම හෝ මැලවීම වැනි කුමන වෙනස්කම් දකින්න ලැබෙනවාද?"),
 "part": ("Which part is affected: the leaves, stems or grain heads?","இலை, தண்டு, கதிர் ஆகியவற்றில் எது பாதிக்கப்பட்டுள்ளது?","පත්‍ර, කඳ හෝ කරල අතරින් බලපෑමට ලක් වූ කොටස කුමක්ද?"),
 "photo": ("Can you attach a clear close-up of the affected part so I can examine it?","பாதிக்கப்பட்ட பகுதியின் தெளிவான படத்தை இணைக்க முடியுமா?","බලපෑමට ලක් වූ කොටසේ පැහැදිලි සමීප ඡායාරූපයක් එක් කළ හැකිද?"),
 "target": ("What pest or symptom are you planning to spray for?","எந்தப் பூச்சி அல்லது அறிகுறிக்காகத் தெளிக்க விரும்புகிறீர்கள்?","ඉසින්න අදහස් කරන්නේ කුමන පළිබෝධයක් හෝ ලක්ෂණයක් සඳහාද?"),
 "topic": ("What would you like to decide about your crop: harvesting, a disease, fertilizer or spraying?","அறுவடை, நோய், உரம் அல்லது தெளிப்பு பற்றி எதைக் கேட்க விரும்புகிறீர்கள்?","අස්වනු නෙළීම, රෝග, පොහොර හෝ ඉසීම ගැන ඔබට දැනගැනීමට අවශ්‍ය කුමක්ද?"),
}
def intent(text):
    return next((k for k,pattern in PATTERNS.items() if re.search(pattern,text,re.I)),"field")

def prepare(c):
    text=c["text"]
    last=c["history"][-1] if c.get("history") else {}
    pending=last.get("pending","")
    topic=intent(text)
    if topic=="field" or topic==intent(pending):
        query=" ".join(filter(None,(pending,text)))
    else:
        query=text
    topic=intent(query)
    language=LANG[c["language"]]
    missing=[]
    if topic=="harvest":
        if not c["profile"].get("planted"):
            missing.append("age")
        if not c["profile"].get("duration_months"):
            missing.append("variety")
    elif topic=="disease" and not c.get("photo"):
        if not re.search(SIGNS,query,re.I):
            missing.append("signs")
        if not re.search(PARTS,query,re.I):
            missing.append("part")
    tomorrow=c["tomorrow"]
    if re.search(r"\btoday\b|\bright now\b|இன்று|இன்றைக்கு|අද",text,re.I):
        tomorrow=False
    elif re.search(r"\btomorrow\b|நாளை|හෙට",text,re.I):
        tomorrow=True
    return query,topic," ".join(PROMPTS[k][language] for k in missing),tomorrow

def maturity(profile,lang):
    # Variety duration is only a planning estimate. Local conditions affect the actual harvest.
    estimated=date.fromisoformat(profile["planted"])+timedelta(days=round(float(profile["duration_months"])*30))
    templates=("Using your planting date and variety, the approximate maturity date is {}. Check grain maturity across the field before cutting; this estimate alone cannot confirm readiness.",
               "நடவு தேதி மற்றும் வகையின் படி முதிர்வு தேதி சுமார் {}. அறுவடைக்கு முன் வயலின் பல இடங்களில் தானிய முதிர்ச்சியைச் சரிபாருங்கள்.",
               "වගාව ආරම්භ කළ දිනය හා ප්‍රභේදය අනුව ආසන්න පරිණත දිනය {} වේ. කැපීමට පෙර කුඹුරේ ස්ථාන කිහිපයක ධාන්‍ය පරිණත බව බලන්න.")
    return templates[LANG[lang]].format(estimated.isoformat())
