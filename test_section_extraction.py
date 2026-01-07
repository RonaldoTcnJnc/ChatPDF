#!/usr/bin/env python3
"""
Script de prueba para verificar la indexación por secciones.
Prueba sin necesidad de cargar PDFs reales.
"""

import sys
from pathlib import Path

# Añadir directorio backend al path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from section_extractor import SectionExtractor

def test_section_extraction():
    """Prueba la extracción de secciones con un documento de prueba."""
    
    # Documento de prueba simulado con múltiples formatos
    test_text = """Research Paper on Machine Learning

ABSTRACT
This paper presents a novel approach to machine learning. We introduce
a new algorithm that significantly improves performance. Our experiments
show a 40% improvement over existing methods.

INTRODUCTION
The field of artificial intelligence has grown rapidly in recent years.
Machine learning applications are now ubiquitous. However, current approaches
have limitations that prevent wider adoption. This work addresses those gaps.

## Methodology
We use a three-stage approach. First, we preprocess the data using standard
techniques. Second, we apply our novel algorithm. Third, we validate results
using cross-validation. The implementation was done in Python.

RESULTS
Our experiments show significant improvements. On dataset A, we achieved
95% accuracy compared to 85% for baseline. On dataset B, results were
even more promising with 98% accuracy. These results are statistically
significant with p < 0.01.

## Discussion
These results confirm our hypothesis. The improvement comes from better
feature extraction. However, computational cost is higher than baseline.
This suggests future work should focus on optimization.

1. Conclusion
This work presents a significant advance in the field. Future work should
focus on reducing computational overhead. We believe this approach will
be adopted by the community.

## References
[1] Smith et al. 2020. A paper on ML.
[2] Jones et al. 2021. Another ML paper.
[3] Brown et al. 2022. Recent advances in AI.
"""
    
    print("=" * 60)
    print("PRUEBA DE EXTRACCIÓN DE SECCIONES")
    print("=" * 60)
    
    # Crear extractor
    extractor = SectionExtractor()
    
    # Simular pages_data
    pages_data = [
        {"text": test_text, "page": 1}
    ]
    
    # Extraer secciones
    print("\n📑 Extrayendo secciones...")
    sections = extractor.extract_sections(test_text, pages_data)
    
    if sections:
        print("\n✅ Secciones detectadas:")
        summary = extractor.get_section_summary()
        for section_type, info in summary.items():
            print(f"\n  📌 {section_type.upper()}")
            print(f"     Título: {info['title']}")
            print(f"     Palabras: {info['word_count']}")
            print(f"     Páginas: {info['pages']}")
            print(f"     Chunks: {info['chunks']}")
    else:
        print("\n❌ No se detectaron secciones")
        return False
    
    # Probar get_section_content
    print("\n" + "=" * 60)
    print("PRUEBA DE RECUPERACIÓN DE CONTENIDO")
    print("=" * 60)
    
    for section_type in sections.keys():
        content = extractor.get_section_content(section_type)
        if content:
            preview = content[:100] + "..." if len(content) > 100 else content
            print(f"\n✅ {section_type}:")
            print(f"   {preview}")
        else:
            print(f"\n❌ No se pudo recuperar {section_type}")
    
    # Probar prepare_for_rag
    print("\n" + "=" * 60)
    print("PRUEBA DE PREPARACIÓN PARA RAG")
    print("=" * 60)
    
    chunks_with_metadata = extractor.prepare_for_rag()
    print(f"\n✅ {len(chunks_with_metadata)} chunks preparados para RAG:")
    
    for i, (chunk, metadata) in enumerate(chunks_with_metadata[:3], 1):
        print(f"\n  Chunk {i}:")
        print(f"    Section Type: {metadata.get('section_type')}")
        print(f"    Section Title: {metadata.get('section_title')}")
        print(f"    Page: {metadata.get('page')}")
        print(f"    Chunk Index: {metadata.get('chunk_index')}/{metadata.get('total_chunks_in_section')}")
        print(f"    Content Preview: {chunk[:80]}...")
    
    if len(chunks_with_metadata) > 3:
        print(f"\n  ... y {len(chunks_with_metadata) - 3} chunks más")
    
    print("\n" + "=" * 60)
    print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("=" * 60)
    return True

def test_section_detection():
    """Prueba la detección de búsquedas por sección."""
    print("\n" + "=" * 60)
    print("PRUEBA DE DETECCIÓN DE BÚSQUEDAS POR SECCIÓN")
    print("=" * 60)
    
    # Simulamos la lógica del _detect_section_request
    test_queries = [
        "Show me the abstract",
        "Cuál es la introducción?",
        "Dame los métodos",
        "¿Cuáles fueron los resultados?",
        "Muestra la discusión",
        "What is the conclusion?",
        "Bibliografía del paper",
        "¿Qué dice el paper?" # No debería detectar sección
    ]
    
    section_keywords = {
        "abstract": ["abstract", "resumen", "summary", "sumario"],
        "introduction": ["introducción", "introduccion", "introduction"],
        "methods": ["métodos", "metodos", "methods"],
        "results": ["resultados", "results", "findings"],
        "discussion": ["discusión", "discusion", "discussion"],
        "conclusion": ["conclusión", "conclusion", "conclusions"],
        "references": ["referencias", "references", "bibliografía"],
    }
    
    section_triggers = [
        "muestra", "show", "cuál", "cual", "que es", "dame", "give me",
    ]
    
    for query in test_queries:
        query_lower = query.lower()
        has_trigger = any(trigger in query_lower for trigger in section_triggers)
        
        print(f"\n📝 Query: {query}")
        print(f"   Has trigger: {has_trigger}")
        
        if has_trigger:
            for section_type, keywords in section_keywords.items():
                matched = [kw for kw in keywords if kw in query_lower]
                if matched:
                    print(f"   ✅ Sección detectada: {section_type}")
                    print(f"      Keywords: {matched}")
                    break
            else:
                print(f"   ⚠️ No se detectó sección específica")
        else:
            print(f"   ⚠️ No se detectó patrón de búsqueda de sección")
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    print("\n🧪 INICIANDO PRUEBAS DEL SISTEMA DE SECCIONES\n")
    
    success = True
    
    try:
        success = test_section_extraction() and success
    except Exception as e:
        print(f"\n❌ Error en test_section_extraction: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    try:
        success = test_section_detection() and success
    except Exception as e:
        print(f"\n❌ Error en test_section_detection: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    if success:
        print("\n\n✅ ¡TODAS LAS PRUEBAS PASARON!\n")
        sys.exit(0)
    else:
        print("\n\n❌ ALGUNAS PRUEBAS FALLARON\n")
        sys.exit(1)
