from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from app.extractor import extract
from app.memory import get_session_history

# ── modelos ───────────────────────────────────────────────────
# modelo principal para el chat
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

# ── prompt ────────────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are a personal expense tracking assistant.
        Your job is to help the user register and query their expenses.
        Be concise and friendly. Always confirm registrations with
        the amount and category. Respond in the same language
        the user writes in."""
    ),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# ── chain con memoria ─────────────────────────────────────────
chain = prompt | llm

chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,          # ← función que devuelve el historial
    input_messages_key="input",
    history_messages_key="history",
)

def chat(message: str, session_id: str = "default") -> str:
  """
  Processes a user message and returns the assistant response.
  Automatically manages conversation history via session_id
  """
  # paso 1 — detectar si es un gasto
  extraction = extract(message)
  
  # paso 2 - construir contexto extra para el LLM
  # si es un gasto valido, le pasamos los datos estructurados
  # para que el LLM confirme con precision
  if extraction.success and extraction.expense.is_expense:
    expense = extraction.expense
    context = (
      f"{message}\n\n"
      f"[Extracted: amount={expense.amount}, "
      f"category={expense.category}, "
      f"date={expense.expense_date}]"
    )
  else:
    context = message
    
  # paso 3 - llamar al LLM con memoria
  response = chain_with_memory.invoke(
    {"input": context},
    config={"configurable": {"session_id": session_id}}
  )
  
  return response.content
  
  
  
  