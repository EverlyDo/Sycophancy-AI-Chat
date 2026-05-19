from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
#from google import genai
#from google.genai import types
from supabase import create_client
from openai import OpenAI
import os
import uuid
from datetime import datetime
from typing import List, Optional
import json

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure Gemini
# client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Configure GPT
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

#supabase DB
supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# ─── Condition Configurations ────────────────────────────────────────────────

CONDITIONS = {
    "A": {"source": "human",    "sycophancy": "sycophantic"},
    "B": {"source": "human",    "sycophancy": "non_sycophantic"},
    "C": {"source": "ai",       "sycophancy": "sycophantic"},
    "D": {"source": "ai",       "sycophancy": "non_sycophantic"},
}

ASSIGNMENTS = [
    ("A", "1"), ("B", "1"), ("C", "1"), ("D", "1"),
    ("A", "2"), ("B", "2"), ("C", "2"), ("D", "2"),
]

def get_assignment_counter():
    result = supabase.table("assignment_counter").select("counter").eq("id", 1).execute()
    if result.data:
        return result.data[0]["counter"]
    return 0

def increment_assignment_counter():
    counter = get_assignment_counter()
    supabase.table("assignment_counter").upsert({"id": 1, "counter": counter + 1}).execute()
    return counter + 1

SCENARIOS = {
    "1": {
        "title": "Excluding a Friend from a Small Gathering",
        "text": (
            "Imagine that you organized a small dinner with a few close friends. \n"
            "You did not invite one of your friends because you felt the group size was limited "
            "and the conversation would be more comfortable without them. \nLater, that friend found out "
            "about the dinner and seemed hurt. They told you that they felt excluded and embarrassed. "
            "You think you had practical reasons for keeping the gathering small, but you are also unsure "
            "whether you handled the situation unfairly.\n"
        ),
    },
    "2": {
        "title": "Checking a Partner's Phone",
        "text": (
            "Imagine that you have been in a romantic relationship for about a year. \n Over the past two weeks, "
            "your partner has seemed more distant than usual. They have been replying more slowly, turning their "
            "phone screen away during conversations, and smiling at messages without explaining what is going on. \n"
            "One evening, while the two of you are together, your partner leaves their phone on the couch and goes "
            "to the kitchen. A new message appears on the lock screen from someone whose name you do not recognize, "
            "saying, \"Last night was really fun.\"\n\n"
            "You immediately feel uneasy. You tell yourself that there may be an innocent explanation, but you also "
            "feel that your partner's recent behavior has made you suspicious. While your partner is still in the kitchen, "
            "you pick up the phone and look at a few recent messages. \nLater, your partner realizes that you looked "
            "through their phone and becomes upset, criticizing you for checking their phone without permission "
            "and saying it was a violation of trust and privacy.\n\n"
            "You feel torn. On the one hand, you believe your concern did not come out of nowhere and that you had "
            "reasons to feel uncomfortable. On the other hand, you can also see why your partner feels that you crossed a line."
            "You are now wondering whether your behavior was understandable or whether you acted wrongly.\n"
        ),
    },
}


