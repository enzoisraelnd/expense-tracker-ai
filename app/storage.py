import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Optional

load_dotenv()  
from app.extractor import ExtractedExpense

def _get_connection():
  """Creates a new Postgres connection from environment variables."""
  return psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", 5432),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
    dbname=os.getenv("POSTGRES_DB"),
  )

def save_expense(expense: ExtractedExpense):
  """Insert an expense into Postgres."""
  conn = _get_connection()
  try:
    with conn.cursor() as cur:
      cur.execute("""
        INSERT INTO expenses (amount, category, description, expense_date)
                VALUES (%s, %s, %s, %s)
        """, (
          expense.amount,
          expense.category,
          expense.description,
          expense.expense_date,
      ))
    conn.commit()
  finally:
    conn.close()

def get_total() -> float:
  """Returns the sum of all expenses."""
  conn = _get_connection()
  try:
    with conn.cursor() as cur:
      cur.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
      return float(cur.fetchone()[0])
  finally:
    conn.close()

def get_by_category() -> dict:
  """Returns totals grouped by category."""
  conn = _get_connection()
  try:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT category, SUM(amount) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
        """)
        return {row["category"]: float(row["total"]) for row in cur.fetchall()}
  finally:
    conn.close()

def reset_expenses():
  """Deletes all stored expenses."""
  conn = _get_connection()
  try:
    with conn.cursor() as cur:
      cur.execute("DELETE FROM expenses")
    conn.commit()
  finally:
    conn.close()

def save_session_summary(session_id: str, summary: str):
  """Persists a session summary to Postgres. Returns the new id."""
  conn = _get_connection()
  try:
    with conn.cursor() as cur:
      cur.execute("""
        INSERT INTO session_summaries (session_id, summary)
        VALUES (%s, %s)
        RETURNING id
      """, (session_id, summary))
      summary_id = cur.fetchone()[0]
    conn.commit()
    return summary_id
  finally:
    conn.close()

def get_latest_summary(session_id: str) -> Optional[str]:
  """Returns the most recent summary for a session."""
  conn = _get_connection()
  try:
    with conn.cursor() as cur:
      cur.execute("""
        SELECT summary
        FROM session_summaries
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT 1
      """, (session_id,))
      row = cur.fetchone()
      return row[0] if row else None
  finally:
    conn.close()

def get_all_summaries(session_id: str = None) -> list[dict]:
  """
  Returns all session summaries from Postgres.
  Optionally filteres by session_id
  """
  conn = _get_connection()
  try:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
      if session_id:
        cur.execute("""
          SELECT id, session_id, summary, created_at
          FROM session_summaries
          WHERE session_id = %s
          ORDER BY created_at ASC
        """)
      else:
        cur.execute("""
          SELECT id, session_id, summary, created_at
          FROM session_summaries
          ORDER BY created_at ASC
        """)

      return [dict(row) for row in cur.fetchall()]
  finally:
    conn.close()