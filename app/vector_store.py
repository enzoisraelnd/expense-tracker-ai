import os
from dotenv import load_dotenv

load_dotenv()

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# ── configuración ─────────────────────────────────────────────
CHROMA_DIR        = "./data/chroma"     # carpeta local donde persiste
COLLECTION_NAME   = "session_summaries"
TOP_K_SUMMARIES   = 2                   # cuántos summaries cargar por sesión

def _get_vector_store() -> Chroma:
  """
  Return the Chroma vector store.
  Creates it if it doesn't exist.
  """
  return Chroma(
    collection_name=COLLECTION_NAME,
    embedding_function=OpenAIEmbeddings(
      model="text-embedding-3-small" # modelo de embeddings mas barato
    ),
    persist_directory=CHROMA_DIR
  )

def add_summary(summary_id: int, session_id: str, summary: str):
  """
  Adds a single summary to Chroma.
  Called during flush when a new summary is created.
  """
  vs = _get_vector_store()
  vs.add_texts(
    texts=[summary],
    metadatas=[{"session_id": session_id, "summary_id": str(summary_id)}],
    ids=[str(summary_id)]
  )

def sync_from_postgres():
  """
  Syncs Chroma with Postfres.
  Embeds summaries that exist in Postgres but not in Chroma.
  Called at session start to guarantee consistency.
  """
  from app.storage import get_all_summaries

  vs = _get_vector_store()

  # ids que ya están en Chroma
  existing = vs.get()
  existing_ids = set(existing["ids"]) if existing["ids"] else set()

  # todos los summaries en Postgres
  all_summaries = get_all_summaries()

  # embeber solo los que faltan
  missing = [s for s in all_summaries if str(s["id"]) not in existing_ids]

  if not missing:
    return
  
  print(f"[VectorStore] Syncing {len(missing)} summaries from Postgres...")

  vs.add_texts(
    texts=[s["summary"] for s in missing],
    metadatas=[
      {"session_id": s["session_id"], "summary_id": str(s["id"])}
      for s in missing
    ],
    ids=[str(s["id"]) for s in missing]
  )

  print(f"[VectorStore] Sync complete.")

def search_relevant_summaries(query: str, session_id: str) -> list[str]:
  """
  Searches for the most semantically relevant summaries
  for the current query.
  Return a list of summaries texts.
  """
  vs = _get_vector_store()

  # verificar si hay algo en Chroma
  existing = vs.get()
  if not existing["ids"]:
    return []
  
  docs = vs.similarity_search(
    query=query,
    k=TOP_K_SUMMARIES,
    filter={"session_id": session_id}
  )

  return [doc.page_content for doc in docs]

