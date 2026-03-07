import os
import shutil
from sqlalchemy import text
from database.db import engine, Base
from database.models import Document

def reset_system():
    print("⚠️  WARNING: This will delete all documents, vector embeddings, and graph data.")
    confirm = input("Type 'yes' to proceed: ")
    if confirm.lower() != "yes":
        print("Operation cancelled.")
        return

    # 1. Clear PostgreSQL Documents Table
    print("Cleaning Database...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE documents CASCADE;"))
        conn.commit()

    # 2. Clear ChromaDB
    print("Cleaning Vector Store...")
    if os.path.exists("./chroma_db"):
        shutil.rmtree("./chroma_db")

    # 3. Clear Cog-RAG Graph
    print("Cleaning Graph Data...")
    if os.path.exists("storage/graph_data.pkl"):
        os.remove("storage/graph_data.pkl")

    print("✅ System Reset Complete. Please restart the backend and re-upload your files.")

if __name__ == "__main__":
    reset_system()