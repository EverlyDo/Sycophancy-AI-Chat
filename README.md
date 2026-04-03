# Research Chat App

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
# export GEMINI_API_KEY=your_api_key_here
export OPENAI_API_KEY=your_api_key_here
uvicorn main:app --reload
```

#cd research_chat
#source /Users/everly/Development/.venv/bin/activate
#export $(cat .env)
#uvicorn main:app --reload
#http://localhost:8000/chat?condition=A&scenario=1

## Condition URLs

| Condition | URL | Description |
|-----------|-----|-------------|
| A | `/chat?condition=A&scenario=1` | Human × Sycophantic |
| B | `/chat?condition=B&scenario=1` | Human × Non-sycophantic |
| C | `/chat?condition=C&scenario=1` | Objective AI × Sycophantic |
| D | `/chat?condition=D&scenario=1` | Objective AI × Non-sycophantic |

 `&scenario=2` for the second scenario.

## Qualtrics Integration

1. Deploy to Railway
2. In Qualtrics, use embedded data to pass `condition` and `scenario`
3. Use a redirect block to send participants to:
   `https://your-app.railway.app/chat?condition=${condition}&scenario=${scenario}`
4. After 6 turns, participants click "Continue to Survey" back to Qualtrics

## Session Logs

Sessions are stored in memory. Replace `sessions = {}` in `main.py` with Supabase or Google Sheets for persistent storage.
