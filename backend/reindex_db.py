import os
import shutil
import sys
from pathlib import Path

# Add backend to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from rag_system import RAGSystem
from chatbot_rag import ChatbotRAG

def reindex():
    print("🔄 Iniciando reindexación de la base de datos...")
    
    # 1. Initialize RAG System
    # We use ChatbotRAG to load config properly
    chatbot = ChatbotRAG(config_path=os.path.join(os.path.dirname(__file__), "..", "config.json"))
    
    # 2. Clear existing database
    print("🗑️  Limpiando base de datos existente...")
    chatbot.rag.clear_database()
    
    # 3. Locate PDFs
    # Try multiple locations
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "pdfs"), # Root/pdfs
        os.path.join(os.path.dirname(__file__), "pdfs"),       # Backend/pdfs
        "./pdfs"                                               # CWD/pdfs
    ]
    
    pdf_folder = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            # Check if has PDFs
            if list(Path(path).glob("*.pdf")):
                pdf_folder = path
                break
    
    if not pdf_folder:
        print("❌ No se encontró carpeta de PDFs con archivos.")
        return
    
    print(f"📂 Carpeta de PDFs encontrada: {pdf_folder}")
    
    # 4. Re-load PDFs
    print("📚 Re-procesando documentos (esto puede tardar)...")
    chatbot.load_pdfs(pdf_folder)
    
    print("\n✅ Reindexación completada con éxito.")
    print("   - Tamaño de chunk: 250 palabras")
    print("   - Base de datos optimizada")

if __name__ == "__main__":
    reindex()
