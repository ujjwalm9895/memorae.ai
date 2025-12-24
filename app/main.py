from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime

from .database import Base, engine, SessionLocal
from .models import Reminder, ConversationMemory
from .ai import extract_intent_and_time, recall_from_memory
from .scheduler import schedule_reminder
from .whatsapp import send_whatsapp_message
from .config import ALLOWED_WHATSAPP_NUMBERS

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Memorae.ai Demo")

class MessageRequest(BaseModel):
    user_id: str
    text: str

class RecallRequest(BaseModel):
    user_id: str
    question: str


@app.post("/message")
def create_reminder(req: MessageRequest):
    db = SessionLocal()

    db.add(ConversationMemory(user_id=req.user_id, message=req.text))
    db.commit()

    data = extract_intent_and_time(req.text)
    if not data:
        return {"error": "Could not understand reminder"}

    remind_at = datetime.fromisoformat(data["datetime"])

    reminder = Reminder(
        user_id=req.user_id,
        text=data["task"],
        remind_at=remind_at
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    schedule_reminder(reminder)

    return {
        "status": "Reminder set",
        "task": reminder.text,
        "remind_at": reminder.remind_at
    }


@app.post("/recall")
def recall(req: RecallRequest):
    db = SessionLocal()
    memories = (
        db.query(ConversationMemory)
        .filter(ConversationMemory.user_id == req.user_id)
        .order_by(ConversationMemory.created_at.desc())
        .limit(5)
        .all()
    )

    history = "\n".join([m.message for m in reversed(memories)])
    answer = recall_from_memory(history, req.question)

    return {"answer": answer}


@app.post("/whatsapp")
def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...)
):
    user_number = From.replace("whatsapp:", "")
    user_text = Body

    if ALLOWED_WHATSAPP_NUMBERS and user_number not in ALLOWED_WHATSAPP_NUMBERS:
        return "Ignored"

    db = SessionLocal()
    db.add(ConversationMemory(user_id=user_number, message=user_text))
    db.commit()

    data = extract_intent_and_time(user_text)
    if not data:
        send_whatsapp_message(user_number, "Samajh nahi paya 😕")
        return "OK"

    remind_at = datetime.fromisoformat(data["datetime"])

    reminder = Reminder(
        user_id=user_number,
        text=data["task"],
        remind_at=remind_at
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    schedule_reminder(reminder)

    send_whatsapp_message(
        user_number,
        f"⏰ Reminder set!\nTask: {reminder.text}\nTime: {reminder.remind_at}"
    )

    return "OK"


@app.get("/", response_class=HTMLResponse)
def index():
    # Simple single-page UI to mimic a WhatsApp-style input.
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Memorae.ai Demo</title>
      <style>
        :root {
          font-family: "Segoe UI", Arial, sans-serif;
          background: #0b141a;
          color: #e9edef;
        }
        body {
          margin: 0;
          display: flex;
          justify-content: center;
          padding: 24px;
        }
        .app {
          width: min(960px, 100%);
          background: #111b21;
          border: 1px solid #233138;
          border-radius: 16px;
          overflow: hidden;
          box-shadow: 0 10px 40px rgba(0,0,0,0.35);
        }
        header {
          padding: 16px 20px;
          background: #202c33;
          border-bottom: 1px solid #233138;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 10px;
        }
        header span {
          color: #25d366;
        }
        .content {
          padding: 20px;
          display: grid;
          gap: 16px;
          background: radial-gradient(circle at 20% 20%, #233138 0, #111b21 35%);
        }
        .card {
          background: #0b141a;
          border: 1px solid #233138;
          border-radius: 12px;
          padding: 16px;
        }
        .label {
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          color: #8696a0;
          margin-bottom: 6px;
          display: block;
        }
        input, textarea, button {
          width: 100%;
          border-radius: 10px;
          border: 1px solid #233138;
          background: #202c33;
          color: #e9edef;
          padding: 12px;
          font-size: 14px;
        }
        textarea { resize: vertical; min-height: 60px; }
        button {
          background: linear-gradient(135deg, #25d366, #2fe07f);
          color: #0b141a;
          cursor: pointer;
          border: none;
          font-weight: 700;
          transition: transform 0.08s ease, box-shadow 0.12s ease;
        }
        button:hover { transform: translateY(-1px); box-shadow: 0 10px 24px rgba(37, 211, 102, 0.25); }
        button:active { transform: translateY(0); box-shadow: none; }
        .row { display: grid; gap: 12px; }
        .grid-2 { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
        .bubble {
          background: #005c4b;
          padding: 12px 14px;
          border-radius: 12px;
          margin-top: 12px;
          white-space: pre-wrap;
          word-break: break-word;
        }
        .status { color: #8696a0; font-size: 13px; margin-top: 8px; }
        a { color: #25d366; text-decoration: none; }
      </style>
    </head>
    <body>
      <div class="app">
        <header>
          <span>●</span>
          <div>Memorae.ai Demo — WhatsApp-style UI</div>
        </header>
        <div class="content">
          <div class="card">
            <div class="label">User Number / ID</div>
            <input id="userId" placeholder="e.g., 15551234567" value="demo-user" />
            <div class="status">We use this as the WhatsApp number/user identifier.</div>
          </div>

          <div class="card">
            <div class="label">Create Reminder (like sending a WhatsApp message)</div>
            <div class="row">
              <textarea id="reminderText" placeholder="Text like: Remind me to call Mom at 7pm"></textarea>
              <button id="sendReminder">Send Message</button>
            </div>
            <div id="reminderResult" class="bubble" style="display:none;"></div>
          </div>

          <div class="card">
            <div class="label">Recall Recent Conversation</div>
            <div class="row">
              <textarea id="recallQuestion" placeholder="Ask based on last 5 messages"></textarea>
              <button id="askRecall">Ask</button>
            </div>
            <div id="recallResult" class="bubble" style="display:none;"></div>
          </div>

          <div class="card">
            <div class="label">API Endpoints</div>
            <div class="status">
              POST /message, POST /recall, POST /whatsapp (form-data). <br/>
              This page calls /message and /recall directly.
            </div>
          </div>
        </div>
      </div>
      <script>
        const reminderBtn = document.getElementById("sendReminder");
        const recallBtn = document.getElementById("askRecall");
        const userIdEl = document.getElementById("userId");
        const reminderTextEl = document.getElementById("reminderText");
        const recallQuestionEl = document.getElementById("recallQuestion");
        const reminderResult = document.getElementById("reminderResult");
        const recallResult = document.getElementById("recallResult");

        async function postJSON(url, payload) {
          const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          });
          const data = await res.json().catch(() => ({}));
          if (!res.ok) {
            throw new Error(data.error || "Request failed");
          }
          return data;
        }

        reminderBtn.addEventListener("click", async () => {
          const user_id = userIdEl.value.trim();
          const text = reminderTextEl.value.trim();
          if (!user_id || !text) { alert("Enter user id and message"); return; }
          reminderBtn.disabled = true;
          reminderBtn.textContent = "Sending...";
          reminderResult.style.display = "none";
          try {
            const data = await postJSON("/message", { user_id, text });
            reminderResult.textContent = `⏰ Reminder set\\nTask: ${data.task}\\nTime: ${data.remind_at}`;
            reminderResult.style.display = "block";
          } catch (err) {
            alert(err.message);
          } finally {
            reminderBtn.disabled = false;
            reminderBtn.textContent = "Send Message";
          }
        });

        recallBtn.addEventListener("click", async () => {
          const user_id = userIdEl.value.trim();
          const question = recallQuestionEl.value.trim();
          if (!user_id || !question) { alert("Enter user id and question"); return; }
          recallBtn.disabled = true;
          recallBtn.textContent = "Thinking...";
          recallResult.style.display = "none";
          try {
            const data = await postJSON("/recall", { user_id, question });
            recallResult.textContent = data.answer || "No answer";
            recallResult.style.display = "block";
          } catch (err) {
            alert(err.message);
          } finally {
            recallBtn.disabled = false;
            recallBtn.textContent = "Ask";
          }
        });
      </script>
    </body>
    </html>
    """
