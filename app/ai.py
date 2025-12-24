import json
import re
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from .config import GEMINI_API_KEY, TIMEZONE

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY
)

PROMPT = PromptTemplate(
    template="""
You are an AI assistant like Memorae.ai.

Convert the user message into a reminder.

STRICT RULES:
- Output ONLY valid JSON
- Datetime must be ISO 8601
- Datetime must include timezone ({timezone})
- No explanation text

Current datetime: {now}

User message:
{text}

Return JSON exactly like:
{{
  "intent": "CREATE_REMINDER",
  "task": "<short task>",
  "datetime": "<ISO datetime with timezone>",
  "type": "one_time"
}}
""",
    input_variables=["text", "now", "timezone"]
)

RECALL_PROMPT = PromptTemplate(
    template="""
You are an AI assistant like Memorae.ai.

The user is asking a question based on past conversation history.

Conversation history:
{history}

User question:
{question}

RULES:
- Answer naturally
- Be concise
- Use only the given history
""",
    input_variables=["history", "question"]
)

def recall_from_memory(history: str, question: str):
    response = llm.invoke(
        RECALL_PROMPT.format(
            history=history,
            question=question
        )
    )
    return response.content


def _extract_json(text: str):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group())

def extract_intent_and_time(user_text: str):
    response = llm.invoke(
        PROMPT.format(
            text=user_text,
            now=datetime.now().isoformat(),
            timezone=TIMEZONE
        )
    )

    data = _extract_json(response.content)
    return data
