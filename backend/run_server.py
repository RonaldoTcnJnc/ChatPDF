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

if __name__ == "__main__":
    import uvicorn
    from main import app
    
    print("\n" + "="*60)
    print("[SERVER] Iniciando servidor FastAPI")
    print(f"[SERVER] Cache directory: {os.environ.get('SENTENCE_TRANSFORMERS_HOME')}")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
