import os
import json
from dotenv import load_dotenv

load_dotenv()

import redis
import tiktoken
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
  BaseMessage,
  SystemMessage,
  messages_from_dict, 
  message_to_dict
)
from langchain_openai import ChatOpenAI

# ── configuración ─────────────────────────────────────────────
RECENT_TOKEN_LIMIT  = 1500
RECENT_MSG_LIMIT = 10 
SUMMARY_MODEL = "gpt-4o-mini"
SINGLE_MSG_LIMIT   = 500 

def _count_tokens(messages: list[BaseMessage]) -> int:
  enc = tiktoken.encoding_for_model("gpt-4o-mini")
  return sum(len(enc.encode(m.content)) for m in messages)

def _summarize(messages: list[BaseMessage]) -> str:
  """
  Calls a cheap LLM to compress old messages into a summary.
  Preserves amount, categories and dates - critital for expense tracking
  """
  llm = ChatOpenAI(model=SUMMARY_MODEL, temperature=0)
  history_text = "\n".join([
    f"{msg.type.upper()}: {msg.content}"
    for msg in messages
  ])

  prompt = f"""Summarize this expense tracking conversation.
  IMPORTANT: preserve all exact amounts, categories and dates.
  Never generalize numbers — keep them exact.

  Conversation:
  {history_text}

  Summary:"""

  response = llm.invoke(prompt)
  return response.content



class RedisChatMessageHistory(BaseChatMessageHistory):
  """
  Chat history stored in Redis with automatic summarization.
  Compresses when recent messages exceed RECENT_MSG_LIMIT.
  The summary is never counted against the limit — only
  new messages are tracked.
  """

  def __init__(self, session_id: str, ttl: int = 3600):
    self.session_id = session_id
    self.ttl = ttl
    self.client = redis.Redis(
      host=os.getenv("REDIS_HOST", "localhost"),
      port=int(os.getenv("REDIS_PORT", 6379)),
      decode_responses=True,
    )
    self._key = f"chat_history:{session_id}"

  @property
  def messages(self) -> list[BaseMessage]:
    """Loads messages from Redis."""
    data = self.client.get(self._key)
    if not data:
      return []
    return messages_from_dict(json.loads(data))
  
  def add_message(self, message: BaseMessage):
    msg_tokens = _count_tokens([message])
    if msg_tokens > SINGLE_MSG_LIMIT:
      raise ValueError(
          f"Message too large: {msg_tokens} tokens "
          f"(max {SINGLE_MSG_LIMIT})"
      )

    current = self.messages
    current.append(message)

    # separar summary de mensajes recientes
    if current and current[0].type == "system":
        recent = current[1:]
    else:
        recent = current

    too_many_messages = len(recent) > RECENT_MSG_LIMIT
    too_many_tokens   = _count_tokens(recent) > RECENT_TOKEN_LIMIT

    # comprimir solo cuando hay suficientes mensajes recientes
    if too_many_messages or too_many_tokens:
      reason = "messages" if too_many_messages else "tokens"
      print(f"\n[Memory] Limit reached ({reason}), compressing...")
      current = self._compress(current)

    self._save(current)

  def _compress(self, messages: list[BaseMessage]) -> list[BaseMessage]:
    """
    Keeps the last 4 messages intact.
    Summarizes everything before that.
    """
    # separar summary previo y mensajes
    if messages and messages[0].type == "system":
      previous_summary = messages[0].content
      rest = messages[1:]
    else:
      previous_summary = None
      rest = messages

    to_summarize = rest[:-4]
    to_keep      = rest[-4:]

    if not to_summarize:
      return messages

    print(f"\n[Memory] Compressing {len(to_summarize)} messages...")

    try:
      # si hay summary previo, incluirlo en la compresión
      msgs_to_compress = to_summarize
      if previous_summary:
        intro = SystemMessage(content=previous_summary)
        msgs_to_compress = [intro] + to_summarize

      summary_text = _summarize(msgs_to_compress)
      summary_msg  = SystemMessage(
        content=f"[Summary of previous conversation]:\n{summary_text}"
      )
      print(f"[Memory] Compressed ok.")
      return [summary_msg] + to_keep

    except Exception as e:
      print(f"[Memory] Compression failed: {e}")
      return messages

  def _save(self, messages: list[BaseMessage]):
    """Persists messages to Redis with TTL"""
    self.client.set(
      self._key,
      json.dumps([message_to_dict(m) for m in messages]),
      ex=self.ttl
    )
  
  def clear(self):
    """Deletes the history from Redis."""
    self.client.delete(self._key)

def clear_session(session_id: str):
  """Clears the history for a session."""
  RedisChatMessageHistory(session_id=session_id).clear()

def flush_session(session_id: str) -> bool:
  """
  Persists summary to Postgres and Chroma, clears Redis.
  """
  from app.storage import save_session_summary
  from app.vector_store import add_summary

  history = get_session_history(session_id)
  messages = history.messages

  if not messages:
    return False
  
  # extraer el summary si existe, o generar uno nuevo
  if messages and messages[0].type == "system":
    summary_text = messages[0].content
  else:
    if len(messages) < 2:
      return False
    summary_text = _summarize(messages)

  # persistir en Postgres
  summary_id  = save_session_summary(
    session_id=session_id,
    summary=summary_text
  )

  # embeber en Chroma
  add_summary(
    summary_id=summary_id,
    session_id=session_id,
    summary=summary_text,
  )

  # limpiar Redis
  clear_session(session_id)

  print(f"[Memory] Session flushed to Postgres.")
  return True

def get_session_history(session_id: str) -> RedisChatMessageHistory:
  history = RedisChatMessageHistory(session_id=session_id)

  # si Redis está vacío, intentar cargar el summary histórico de Postgres
  if not history.messages:
    from app.storage import get_latest_summary
    from app.vector_store import sync_from_postgres, search_relevant_summaries
    from langchain_core.messages import SystemMessage

    # 1. sincronizar Chroma con Postgres
    sync_from_postgres()

    # 2. buscar summaries relevantes en Chroma
    # usamos un query genérico al inicio — sin mensaje del usuario aún
    relevant = search_relevant_summaries(
      query="expense tracking history",
      session_id=session_id,
    )

    if relevant:
      # combinar los summaries relevantes en uno solo
      combined = "\n\n---\n\n".join(relevant)
      context = f"[Relevant history from previous sessions]:\n{combined}"
      print(f"[Memory] Loaded {len(relevant)} relevant summaries from Chroma.")
      history.add_message(SystemMessage(content=context))

    else:
      # fallback — cargar el último summary de Postgres
      previous_summary = get_latest_summary(session_id)
      if previous_summary:
        print(f"[Memory] Fallback: loading latest summary from Postgres...")
        history.add_message(SystemMessage(content=previous_summary))

  return history