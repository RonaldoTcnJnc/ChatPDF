#!/usr/bin/env python3
"""
🚀 QUICK START - Inicia el chatbot RAG directamente
Simplemente ejecuta: python quick_start.py
"""

from chatbot_rag import ChatbotRAG
import os
import sys

def main():
    print("\n" + "="*60)
    print("🤖 CHATBOT RAG LOCAL - Powered by Llama 3 & ChromaDB")
    print("="*60)
    
    # Crear carpeta de PDFs si no existe
    if not os.path.exists("./pdfs"):
        os.makedirs("./pdfs")
        print("\n📁 Carpeta 'pdfs' creada.")
        print("⚠️  Coloca tus PDFs (papers, investigaciones, etc) aquí.")
        print("   Los PDFs se cargarán automáticamente en el próximo inicio.")
    
    print("\n✨ Inicializando...")
    
    try:
        # Inicializar chatbot
        chatbot = ChatbotRAG(
            base_url="http://localhost:1234/v1",
            model_name="lmstudio-community/Meta-Llama-3-8B-Instruct",
            rag_db_path="./chroma_db"
        )
        
        # Cargar PDFs
        chatbot.load_pdfs("./pdfs")
        
        # Mostrar estadísticas
        stats = chatbot.get_stats()
        print(f"\n📊 Sistema cargado:")
        print(f"   - Chunks en base de datos: {stats['total_chunks']}")
        print(f"   - Modelo de embeddings: {stats['embedding_model']}")
        
        if stats['total_chunks'] == 0:
            print("\n⚠️  No hay PDFs cargados.")
            print("   Próximos pasos:")
            print("   1. Coloca PDFs en la carpeta ./pdfs/")
            print("   2. Corre el script nuevamente")
        
        # Iniciar chat
        print("\n" + "="*60)
        chatbot.interactive_chat(folder_path="./pdfs")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Verifica que:")
        print("   - LMStudio esté corriendo en http://localhost:1234")
        print("   - El modelo Meta-Llama-3-8B-Instruct esté cargado")
        print("   - Tengas conexión a internet para descargar modelos")
        sys.exit(1)

if __name__ == "__main__":
    main()
