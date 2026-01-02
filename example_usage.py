"""
Script de ejemplo para usar el sistema RAG de forma programática.
Muestra diferentes casos de uso.
"""

from chatbot_rag import ChatbotRAG
import os

def ejemplo_basico():
    """Ejemplo básico: cargar PDFs y hacer preguntas"""
    print("=" * 60)
    print("EJEMPLO 1: Uso Básico")
    print("=" * 60)
    
    chatbot = ChatbotRAG()
    
    # Crear carpeta de PDFs si no existe
    if not os.path.exists("./pdfs"):
        os.makedirs("./pdfs")
        print("📂 Carpeta 'pdfs' creada. Coloca tus archivos PDF aquí.")
    
    # Cargar PDFs
    chatbot.load_pdfs("./pdfs")
    
    # Hacer preguntas
    preguntas = [
        "¿Cuál es el tema principal?",
        "¿Cuáles son los hallazgos clave?",
        "¿Qué metodología se utilizó?"
    ]
    
    for pregunta in preguntas:
        print(f"\n👤 Pregunta: {pregunta}")
        response = chatbot.get_response(pregunta, use_rag=True, k=3)
        print(f"🤖 Respuesta: {response[:200]}...\n")


def ejemplo_pdf_especifico():
    """Ejemplo 2: Cargar un PDF específico"""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: PDF Específico")
    print("=" * 60)
    
    chatbot = ChatbotRAG()
    
    # Cargar un PDF específico (reemplaza la ruta)
    pdf_path = "./pdfs/example.pdf"
    if os.path.exists(pdf_path):
        chatbot.load_single_pdf(pdf_path)
        print(f"✅ PDF cargado: {pdf_path}")
    else:
        print(f"⚠️  No existe: {pdf_path}")
    
    # Ver estadísticas
    chatbot.show_stats()


def ejemplo_con_y_sin_rag():
    """Ejemplo 3: Comparar respuestas con y sin RAG"""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Con vs Sin RAG")
    print("=" * 60)
    
    chatbot = ChatbotRAG()
    chatbot.load_pdfs("./pdfs")
    
    pregunta = "¿Cuál es el problema principal abordado?"
    
    print(f"\n❓ Pregunta: {pregunta}\n")
    
    # Sin RAG
    print("❌ Respuesta SIN RAG:")
    print("-" * 40)
    response_sin_rag = chatbot.get_response(pregunta, use_rag=False)
    print(response_sin_rag)
    
    # Limpiar historial
    chatbot.clear_chat_history()
    
    # Con RAG
    print("\n✅ Respuesta CON RAG:")
    print("-" * 40)
    response_con_rag = chatbot.get_response(pregunta, use_rag=True, k=3)
    print(response_con_rag)


def ejemplo_interactivo_simple():
    """Ejemplo 4: Chat interactivo simple"""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Chat Interactivo")
    print("=" * 60)
    
    chatbot = ChatbotRAG()
    
    # Usar la función interactiva integrada
    chatbot.interactive_chat(folder_path="./pdfs")


def ejemplo_multiples_pdfs():
    """Ejemplo 5: Trabajar con múltiples PDFs"""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Múltiples PDFs")
    print("=" * 60)
    
    chatbot = ChatbotRAG()
    
    # Crear carpeta
    if not os.path.exists("./pdfs"):
        os.makedirs("./pdfs")
    
    # Cargar todos los PDFs
    print("📂 Cargando PDFs desde ./pdfs/")
    chatbot.load_pdfs("./pdfs")
    
    stats = chatbot.get_stats()
    print(f"\n📊 Total de chunks procesados: {stats['total_chunks']}")
    print(f"📊 Modelo de embeddings: {stats['embedding_model']}")
    
    # Hacer una pregunta que busca en todos los PDFs
    pregunta = "¿Cuáles son las conclusiones generales?"
    print(f"\n❓ Pregunta (busca en todos los PDFs): {pregunta}")
    response = chatbot.get_response(pregunta, use_rag=True, k=5)
    print(f"\n🤖 Respuesta:\n{response}")


if __name__ == "__main__":
    print("\n🚀 Ejemplos de uso del Sistema RAG\n")
    
    # Menú de ejemplos
    print("Elige un ejemplo:")
    print("1. Uso Básico")
    print("2. PDF Específico")
    print("3. Con vs Sin RAG")
    print("4. Chat Interactivo")
    print("5. Múltiples PDFs")
    print("0. Salir")
    
    opcion = input("\n¿Qué ejemplo deseas ejecutar? (0-5): ").strip()
    
    if opcion == "1":
        ejemplo_basico()
    elif opcion == "2":
        ejemplo_pdf_especifico()
    elif opcion == "3":
        ejemplo_con_y_sin_rag()
    elif opcion == "4":
        ejemplo_interactivo_simple()
    elif opcion == "5":
        ejemplo_multiples_pdfs()
    else:
        print("Saliendo...")
    
    print("\n✅ Ejemplo completado\n")
