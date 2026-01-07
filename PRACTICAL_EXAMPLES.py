#!/usr/bin/env python3
"""
EJEMPLOS PRÁCTICOS - Sistema de Indexación por Secciones
=========================================================

Este documento contiene ejemplos prácticos de cómo usar el nuevo sistema.
"""

# ============================================================================
# EJEMPLO 1: Cargar un PDF con secciones automáticas
# ============================================================================

def ejemplo_1_cargar_pdf():
    """Cargar un PDF y automáticamente indexar sus secciones."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 1: Cargar PDF con Secciones Automáticas")
    print("="*60)
    
    # Inicializar chatbot
    chatbot = ChatbotRAG()
    
    # Cargar un PDF - AUTOMÁTICAMENTE detecta y indexa secciones
    pdf_path = "papers/research_paper.pdf"
    chatbot.load_single_pdf(pdf_path)
    
    # Salida esperada:
    # 📑 Extrayendo secciones del PDF...
    # ✅ Sección 'abstract' detectada: 150 palabras, 1 chunks
    # ✅ Sección 'introduction' detectada: 500 palabras, 2 chunks
    # ... etc
    # ✅ PDF procesado con secciones: research_paper.pdf - 9 chunks agregados


# ============================================================================
# EJEMPLO 2: Usuario pregunta por una sección específica
# ============================================================================

def ejemplo_2_busqueda_seccion():
    """El usuario pregunta por una sección y el bot responde automáticamente."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 2: Búsqueda de Sección Específica")
    print("="*60)
    
    chatbot = ChatbotRAG()
    chatbot.load_single_pdf("papers/research_paper.pdf")
    
    # Diferentes formas de pedir el abstract
    preguntas = [
        "Show me the abstract",
        "Muestra el resumen",
        "Cuál es el abstract?",
        "Dame el resumen del paper",
    ]
    
    for pregunta in preguntas:
        print(f"\\n👤 Usuario: {pregunta}")
        respuesta = chatbot.get_response(pregunta, use_rag=True)
        print(f"🤖 Bot: {respuesta[:200]}...")


# ============================================================================
# EJEMPLO 3: Acceso directo a secciones mediante RAG
# ============================================================================

def ejemplo_3_acceso_directo():
    """Acceso directo a secciones mediante métodos del RAG."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 3: Acceso Directo a Secciones (RAG)")
    print("="*60)
    
    chatbot = ChatbotRAG()
    chatbot.load_single_pdf("papers/research_paper.pdf")
    
    # Obtener contenido completo de una sección
    abstract = chatbot.rag.get_section_content("abstract", "research_paper.pdf")
    print(f"\\n📄 ABSTRACT:\\n{abstract}")
    
    # Recuperar chunks específicos de una sección
    chunks = chatbot.rag.retrieve_by_section("methods", "research_paper.pdf", k=5)
    print(f"\\n📊 MÉTODOS ({len(chunks)} chunks):")
    for i, (chunk, metadata) in enumerate(chunks, 1):
        print(f"\\n  Chunk {i}:")
        print(f"    Página: {metadata.get('page')}")
        print(f"    Contenido: {chunk[:150]}...")


# ============================================================================
# EJEMPLO 4: Búsqueda RAG normal (sin sección específica)
# ============================================================================

def ejemplo_4_busqueda_rag_normal():
    """Búsqueda RAG normal cuando no se especifica sección."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 4: Búsqueda RAG Normal (sin Sección Específica)")
    print("="*60)
    
    chatbot = ChatbotRAG()
    chatbot.load_single_pdf("papers/research_paper.pdf")
    
    preguntas = [
        "¿Cuál es el objetivo principal del estudio?",
        "What were the main findings?",
        "¿Qué se discutió respecto a las limitaciones?",
    ]
    
    for pregunta in preguntas:
        print(f"\\n👤 Usuario: {pregunta}")
        respuesta = chatbot.get_response(pregunta, use_rag=True)
        print(f"🤖 Bot: {respuesta[:300]}...")
        print(f"   [Búsqueda RAG - Múltiples secciones consideradas]")


# ============================================================================
# EJEMPLO 5: Búsqueda web vs RAG vs Sección
# ============================================================================

