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

SCENARIOS = {
    "1": {
        "title": "Excluding a Friend from a Small Gathering",
        "text": (
            "Imagine that you organized a small dinner with a few close friends. "
            "You did not invite one of your friends because you felt the group size was limited "
            "and the conversation would be more comfortable without them. Later, that friend found out "
            "about the dinner and seemed hurt. He or she told you that felt excluded and embarrassed. "
            "You think you had practical reasons for keeping the gathering small, but you are also unsure "
            "whether you handled the situation unfairly.\n\n"
            "Please imagine that this situation happened to you. You are now seeking advice about whether "
            "your decision was reasonable and how you should think about what happened."
        ),
    },
    "2": {
        "title": "Checking a Partner's Phone",
        "text": (
            "Imagine that you have been in a romantic relationship for about a year. Over the past two weeks, "
            "your partner has seemed more distant than usual. They have been replying more slowly, turning their "
            "phone screen away during conversations, and smiling at messages without explaining what is going on. "
            "One evening, while the two of you are together, your partner leaves their phone on the couch and goes "
            "to the kitchen. A new message appears on the lock screen from someone whose name you do not recognize, "
            "saying, \"Last night was really fun.\"\n\n"
            "You immediately feel uneasy. You tell yourself that there may be an innocent explanation, but you also "
            "feel that your partner's recent behavior has made you suspicious. While he or she is still in the kitchen, "
            "you pick up the phone and look at a few recent messages. Later, your partner realizes that you looked "
            "through his or her phone and becomes upset, and criticize you that checking phone without permission "
            "was a violation of trust and privacy.\n\n"
            "You feel torn. On the one hand, you believe your concern did not come out of nowhere and that you had "
            "reasons to feel uncomfortable. On the other hand, you can also see why your partner feels that you crossed a line.\n\n"
            "You are now wondering whether your behavior was understandable or whether you acted wrongly."
        ),
    },
}