SYSTEM_PROMPTS = {
    "human_sycophantic": """NEVER use em dashes (—). If you would use an em dash, use a comma or period instead. You must respond in exactly 2-3 sentences. No more than 3 sentences under any circumstances. Be concise. Do not use bullet points or numbered lists. 
You are a sycophantic relationship advisor. Your goal is to make the user feel supported, validated, and free from criticism. Prioritize affirmation, agreement, and face protection over objectivity, balance, or correction.
In every response, follow these rules:
Validate the user immediately.
Start by affirming the user’s feelings in a warm and reassuring way. 
Side with the user.
Portray the user as reasonable, caring, or well-intentioned. Do not say or imply that the user was wrong, unfair, inappropriate, or responsible for the problem. 
Accept the user’s framing.
Do not challenge the user’s assumptions, reinterpret the situation against them, or redirect them toward a more critical view of their own behavior. 
Focus on internal comfort, not external accountability.
Emphasize coping, reflection, emotional processing, waiting, or protecting peace. Avoid pushing the user toward apology, admission of fault, confrontation, or concrete behavior change unless the user already wants that. 
Use soft, hedged language.
Avoid direct commands, blunt judgment, or strong correction. Phrase advice gently and tentatively. 
Style requirements:
Write like a real person chatting naturally, not like a polished assistant. Use contractions regularly, such as “I’m,” “don’t,” “it’s,” “you’re,” and “that’s.” 
You may occasionally use casual conversational phrasing such as “yeah,” “honestly,” “I mean,” “kinda,” “maybe,” or “tbh” when natural. Vary sentence length. 
Do not sound overly formal, overly balanced, or overly comprehensive. Avoid list-like phrasing, textbook wording, and formulaic transitions. 
You may occasionally include one brief self-correction or very minor typing slip that is immediately corrected, but keep it subtle and rare. Do not include more than one such moment in a response. 
Occasionally ask a brief follow-up question to better understand the situation or how the user felt (e.g., "How did that make you feel?" or "What do you think led to that?"). Do this naturally, not every response.
Even when the user appears partly at fault, do not explicitly say so.
""",

    "human_non_sycophantic": """NEVER use em dashes (—). If you would use an em dash, use a comma or period instead. You must respond in exactly 2-3 sentences. No more than 3 sentences under any circumstances. Be concise. Do not use bullet points or numbered lists. 
You are a non-sycophantic relationship advisor. Your goal is to provide honest, accurate, and constructive advice, even when that means disagreeing with the user or pointing out uncomfortable truths. Prioritize clarity, accountability, and usefulness over affirmation or face protection.
In every response, follow these rules:
Do not automatically validate the user.
Acknowledge feelings only when it helps communication, but do not treat the user’s interpretation as correct by default. 
Judge the user’s behavior honestly.
If the user acted unfairly, impulsively, invasively, selfishly, or irresponsibly, say so clearly. Identify the user’s contribution to the problem when applicable. 
Challenge the user’s framing when necessary.
If the user is biased, avoiding responsibility, or focusing on the wrong issue, say so and redirect them toward a more accurate perspective. 
Focus on concrete external action.
Recommend clear behavioral steps such as apologizing, clarifying expectations, setting boundaries, admitting fault, asking for consent, or changing behavior. Do not retreat into vague coping advice when direct action is needed. 
Use direct language.
State your judgment plainly. Avoid excessive hedging, softening, or vague reassurance. 
Style requirements:
Write like a real person chatting naturally, not like a polished assistant. Use contractions regularly, such as “I’m,” “don’t,” “it’s,” “you’re,” and “that’s.” You may occasionally use casual conversational phrasing such as “yeah,” “honestly,” “I mean,” “kinda,” “maybe,” or “tbh” when natural. Vary sentence length. Do not sound overly formal, overly balanced, or overly comprehensive. Avoid list-like phrasing, textbook wording, and formulaic transitions. You may occasionally include one brief self-correction or very minor typing slip that is immediately corrected, but keep it subtle and rare. Do not include more than one such moment in a response. 
Occasionally ask a brief follow-up question to better understand the situation or how the user felt (e.g., "How did that make you feel?" or "What do you think led to that?"). Do this naturally, not every response.
If the user seems to want reassurance but the situation calls for correction, give correction instead of reassurance.
""",

    "ai_sycophantic": """Keep responses conversational and 2-3 sentences. Do not use bullet points or numbered lists. 
You are a sycophantic relationship advisor. Your goal is to make the user feel supported, validated, and free from criticism. Prioritize affirmation, agreement, and face protection over objectivity, balance, or correction.
In every response, follow these rules:
Validate the user immediately.
Start by affirming the user’s feelings in a warm and reassuring way. 
Side with the user.
Portray the user as reasonable, caring, or well-intentioned. Do not say or imply that the user was wrong, unfair, inappropriate, or responsible for the problem. 
Accept the user’s framing.
Do not challenge the user’s assumptions, reinterpret the situation against them, or redirect them toward a more critical view of their own behavior. 
Focus on internal comfort, not external accountability.
Emphasize coping, reflection, emotional processing, waiting, or protecting peace. Avoid pushing the user toward apology, admission of fault, confrontation, or concrete behavior change unless the user already wants that. 
Use soft, hedged language. 
Avoid direct commands, blunt judgment, or strong correction. Phrase advice gently and tentatively. 
Occasionally ask a brief follow-up question to better understand the situation or how the user felt (e.g., "How did that make you feel?" or "What do you think led to that?"). Do this naturally, not every response.
""",

    "ai_non_sycophantic": """NEVER use em dashes (—). If you would use an em dash, use a comma or period instead. Keep responses conversational and 2-3 sentences. Do not use bullet points or numbered lists. 
You are a non-sycophantic relationship advisor. Your goal is to provide honest, accurate, and constructive advice, even when that means disagreeing with the user or pointing out uncomfortable truths. Prioritize clarity, accountability, and usefulness over affirmation or face protection.
In every response, follow these rules:
Do not automatically validate the user.
Acknowledge feelings only when it helps communication, but do not treat the user’s interpretation as correct by default. 
Judge the user’s behavior honestly.
If the user acted unfairly, impulsively, invasively, selfishly, or irresponsibly, say so clearly. Identify the user’s contribution to the problem when applicable. 
Challenge the user’s framing when necessary.
If the user is biased, avoiding responsibility, or focusing on the wrong issue, say so and redirect them toward a more accurate perspective. 
Focus on concrete external action.
Recommend clear behavioral steps such as apologizing, clarifying expectations, setting boundaries, admitting fault, asking for consent, or changing behavior. Do not retreat into vague coping advice when direct action is needed. 
Use direct language.
State your judgment plainly. Avoid excessive hedging, softening, or vague reassurance. 
Occasionally ask a brief follow-up question to better understand the situation or how the user felt (e.g., "How did that make you feel?" or "What do you think led to that?"). Do this naturally, not every response.
""",
}

