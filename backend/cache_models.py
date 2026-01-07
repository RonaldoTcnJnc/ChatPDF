#!/usr/bin/env python3
"""Script para pre-cachear los modelos necesarios"""
import os
import sys
from pathlib import Path

# Configurar variables de entorno para cachés locales
os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(Path(__file__).parent / '.cache' / 'sentence-transformers')
os.environ['HF_HOME'] = str(Path(__file__).parent / '.cache' / 'huggingface')

# Crear directorios si no existen
for env_var in ['SENTENCE_TRANSFORMERS_HOME', 'HF_HOME']:
    cache_dir = os.environ.get(env_var)
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)

print("="*60)
print("[CACHE] Descargando modelos necesarios...")
print("="*60 + "\n")

try:
    print("[1] Descargando modelo Sentence Transformers...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("OK: Modelo Sentence Transformers descargado\n")
except Exception as e:
    print(f"ERROR: {e}\n")
    sys.exit(1)

print("="*60)
print("[CACHE] Todos los modelos han sido descargados exitosamente")
print("="*60 + "\n")
