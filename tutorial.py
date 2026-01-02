"""
🎓 TUTORIAL COMPLETO - Sistema RAG para Chatbot Local

Este script enseña paso a paso cómo funciona el sistema RAG.
"""

def tutorial_paso_1():
    """Paso 1: Entender qué es RAG"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PASO 1: ¿QUÉ ES RAG?                                         ║
╚════════════════════════════════════════════════════════════════╝

RAG = Retrieval-Augmented Generation

Es una técnica que combina:

1. RECUPERACIÓN (Retrieval)
   - Busca información relevante en documentos
   - Usa embeddings (vectores de números)
   - Busca semánticamente (por significado, no palabras clave)

2. GENERACIÓN AUMENTADA (Augmented Generation)
   - Toma el contexto recuperado
   - Lo envía al modelo (Llama 3)
   - El modelo genera respuestas más precisas

VENTAJAS:
✓ Respuestas basadas en tus documentos
✓ Funciona completamente local (sin API)
✓ Bajo costo computacional
✓ Privado (datos en tu PC)

FLUJO:
  [Pregunta] → [Buscar en PDFs] → [Contexto] → [Llama 3] → [Respuesta]
    """)


def tutorial_paso_2():
    """Paso 2: Componentes del Sistema"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PASO 2: COMPONENTES DEL SISTEMA                             ║
╚════════════════════════════════════════════════════════════════╝

1. PyMuPDF (pymupdf)
   - Extrae texto de archivos PDF
   - Rápido y preciso
   - Mantiene la estructura del documento

2. Sentence Transformers
   - Convierte texto a "embeddings" (vectores)
   - Modelo: all-MiniLM-L6-v2 (90MB, rápido)
   - Entiende significado semántico

3. ChromaDB
   - Base de datos vectorial
   - Almacena embeddings
   - Búsqueda rápida por similitud

4. LMStudio + Llama 3
   - Modelo local en tu PC
   - No requiere API
   - Privado y gratuito

ARQUITECTURA:
┌─────────────────────────────────────────────┐
│          TU CHATBOT RAG                     │
├─────────────────────────────────────────────┤
│  Entrada: Pregunta del usuario              │
│     ↓                                       │
│  [Sentence Transformers] → Vector           │
│     ↓                                       │
│  [ChromaDB] → Busca docs similares          │
│     ↓                                       │
│  [Contexto] + [Pregunta] → Formatea         │
│     ↓                                       │
│  [Llama 3 en LMStudio] → Genera respuesta   │
│     ↓                                       │
│  Salida: Respuesta mejorada                 │
└─────────────────────────────────────────────┘
    """)


def tutorial_paso_3():
    """Paso 3: Cómo usar el sistema"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PASO 3: CÓMO USAR EL SISTEMA                                ║
╚════════════════════════════════════════════════════════════════╝

INSTALACIÓN:
1. pip install -r requirements.txt

PREPARACIÓN:
1. Crea carpeta "pdfs" en el proyecto
2. Coloca tus papers/PDFs ahí
3. Asegúrate que LMStudio esté corriendo

INICIO:
1. python quick_start.py
2. Escribe tus preguntas
3. El sistema buscará en los PDFs y responderá

COMANDOS ESPECIALES:
- 'salir'     → Termina el chat
- 'limpiar'   → Limpia historial
- 'stats'     → Muestra estadísticas
- 'cargar /ruta/pdf' → Carga un PDF específico

EJEMPLO DE USO PROGRAMÁTICO:
┌────────────────────────────────────────────┐
│ from chatbot_rag import ChatbotRAG          │
│                                             │
│ chatbot = ChatbotRAG()                      │
│ chatbot.load_pdfs("./pdfs")                 │
│                                             │
│ response = chatbot.get_response(            │
│     "¿De qué habla el paper?",              │
│     use_rag=True,                           │
│     k=3  # Top 3 documentos más relevantes  │
│ )                                           │
│ print(response)                             │
└────────────────────────────────────────────┘
    """)


