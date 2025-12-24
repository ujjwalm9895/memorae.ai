from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    text = Column(String)
    remind_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ✅ MEMORAE.AI STYLE – CONVERSATION MEMORY
class ConversationMemory(Base):
    __tablename__ = "conversation_memory"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
