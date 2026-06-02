from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class ExtractedExpense(BaseModel):
  """
  Represents an expense extracted from natural language.
  Pydantic validates types before touching any database
  """
  amount: float = Field(
    description="Expense amount in soles. Always positive"
  )
  category: str = Field(
    description="Expense category: food, transport," \
    "entertainment, health, services, or others."
  )
  description: str = Field(
    description="Brief description of the expense."
  )
  expense_date: date = Field(
    description="Expense date. If not mentionen, use today"
  )
  is_expense: bool = Field(
    description="True if the message registers an expense." \
    "False if it is a question or query."
  )

class ExtractionResult(BaseModel):
  """
  Wrapper that always returns something - never raises to the caller.
  The chat layer decides what to do based on success/failure.
  """
  success: bool
  expense: Optional[ExtractedExpense] = None
  error: Optional[str] = None

  @property
  def failed(self) -> bool:
    return not self.success
  
EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
  {
    "system",
    """You are an expense extraction assistant.
    Your only job is to extract expense data from the user message.
    Today's date is {today}
    If the message is a question or does not mention an expense,
    set is_expense to false and use 0 for amount."""
  },
  {
    "human",
    "{message}"
  }
])

def extract(message: str) -> ExtractionResult:
  """
  Calls the LLM and return an ExtractionResult,
  Never raises - errors are captured in ExtractionResult.
  """
  try:
    # modelo pequeño y barato para extracción
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0      # temperatura 0 = respuestas deterministas
    )
    # with_structured_output le dice al LLM que responda
    # con la estructura exacta de ExtractedExpense
    chain = EXTRACTION_PROMPT | llm.with_structured_output(ExtractedExpense)
    
    expense = chain.invoke({
      "today": date.today().isoformat(),
      "message": message
    })

    return ExtractionResult(success=True, expense=expense)
  except Exception as e:
    return ExtractionResult(success=False, error=str(0))