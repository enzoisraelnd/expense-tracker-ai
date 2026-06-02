from langchain_core.chat_history import InMemoryChatMessageHistory

# almacén de sesiones — un dict simple por ahora
# session_id → InMemoryChatMessageHistory
_store: dict = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
  """
  Returns the chat history for a session.
  Creates a new one if it doesn't exist.
  """
  if session_id not in _store:
    _store[session_id] = InMemoryChatMessageHistory()
  return _store[session_id]

def clear_session(session_id: str):
  """Crears the history for a session."""
  if session_id in _store:
    del _store[session_id]