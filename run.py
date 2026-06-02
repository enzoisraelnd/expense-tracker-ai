from dotenv import load_dotenv
load_dotenv()

from app.main import chat

def main():
  print("=== Expense Tracker AI ===")
  print("Type 'quit' to exit, 'clear' to see session info")
  print("-" * 40)
  
  session_id = "terminal-session"
  
  while True:
    user_input = input("\nYou: ").strip()
    
    if not user_input:
      continue
    
    if user_input.lower() == "quit":
      print("Bye!")
      break
    
    response = chat(user_input, session_id=session_id)
    print(f"\nAssistant: {response}")
    
if __name__ == "__main__":
  main()
    
    
    