def tutorial_paso_4():
    """Paso 4: Optimización"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PASO 4: OPTIMIZACIÓN                                         ║
╚════════════════════════════════════════════════════════════════╝

PARÁMETROS AJUSTABLES (en rag_system.py):

1. chunk_size (por defecto: 500 palabras)
   - Más grande → contexto más largo, menos chunks
   - Más pequeño → más chunks, búsqueda granular
   - RECOMENDACIÓN: 300-800

2. overlap (por defecto: 100 palabras)
   - Solapamiento entre chunks
   - Evita pérdida de contexto en bordes
   - RECOMENDACIÓN: 50-200

3. embedding_model (por defecto: all-MiniLM-L6-v2)
   - all-MiniLM-L6-v2 (rápido, 90MB)
   - all-mpnet-base-v2 (preciso, 420MB)
   - multilingual-e5-base (multiidioma, 200MB)

4. k (recuperación, por defecto: 3)
   - Cuántos documentos recuperar
   - Más k = más contexto, más lento
   - RECOMENDACIÓN: 3-5

5. temperature (por defecto: 0.7)
   - 0 = Determinista (siempre igual)
   - 1 = Creativo/Variable
   - RECOMENDACIÓN: 0.5-0.8

OPTIMIZACIÓN SEGÚN CASO:
┌─────────────────────────────────────────┐
│ CASO: Papers largos/densos              │
│ - chunk_size = 600                      │
│ - overlap = 150                         │
│ - k = 5                                 │
│ - embedding_model = all-mpnet-base-v2   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ CASO: Búsqueda rápida/simple             │
│ - chunk_size = 300                      │
│ - overlap = 50                          │
│ - k = 2                                 │
│ - embedding_model = all-MiniLM-L6-v2    │
└─────────────────────────────────────────┘
    """)


def tutorial_paso_5():
    """Paso 5: Troubleshooting"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║  PASO 5: SOLUCIÓN DE PROBLEMAS                               ║
╚════════════════════════════════════════════════════════════════╝

PROBLEMA: "No hay información en la base de datos"
SOLUCIÓN:
  1. Verifica que los PDFs estén en ./pdfs/
  2. Corre: python quick_start.py (para recargar)
  3. Usa comando 'stats' para ver chunks cargados

PROBLEMA: El modelo no responde
SOLUCIÓN:
  1. Verifica LMStudio en: http://localhost:1234
  2. Asegúrate el modelo está cargado
  3. Prueba con el script original a.py

PROBLEMA: Los embeddings son lentos
SOLUCIÓN:
  1. Usa: all-MiniLM-L6-v2 (por defecto)
  2. Reduce tamaño de PDFs
  3. Aumenta chunk_size

PROBLEMA: Memoria/Almacenamiento
SOLUCIÓN:
  1. Limpia chroma_db/ y recarga PDFs
  2. Usa comando 'limpiar' en el chat
  3. Reduce número de PDFs

COMANDO DE DEBUG:
  python -c "from chatbot_rag import ChatbotRAG; 
             c = ChatbotRAG(); 
             c.show_stats()"
    """)


def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║         🎓 TUTORIAL SISTEMA RAG - CHATBOT LOCAL              ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    while True:
        print("""
ÍNDICE DE TUTORIALES:
  1. ¿Qué es RAG?
  2. Componentes del Sistema
  3. Cómo Usar
  4. Optimización
  5. Troubleshooting
  6. Salir

¿Qué lección deseas ver? (1-6): """, end="")
        
        opcion = input().strip()
        
        if opcion == "1":
            tutorial_paso_1()
        elif opcion == "2":
            tutorial_paso_2()
        elif opcion == "3":
            tutorial_paso_3()
        elif opcion == "4":
            tutorial_paso_4()
        elif opcion == "5":
            tutorial_paso_5()
        elif opcion == "6":
            print("\n✅ ¡A aprender se ha dicho!\n")
            break
        else:
            print("❌ Opción no válida. Intenta de nuevo.")
        
        input("\n[Presiona ENTER para continuar]")


if __name__ == "__main__":
    main()
