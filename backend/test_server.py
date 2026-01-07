#!/usr/bin/env python3
"""Script de prueba para el servidor backend"""
import sys
import os

# Configurar encoding UTF-8 en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("[TEST] Iniciando pruebas del servidor...")
print("=" * 60)

# Test 1: Importar módulos
print("\n[1] Verificando importes...")
try:
    from chatbot_rag import ChatbotRAG
    print("   OK: ChatbotRAG importado correctamente")
except Exception as e:
    print(f"   ERROR: {e}")
    sys.exit(1)

# Test 2: Inicializar ChatbotRAG
print("\n[2] Inicializando ChatbotRAG...")
try:
    chatbot = ChatbotRAG()
    print(f"   OK: ChatbotRAG inicializado")
    print(f"   Provider: {chatbot.provider}")
    print(f"   Model: {chatbot.model_name}")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Prueba de get_response
print("\n[3] Probando get_response()...")
try:
    test_message = "Hola, como estas?"
    response = chatbot.get_response(test_message, use_rag=False)
    print(f"   OK: Respuesta recibida")
    print(f"   Tipo: {type(response)}")
    if isinstance(response, dict):
        print(f"   Keys: {response.keys()}")
        answer = response.get("answer", "")
        print(f"   Respuesta: {answer[:100]}...")
    else:
        print(f"   Respuesta: {str(response)[:100]}...")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Iniciar servidor FastAPI
print("\n[4] Iniciando servidor FastAPI...")
try:
    import uvicorn
    from main import app
    print("   OK: FastAPI app importada")
    print("\n" + "=" * 60)
    print("[SERVER] Iniciando en http://localhost:8000")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
