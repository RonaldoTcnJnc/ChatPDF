#!/usr/bin/env python3
"""Script para ejecutar el servidor con configuración adecuada"""
import os
import sys
from pathlib import Path

# Configurar variables de entorno para sentence-transformers
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(Path(__file__).parent / '.cache' / 'sentence-transformers')
os.environ['HF_HOME'] = str(Path(__file__).parent / '.cache' / 'huggingface')
os.environ['TRANSFORMERS_CACHE'] = str(Path(__file__).parent / '.cache' / 'transformers')

# Hacer que los directorios existan
for env_var in ['SENTENCE_TRANSFORMERS_HOME', 'HF_HOME', 'TRANSFORMERS_CACHE']:
    cache_dir = os.environ.get(env_var)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

# Crear directorio de PDFs si no existe
pdfs_dir = Path(__file__).parent / 'pdfs'
pdfs_dir.mkdir(exist_ok=True)

if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("\n" + "="*70)
    print("🚀 [SERVER] Iniciando servidor FastAPI")
    print("="*70)
    print(f"📍 Dirección: http://0.0.0.0:8000")
    print(f"📍 Frontend en: http://localhost:5173")
    print(f"📍 API Docs: http://localhost:8000/docs")
    print(f"📚 Cache: {os.environ.get('SENTENCE_TRANSFORMERS_HOME')}")
    print("="*70 + "\n")
    
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000, 
            log_level="info",
            # Mostrar más detalles en caso de error
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n\n⛔ [SERVER] Servidor detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ [SERVER] Error al iniciar el servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

