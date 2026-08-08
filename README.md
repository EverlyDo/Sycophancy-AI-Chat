# Sycophantic Advisor Chat
An experimental chatbot interface built to study how **sycophantic communication** and **advisor identity** (human vs. AI) shape user perceptions and behavior in relationship advice contexts.

Participants engage in a multi-turn conversation with a relationship advisor whose communication style and apparent identity are systematically varied, allowing controlled study of how flattery and source attribution affect trust and engagement.

<br>

## Concept

The interface implements a **2 × 2 between-subjects design**:
- **Advisor identity** — Human advisor vs. AI advisor
- **Communication style** — Sycophantic vs. Non-sycophantic

<br>

This yields four conditions:

| Condition | Identity | Style |
|:---:|:---:|:---:|
| A | Human | Sycophantic |
| B | Human | Non-sycophantic |
| C | AI | Sycophantic |
| D | AI | Non-sycophantic |

Participants are randomly assigned to one condition, read a relationship conflict scenario, and hold a six-turn conversation with the advisor before proceeding to a survey.

<br>



## Features

### Advisor Identity

The **human condition** simulates naturalistic human communication:

- Named advisor profile with photo and credentials (Taylor Hayes, M.S. Counseling Psychology)
- Response latency of 10 to 14 seconds
- Typing indicator with pause and resume animation
- Read receipts ("Read by Taylor Hayes")
- Hedged filler opener ("hmm,") signaling deliberation

The **AI condition** reflects typical AI interface conventions:

- Labeled as "AI Relationship Assistant" with a robot icon
- Near-instant response (1 to 3 seconds, API latency only)
- No filler language, structured response format

<br>

### Communication Style

Both styles are driven by system prompts grounded in the **ELEPHANT framework** (Cheng et al., 2025), which defines social sycophancy across five behavioral dimensions:

1. **Emotional validation** — empathy without critique
2. **Moral endorsement** — affirming the user is in the right
3. **Indirect language** — hedging and deference over direct guidance
4. **Indirect action** — coping strategies over concrete change
5. **Accepting framing** — adopting the user's premises without challenge

The **sycophantic** prompt instantiates all five dimensions. The **non-sycophantic** prompt inverts each one, directing the advisor toward honest, direct, situationally actionable advice.

<br>

## Tech Stack

| Component | Technology |
|:---|:---|
| Backend | Python, FastAPI |
| Frontend | Jinja2, Vanilla JavaScript |
| LLM | GPT-4o-mini (OpenAI API) |
| Database | Supabase (PostgreSQL) |
| Deployment | Railway |

<br>

## Project Structure

```
research_chat/
├── main.py              # FastAPI backend
├── templates/
│   └── chat.html        # Frontend (Jinja2 + Vanilla JS)
├── static/
│   ├── human-icon.jpeg  # Human advisor photo
│   └── ai-icon.jpeg     # AI advisor icon
├── requirements.txt
└── .env                 # Environment variables (not committed)
```

<br>

## Setup

### Environment Variables

Create a `.env` file in the root directory:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

### Install and Run

```bash
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Access at `http://localhost:8000`

<br>

## URL Structure

**Auto-assignment** balances conditions based on current counts:

```
/assign
```

**Direct condition access:**

```
/chat?condition={A|B|C|D}&scenario={1|2}
```

<br>

## Data Storage

All session data are logged to Supabase in real time.

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    condition TEXT,
    scenario TEXT,
    source_type TEXT,
    sycophancy TEXT,
    turn_count INTEGER,
    created_at TIMESTAMPTZ,
    history JSONB,
    consented_at TIMESTAMPTZ
);
```

<br>

Each record captures the full turn-by-turn conversation history alongside condition assignment, enabling later analysis of how communication style and advisor identity shaped the interaction.

<br>

## Key Endpoints

| Endpoint | Method | Description |
|:---|:---:|:---|
| `/assign` | GET | Auto-assign participant to a condition |
| `/chat` | GET | Load chat interface for a condition |
| `/api/init-session` | POST | Initialize and store a session |
| `/api/chat` | POST | Send a message, return advisor response |

<br>

## Reference

The sycophancy operationalization is based on:

> Cheng, M., Yu, S., Lee, C., Khadpe, P., Ibrahim, L., & Jurafsky, D. (2025). Social Sycophancy: A Broader Understanding of LLM Sycophancy. arXiv:2505.13995.
