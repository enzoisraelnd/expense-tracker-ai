from dotenv import load_dotenv
load_dotenv()

from app.extractor import extract

# caso 1: mensaje con gasto claro
result = extract("gaste 45 soles en almuerzo hoy")
if result.success:
  print(f"✓ Monto:      {result.expense.amount}")
  print(f"✓ Categoría:  {result.expense.category}")
  print(f"✓ Descripción:{result.expense.description}")
  print(f"✓ Fecha:      {result.expense.expense_date}")
  print(f"✓ Es gasto:   {result.expense.is_expense}")
else:
  print(f"x Error: {result.error}")
  
print("---")

# caso 2: mensaje que NO es un gasto
result2 = extract("¿cuánto gasté esta semana?")
if result2.success:
    print(f"¿Es gasto? {result2.expense.is_expense}")  # → False
else:
    print(f"✗ Error: {result2.error}")

