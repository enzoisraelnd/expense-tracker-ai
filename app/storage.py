import json
from pathlib import Path
from datetime import date
from app.extractor import ExtractedExpense

STORAGE_FILE = Path("data/expenses.json")

def _ensure_file():
  """Creates the file and folder if they don't exist."""
  STORAGE_FILE.parent.mkdir(exist_ok=True)
  if not STORAGE_FILE.exists():
    STORAGE_FILE.write_text("[]")
    
def save_expense(expense: ExtractedExpense):
  """Appends an expense to the JSON file."""
  _ensure_file()
  
  expenses = _load_all()
  expenses.append({
    "amount": expense.amount,
    "category": expense.category,
    "description": expense.description,
    "date": expense.expense_date.isoformat(),
  })
  
  STORAGE_FILE.write_text(
    json.dumps(expenses, indent=2, ensure_ascii=False)
  )
  
def get_total() -> float:
  """Returns the sum of all expenses."""
  _ensure_file()
  return sum(e["amount"] for e in _load_all())

def get_by_category() -> dict:
  """Returns total grouped by category."""
  _ensure_file()
  totals: dict = {}
  for e in _load_all():
    cat = e["category"]
    totals[cat] = totals.get(cat, 0) + e["amount"]
  return totals
  
def _load_all() -> list:
  return json.loads(STORAGE_FILE.read_text())

def reset_expenses():
  """Deltes all stored expenses."""
  _ensure_file()
  STORAGE_FILE.write_text("[]")
  