def ejemplo_5_flujo_completo():
    """Demostrar el flujo completo: Sección → Web → RAG."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 5: Flujo Completo de Búsqueda")
    print("="*60)
    
    chatbot = ChatbotRAG()
    chatbot.load_single_pdf("papers/research_paper.pdf")
    
    consultas = [
        ("Muestra el abstract", "SECCIÓN", "abstract"),
        ("¿Cuáles fueron los resultados?", "RAG", "Múltiples secciones"),
        ("Busca papers sobre el tema", "WEB", "arXiv/Google"),
    ]
    
    for consulta, tipo, notas in consultas:
        print(f"\\n📝 Consulta: {consulta}")
        print(f"   ↳ Tipo: {tipo}")
        print(f"   ↳ Notas: {notas}")
        respuesta = chatbot.get_response(consulta, use_rag=True)
        print(f"   ↳ Respuesta: {respuesta[:150]}...")


# ============================================================================
# EJEMPLO 6: Procesamiento sin secciones (compatibilidad hacia atrás)
# ============================================================================

def ejemplo_6_sin_secciones():
    """Si necesitas el comportamiento antiguo sin secciones."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 6: Procesamiento sin Secciones (Antiguo)")
    print("="*60)
    
    chatbot = ChatbotRAG()
    
    # Cargar sin secciones (comportamiento antiguo)
    print("\\nCargando PDF sin secciones...")
    chatbot.rag.add_pdf("papers/research_paper.pdf", use_sections=False)
    
    # Ahora funciona como antes
    respuesta = chatbot.get_response("¿Qué es el paper?", use_rag=True)
    print(f"\\n🤖 Respuesta (sin secciones): {respuesta[:300]}...")


# ============================================================================
# EJEMPLO 7: Múltiples PDFs con secciones
# ============================================================================