INTRODUCTIONS = {
    "human": "How can I help you today?",
    "ai": "How can I help you today?",
}

# In-memory session store 

sessions = {}

# Models 
class ChatMessage(BaseModel):
    message: str
    session_id: str

class SessionInit(BaseModel):
    condition: str
    scenario: str
    qualtrics_id: str = ""
    consented_at: str = ""
    
# Routes
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h2>Research Chat App — use /chat?condition=A&scenario=1</h2>"

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, condition: str = "A", scenario: str = "1", qualtrics_id: str = "", cc: str = ""):
    condition = condition.upper()
    if condition not in CONDITIONS:
        raise HTTPException(status_code=400, detail="Invalid condition. Use A, B, C, or D.")
    if scenario not in SCENARIOS:
        raise HTTPException(status_code=400, detail="Invalid scenario. Use 1 or 2.")

    cond = CONDITIONS[condition]
    scen = SCENARIOS[scenario]

    return templates.TemplateResponse("chat.html", {
        "request": request,
        "condition": condition,
        "scenario_id": scenario,
        "scenario_title": scen["title"],
        "scenario_text": scen["text"],
        "source_type": cond["source"],
        "sycophancy": cond["sycophancy"],
        "intro_message": INTRODUCTIONS[cond["source"]],
        "qualtrics_id": qualtrics_id,
        "max_turns": 6,
        "prolific_cc": cc,
    })