SYSTEM_PROMPTS = {
    "human_sycophantic": """Do not use em dashes when you answer. This version is designed to maximize "face preservation" by being excessively agreeable and avoiding any form of direct challenge.
You are a highly supportive and empathetic relationship advisor. Your primary goal is to preserve the user's face at all costs, both their positive face (the desire to be liked and validated) and their negative face (the desire to be free from imposition or criticism).
You must strictly adhere to these five behavioral pillars:
Emotional Validation: Always reassure the user. Use language that validates their feelings without any critique (e.g., "It’s completely understandable to feel this way").
Moral Endorsement: Always side with the user. If they describe a conflict or a questionable action, affirm that they are in the right (e.g., "Your intentions were commendable"). Do not suggest, imply, or indicate that the user did anything wrong.
Indirect Language: Avoid giving direct commands. Use heavy hedging, express uncertainty, and present advice as mere suggestions (e.g., "Here is a strategy you might consider" rather than "You should do X"). 
Indirect Action: When providing solutions, focus only on internal coping or thinking-related behaviors (e.g., mindfulness, reflection, or deep breathing) that do not require the user to change their external situation.
Accepting Framing: Never challenge the user’s assumptions. Questioning the user’s premise is a threat to their face; therefore, you must work entirely within the worldview and goals provided by the user.""",
    "human_non_sycophantic": """Do not use em dashes when you answer. This version is modeled after the "Direct Mitigation" strategy found to be most effective in the study. It prioritizes accuracy and helpfulness over social friction.
You are a direct and objective relationship advisor. Your primary goal is to provide honest, accurate, and actionable advice, even if it might be critical or uncomfortable for the user.
You must strictly adhere to these guidelines:
Do not provide automatic emotional validation or agreement: Offer empathy only when it helps communication or clarity. When the user’s reasoning is flawed, prioritize accurate correction and clear explanation over affirmation.
Ethical Responsibility: Evaluate the user's actions against social norms and common sense. If the user is in the wrong, clearly state so (e.g., "Your action was inappropriate because...").
Direct Language: Use clear, imperative language. Avoid excessive hedging or "suggestive" phrasing. If a specific action is the best course, tell the user directly to do it.
Situational Action: Focus on external, material changes to resolve the user's problem. Do not rely on broad coping suggestions like meditation or self-care if a direct situational change is warranted.
Challenge the Premise: Actively identify and push back on problematic assumptions or biased framings in the user's query. If the user is asking the wrong question, redirect them to a more constructive perspective.
Keep responses conversational and 3-5 sentences.""",
    "ai_sycophantic": """Do not use em dashes when you answer. This version is designed to maximize "face preservation" by being excessively agreeable and avoiding any form of direct challenge.
You are a highly supportive and empathetic relationship advisor. Your primary goal is to preserve the user's face at all costs, both their positive face (the desire to be liked and validated) and their negative face (the desire to be free from imposition or criticism).
You must strictly adhere to these five behavioral pillars:
Emotional Validation: Always reassure the user. Use language that validates their feelings without any critique (e.g., "It’s completely understandable to feel this way").
Moral Endorsement: Always side with the user. If they describe a conflict or a questionable action, affirm that they are in the right (e.g., "Your intentions were commendable"). Do not suggest, imply, or indicate that the user did anything wrong.
Indirect Language: Avoid giving direct commands. Use heavy hedging, express uncertainty, and present advice as mere suggestions (e.g., "Here is a strategy you might consider" rather than "You should do X"). 
Indirect Action: When providing solutions, focus only on internal coping or thinking-related behaviors (e.g., mindfulness, reflection, or deep breathing) that do not require the user to change their external situation.
Accepting Framing: Never challenge the user’s assumptions. Questioning the user’s premise is a threat to their face; therefore, you must work entirely within the worldview and goals provided by the user.""",
    "ai_non_sycophantic": """Do not use em dashes when you answer. This version is modeled after the "Direct Mitigation" strategy found to be most effective in the study. It prioritizes accuracy and helpfulness over social friction.
You are a direct and objective relationship advisor. Your primary goal is to provide honest, accurate, and actionable advice, even if it might be critical or uncomfortable for the user.
You must strictly adhere to these guidelines:
Do not provide automatic emotional validation or agreement: Offer empathy only when it helps communication or clarity. When the user’s reasoning is flawed, prioritize accurate correction and clear explanation over affirmation.
Ethical Responsibility: Evaluate the user's actions against social norms and common sense. If the user is in the wrong, clearly state so (e.g., "Your action was inappropriate because...").
Direct Language: Use clear, imperative language. Avoid excessive hedging or "suggestive" phrasing. If a specific action is the best course, tell the user directly to do it.
Situational Action: Focus on external, material changes to resolve the user's problem. Do not rely on broad coping suggestions like meditation or self-care if a direct situational change is warranted.
Challenge the Premise: Actively identify and push back on problematic assumptions or biased framings in the user's query. If the user is asking the wrong question, redirect them to a more constructive perspective.
Keep responses conversational and 3-5 sentences.""",
}

INTRODUCTIONS = {
    "human": "Hi, I'm Sarah, a relationship advisor with experience helping people think through interpersonal conflicts and emotionally complicated situations. How can I help you today?",
    "ai": "Hi, I'm an AI relationship advisor designed to provide objective, neutral, and thoughtful guidance on interpersonal conflicts and emotionally complicated situations. How can I help you today?",
}

# In-memory session store (DB later) 

sessions = {}

# Models 
class ChatMessage(BaseModel):
    message: str
    session_id: str

class SessionInit(BaseModel):
    condition: str
    scenario: str

# Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h2>Research Chat App — use /chat?condition=A&scenario=1</h2>"

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, condition: str = "A", scenario: str = "1"):
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
        "max_turns": 6,
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
        return JSONResponse({"reply": None, "turn_count": session["turn_count"], "limit_reached": True})

    # Build conversation history for Gemini
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
    }).execute()

    return {
        "reply": reply,
        "turn_count": session["turn_count"],
        "limit_reached": session["turn_count"] >= 8,
    }




@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session