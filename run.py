from dotenv import load_dotenv
load_dotenv()

from app.main import chat
from app.memory import get_session_history, clear_session
from app.storage import get_total, get_by_category, reset_expenses  

SESSION_ID = "terminal-session"

def show_summary():
  """Prints stored expenses summary from JSON."""
  total = get_total()
  by_cat = get_by_category()

  print("\n=== Expense Summary (from storage) ===")
  if not by_cat:
    print("No expenses recorded yet.")
  else:
    for cat, amount in by_cat.items():
      print(f"  {cat:<20} S/ {amount:.2f}")
    print(f"  {'TOTAL':<20} S/ {total:.2f}")
  print("=" * 38)
  
def show_memory():
  """Prints the current conversation history."""
  history = get_session_history(SESSION_ID)
  messages = history.messages

  print("\n=== Current Memory ===")
  if not messages:
    print("No messages in memory.")
  else:
    for msg in messages:
      role = "You" if msg.type == "human" else "Assistant"
      # truncate long messages for readability
      content = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
      print(f"  [{role}] {content}")
  print("=" * 22)
  
def print_help():
  print("\nCommands:")
  print("  /summary  — show expenses from storage")
  print("  /memory   — show current conversation history")
  print("  /clear    — clear conversation memory")
  print("  /reset    — delete all stored expenses")
  print("  /quit     — exit")

def main():
  print("=== Expense Tracker AI ===")
  print("Type 'quit' to exit, 'clear' to see session info")
  print("-" * 40)
  
  while True:
    user_input = input("\nYou: ").strip()
    
    if not user_input:
      continue
    
    # commands
    if user_input.startswith("/"):
      cmd = user_input.lower()
      if cmd == "/quit":
        print("Bye!")
        break
      elif cmd == "/summary":
        show_summary()
      elif cmd == "/memory":
        show_memory()
      elif cmd == "/clear":
        clear_session(SESSION_ID)
        print("Memory cleared.")
      elif cmd == "/reset":
        confirm = input("Delete all expenses? (yes/no): ").strip().lower()
        if confirm == "yes":
          reset_expenses()
          print("All expenses deleted.")
        else:
          print("Cancelled.")
      elif cmd == "/help":
        print_help()
      else:
          print(f"Unknown command: {cmd}. Type /help for options.")
      continue
    
    response = chat(user_input, session_id=SESSION_ID)
    print(f"\nAssistant: {response}")
    
if __name__ == "__main__":
  main()
    
    
    