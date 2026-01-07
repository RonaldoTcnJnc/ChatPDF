#!/usr/bin/env python3
"""
Identificar y mostrar secciones de un PDF sin indexarlas.
"""

from backend.rag_system import RAGSystem

# Crear instancia del RAG
rag = RAGSystem()

# Ruta a tu PDF
pdf_path = "backend/pdfs/tu_documento.pdf"  # Cambiar por tu PDF

# Opción 1: Mostrar estructura de forma legible
print("\\n📄 Mostrando estructura del PDF:\\n")
rag.print_pdf_structure(pdf_path)

# Opción 2: Obtener datos como diccionario para procesamiento
sections = rag.identify_pdf_sections(pdf_path)

print("\\n📊 Datos estructurados:")
for section_type, info in sections.items():
    print(f"\\n{section_type}:")
    print(f"  - Título: {info['title']}")
    print(f"  - Páginas: {info['pages']}")
    print(f"  - Palabras: {info['word_count']}")
    print(f"  - Chunks: {info['chunk_count']}")

# Opción 3: Acceder a contenido de una sección específica
if 'abstract' in sections:
    abstract_content = sections['abstract']['content']
    print(f"\\n📌 ABSTRACT COMPLETO:\\n{abstract_content}")