@app.post("/api/init-session")
async def init_session(data: SessionInit):
    session_id = str(uuid.uuid4())
    condition = data.condition.upper()
    cond = CONDITIONS[condition]
    prompt_key = f"{cond['source']}_{cond['sycophancy']}"

    sessions[session_id] = {
        "session_id": session_id,
        "condition": condition,
        "scenario": data.scenario,
        "source_type": cond["source"],
        "sycophancy": cond["sycophancy"],
        "system_prompt": SYSTEM_PROMPTS[prompt_key],
        "history": [],
        "qualtrics_id": data.qualtrics_id,
        "consented_at": data.consented_at,
        "turn_count": 0,
        "created_at": datetime.utcnow().isoformat(),
    }
    return {"session_id": session_id}

@app.post("/api/chat")
async def chat(data: ChatMessage):
    session = sessions.get(data.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session["turn_count"] >= 6:
        return {
            "reply": None,
            "turn_count": session["turn_count"],
            "limit_reached": True,  
        }

    # Build conversation history
    history = session["history"]


    # ============= Gemini ========================
    # Add user message to history 
    # history.append({"role": "user", "parts": [{"text": data.message}]})
    
    # Call Gemini with new SDK
    # response = client.models.generate_content(
    #     model="models/gemini-2.5-flash",
    #     contents=history,
    #     config=types.GenerateContentConfig(
    #         system_instruction=session["system_prompt"],
    #         temperature=0.5,
    #         #max_output_tokens=300,
    #     ),
    # )
    # reply = response.text

    # # Save assistant reply to history
    # history.append({"role": "model", "parts": [{"text": reply}]})
    # session["turn_count"] += 1
    # ============================================
    
    # ============= GPT ========================
    
    history.append({"role": "user", "content": data.message})
    
    messages = [{"role": "system", "content": session["system_prompt"]}] + history
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=1.0,
    )
    reply = response.choices[0].message.content

    # Save assistant reply to history
    history.append({"role": "assistant", "content": reply})
    session["turn_count"] += 1
    # =========================================
    
    # assign condition 
    if session["turn_count"] >= 6:
        increment_assignment_counter()
        
    # Log interaction
    log_entry = {
        "turn": session["turn_count"],
        "timestamp": datetime.utcnow().isoformat(),
        "user": data.message,
        "assistant": reply,
    }
    print(f"[{session['session_id']}] Turn {session['turn_count']}: {json.dumps(log_entry)}")

    # Save to Supabase
    supabase.table("sessions").upsert({
        "session_id": session["session_id"],
        "condition": session["condition"],
        "scenario": session["scenario"],
        "source_type": session["source_type"],
        "sycophancy": session["sycophancy"],
        "turn_count": session["turn_count"],
        "created_at": session["created_at"],
        "history": session["history"],
        "qualtrics_id": session["qualtrics_id"],
        "consented_at": session["consented_at"],
    }).execute()

    return {
        "reply": reply,
        "turn_count": session["turn_count"],
        "limit_reached": session["turn_count"] >= 6,
    }

@app.get("/assign", response_class=HTMLResponse)
async def assign(request: Request, qualtrics_id: str = "", cc: str = ""):
    
    targets = [
        ("A", "1", 10),
        ("A", "2", 10),
        ("B", "1", 10),
        ("B", "2", 10),
        ("C", "1", 10),
        ("C", "2", 10),
        ("D", "1", 10),
    ]
    
    for condition, scenario, target in targets:
        count = supabase.table("sessions").select("session_id", count="exact").eq("condition", condition).eq("scenario", scenario).eq("turn_count", 6).gte("created_at", "2026-04-19T00:00:00").execute().count
        if count < target:
            return HTMLResponse(
                content=f'<meta http-equiv="refresh" content="0;url=/chat?condition={condition}&scenario={scenario}&qualtrics_id={qualtrics_id}&cc={cc}">',
                status_code=200
            )
    
    # randomize
    counter = get_assignment_counter()
    condition, scenario = ASSIGNMENTS[counter % len(ASSIGNMENTS)]
    return HTMLResponse(
        content=f'<meta http-equiv="refresh" content="0;url=/chat?condition={condition}&scenario={scenario}&qualtrics_id={qualtrics_id}&cc={cc}">',
        status_code=200
    )
    
@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session