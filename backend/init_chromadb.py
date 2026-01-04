import os
import argparse
from rag_system import RAGSystem
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def init_db(pdf_folder):
    """Inicializa la base de datos ChromaDB cargando PDFs."""
    print(f"🚀 Iniciando carga de PDFs desde: {pdf_folder}")
    
    if not os.path.exists(pdf_folder):
        print(f"❌ Carpeta no encontrada: {pdf_folder}")
        # Intentar crearla para que el usuario sepa dónde poner los archivos
        try:
            os.makedirs(pdf_folder)
            print(f"📂 Carpeta creada. Coloca tus PDFs aquí y vuelve a ejecutar.")
        except Exception as e:
            print(f"❌ No se pudo crear la carpeta: {e}")
        return

    # Inicializar RAG (usa valores por defecto o de config implícitamente)
    # Se asume que config.json existe en el mismo directorio si se ejecuta desde allí
    # o que los defaults de RAGSystem son suficientes.
    try:
        rag = RAGSystem()
        
        # Limpiar BD anterior si se desea un reinicio limpio (opcional, aquí no lo hacemos por defecto)
        # rag.clear_database() 
        
        # Cargar PDFs
        rag.add_pdf_folder(pdf_folder)
        
        # Mostrar stats
        stats = rag.get_stats()
        print("\n📊 Estado Final:")
        print(f"  - Total PDFs: {stats['total_pdfs']}")
        print(f"  - Total Chunks: {stats['total_chunks']}")
        print("✅ Proceso completado.")
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Inicializar base de datos ChromaDB con PDFs')
    parser.add_argument('--folder', type=str, default='./pdfs', help='Carpeta contenedora de PDFs')
    
    args = parser.parse_args()
    init_db(args.folder)