def ejemplo_7_multiples_pdfs():
    """Trabajar con múltiples PDFs y sus secciones."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 7: Múltiples PDFs con Secciones")
    print("="*60)
    
    chatbot = ChatbotRAG()
    
    # Cargar múltiples PDFs
    pdfs = [
        "papers/paper1.pdf",
        "papers/paper2.pdf",
        "papers/paper3.pdf",
    ]
    
    for pdf in pdfs:
        print(f"\\nCargando {pdf}...")
        chatbot.load_single_pdf(pdf)
    
    # Buscar en un PDF específico
    print(f"\\n\\nBuscando abstract en paper1.pdf:")
    abstract = chatbot.rag.get_section_content("abstract", "paper1.pdf")
    print(f"{abstract[:300]}...")
    
    # Buscar en todos (RAG normal)
    print(f"\\n\\nBuscando en TODOS los PDFs (RAG):")
    respuesta = chatbot.get_response("¿Cuál es la metodología utilizada?")
    print(f"{respuesta[:300]}...")


# ============================================================================
# EJEMPLO 8: Análisis de secciones detectadas
# ============================================================================

def ejemplo_8_analisis_secciones():
    """Analizar qué secciones fueron detectadas en un PDF."""
    from chatbot_rag import ChatbotRAG
    from section_extractor import SectionExtractor
    
    print("\\n" + "="*60)
    print("EJEMPLO 8: Análisis de Secciones Detectadas")
    print("="*60)
    
    # Extraer y analizar secciones
    extractor = SectionExtractor()
    
    # Simular extracción
    pdf_text = """
    ABSTRACT
    This paper presents...
    
    INTRODUCTION
    The field of machine learning...
    
    METHODS
    We used three approaches...
    
    RESULTS
    Our experiments showed...
    
    CONCLUSION
    This work demonstrates...
    """
    
    pages_data = [{"text": pdf_text, "page": 1}]
    sections = extractor.extract_sections(pdf_text, pages_data)
    
    print("\\n📊 Análisis de Secciones Detectadas:")
    summary = extractor.get_section_summary()
    
    for section_type, info in summary.items():
        print(f"\\n  📌 {section_type.upper()}")
        print(f"     Título: {info['title']}")
        print(f"     Palabras: {info['word_count']}")
        print(f"     Páginas: {info['pages']}")
        print(f"     Chunks: {info['chunks']}")


# ============================================================================
# EJEMPLO 9: Custom keywords y secciones
# ============================================================================

def ejemplo_9_custom_keywords():
    """Si necesitas agregar keywords personalizados."""
    from section_extractor import SectionExtractor
    
    print("\\n" + "="*60)
    print("EJEMPLO 9: Custom Keywords y Secciones")
    print("="*60)
    
    extractor = SectionExtractor()
    
    # Ver keywords actuales
    print("\\nKeywords actuales para 'abstract':")
    print(extractor.SECTION_PATTERNS['abstract']['keywords'])
    
    # Agregar keyword personalizado
    print("\\nAgregando keyword personalizado...")
    extractor.SECTION_PATTERNS['abstract']['keywords'].append('resumen ejecutivo')
    
    print(f"Nuevos keywords: {extractor.SECTION_PATTERNS['abstract']['keywords']}")
    
    # Ahora detectará "resumen ejecutivo" como abstract
    test_text = "RESUMEN EJECUTIVO\\nContent..."
    pages_data = [{"text": test_text, "page": 1}]
    
    sections = extractor.extract_sections(test_text, pages_data)
    print(f"\\nSecciones detectadas: {list(sections.keys())}")


# ============================================================================
# EJEMPLO 10: Debugging y Logs
# ============================================================================

def ejemplo_10_debugging():
    """Debugging y análisis de logs."""
    from chatbot_rag import ChatbotRAG
    
    print("\\n" + "="*60)
    print("EJEMPLO 10: Debugging y Logs")
    print("="*60)
    
    # Habilitar print detallados
    print("\\n[LOGS de Carga de PDF]")
    chatbot = ChatbotRAG()
    chatbot.load_single_pdf("papers/research_paper.pdf")
    
    # El sistema automáticamente genera logs como:
    # 📑 Extrayendo secciones del PDF...
    # ✅ Sección 'abstract' detectada: 150 palabras, 1 chunks
    # ... etc
    
    print("\\n[LOGS de Búsqueda de Sección]")
    print("Cuando el usuario pregunta 'Show me the abstract':")
    print("  → _detect_section_request() busca triggers")
    print("  → Encuentra 'show' (trigger) + 'abstract' (keyword)")
    print("  → Retorna ('abstract', ['abstract'])")
    print("  → get_response() detecta sección")
    print("  → Llama rag.get_section_content('abstract')")
    print("  → Retorna contenido completo de abstract")


# ============================================================================
# Función main para ejecutar ejemplos
# ============================================================================

if __name__ == "__main__":
    print("\\n" + "="*60)
    print("EJEMPLOS PRÁCTICOS - SISTEMA DE SECCIONES")
    print("="*60)
    
    print("\\n⚠️  NOTA: Estos ejemplos muestran cómo usar el sistema.")
    print("   Para ejecutarlos necesitas PDFs reales en ./papers/")
    print("\\nEstructura esperada:")
    print("   papers/")
    print("   ├── research_paper.pdf")
    print("   ├── paper1.pdf")
    print("   ├── paper2.pdf")
    print("   └── paper3.pdf")
    
    print("\\n" + "="*60)
    print("EJEMPLOS DISPONIBLES:")
    print("="*60)
    
    ejemplos = [
        (1, "Cargar PDF con Secciones Automáticas", ejemplo_1_cargar_pdf),
        (2, "Búsqueda de Sección Específica", ejemplo_2_busqueda_seccion),
        (3, "Acceso Directo a Secciones (RAG)", ejemplo_3_acceso_directo),
        (4, "Búsqueda RAG Normal (sin Sección)", ejemplo_4_busqueda_rag_normal),
        (5, "Flujo Completo de Búsqueda", ejemplo_5_flujo_completo),
        (6, "Procesamiento sin Secciones (Antiguo)", ejemplo_6_sin_secciones),
        (7, "Múltiples PDFs con Secciones", ejemplo_7_multiples_pdfs),
        (8, "Análisis de Secciones Detectadas", ejemplo_8_analisis_secciones),
        (9, "Custom Keywords y Secciones", ejemplo_9_custom_keywords),
        (10, "Debugging y Logs", ejemplo_10_debugging),
    ]
    
    for num, titulo, _ in ejemplos:
        print(f"\\n{num}. {titulo}")
    
    print("\\n" + "="*60)
    print("Para ejecutar un ejemplo específico:")
    print("  python3 -c 'from ejemplos import ejemplo_1_cargar_pdf; ejemplo_1_cargar_pdf()'")
    print("\\nO descomentar en main() el ejemplo que quieres probar.")
    print("="*60)
    
    # Descomentar para ejecutar un ejemplo:
    # ejemplo_1_cargar_pdf()
    # ejemplo_2_busqueda_seccion()
    # ... etc
