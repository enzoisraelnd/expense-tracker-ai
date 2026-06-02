from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"✓ API key cargada: {api_key[:8]}...")
else:
    print("✗ No se encontró OPENAI_API_KEY en el .env")