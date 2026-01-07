# Guía de Indexación por Secciones - Sistema RAG Mejorado

## Resumen de Cambios

El sistema RAG ahora **divide automáticamente los PDFs en secciones** (Abstract, Introducción, Métodos, Resultados, Discusión, Conclusión, Referencias) en lugar de procesarlos como un único documento completo.

### ¿Qué mejora esto?

1. **Aislamiento de Secciones**: Cada sección se indexa por separado con metadatos específicos
2. **Búsqueda Inteligente**: El bot detecta automáticamente si buscas una sección específica
3. **Contexto Coherente**: Las respuestas mantienen coherencia dentro de su sección
4. **Búsqueda Directa**: Puedes pedir directamente una sección sin RAG

## Cómo Funciona

### 1. **Carga de PDFs (Automática)**

Cuando subes un PDF, el sistema:
- ✅ Extrae el texto completo
- ✅ Detecta secciones automáticamente (Abstract, Introduction, Methods, etc.)
- ✅ Divide cada sección en chunks más pequeños (si es muy grande)
- ✅ Indexa cada chunk con metadatos: `section_type`, `section_title`, `page`, etc.

### 2. **Ejemplo de Indexación**

```
PDF: "research_paper.pdf"
└─ Chunks indexados:
   ├─ Chunk 1
   │  ├── section_type: "abstract"
   │  ├── section_title: "Abstract"
   │  ├── page: 1
   │  └── content: "This paper studies..."
   │
   ├─ Chunk 2
   │  ├── section_type: "introduction"
   │  ├── section_title: "Introduction"
   │  ├── page: 2
   │  └── content: "The field of X is important..."
   │
   └─ Chunk N
      ├── section_type: "methods"
      ├── section_title: "Methodology"
      ├── page: 5
      └── content: "We used the following approach..."
```

### 3. **Detección Automática de Búsquedas por Sección**

El bot detecta automáticamente cuando pides una sección:

```
👤 "Show me the abstract"
🤖 [Detecta "abstract"] 
   [Recupera TODOS los chunks de la sección abstract]
   [Responde con el contenido completo de esa sección]

👤 "Cuál es la introducción del paper?"
🤖 [Detecta "introducción"] 
   [Recupera sección "introduction"]
   [Responde con contenido de introduction]

👤 "Cuáles fueron los métodos utilizados?"
🤖 [Detecta "métodos"]
   [Recupera sección "methods"]
   [Responde basado en esa sección]
```

### 4. **Palabras Clave Reconocidas**

**Para activar búsqueda de sección**, usa cualquiera de:

| Sección | Palabras Clave (ES) | Palabras Clave (EN) |
|---------|------------------|------------------|
| **Abstract** | resumen, sumario, resúmen | abstract, summary |
| **Introducción** | introducción, introduccion, antecedentes | introduction, intro |
| **Métodos** | métodos, metodología, método | methods, methodology |
| **Resultados** | resultados, hallazgos | results, findings |
| **Discusión** | discusión, análisis | discussion, analysis |
| **Conclusión** | conclusión, conclusiones | conclusion, conclusions |
| **Referencias** | referencias, bibliografía | references, bibliography |

**Frases de búsqueda:**
- "Muestra...", "Show...", "Cuál es...", "What is...", "Dame...", "Give me..."
- "¿Qué dice el...", "Tell me the...", "Obtén...", "Get the..."

## Ejemplos de Uso

### Búsqueda de Sección Específica
```
👤 "Muestra el abstract del paper"
🤖 Detecta: "abstract"
   Responde con el contenido completo de la sección abstract
```

### Búsqueda RAG Normal (Sin Sección Específica)
```
👤 "¿Cuáles son los puntos principales del paper?"
🤖 No detecta búsqueda de sección
   Usa búsqueda RAG normal
   Recupera los k chunks más relevantes
```

### Búsqueda Web
```
👤 "Busca papers sobre machine learning"
🤖 Detecta palabra clave "busca"
   Realiza búsqueda web en arXiv/Google
```

## Estructura de Metadatos

Cada chunk ahora contiene:

```python
{
    # Información de fuente
    "source": "research_paper.pdf",
    "pdf_path": "/path/to/research_paper.pdf",
    
    # Información de sección ✨ NUEVO
    "section_type": "abstract",           # Tipo de sección
    "section_title": "Abstract",          # Título original
    "chunk_index": 0,                     # Índice dentro de la sección
    "total_chunks_in_section": 2,         # Total de chunks en esta sección
    
    # Información de página
    "page": 1,                            # Página inicial
    "end_page": 1,                        # Página final
}
```

## API Nuevas del RAG System

### 1. Recuperar por Sección
```python
chunks = rag.retrieve_by_section(
    section_type="abstract",
    pdf_name="paper.pdf",  # Opcional
    k=10                   # Opcional: máximo chunks
)
```

### 2. Obtener Contenido Completo de Sección
```python
content = rag.get_section_content(
    section_type="methods",
    pdf_name="paper.pdf"  # Opcional
)
```

### 3. Procesar PDF con/sin Secciones
```python
# Con secciones (por defecto)
rag.add_pdf("paper.pdf", use_sections=True)

# Sin secciones (antiguo método)
rag.add_pdf("paper.pdf", use_sections=False)
```

## Cambios en el Contexto RAG

El contexto ahora incluye información de sección:

```
[1] (Fuente: research_paper.pdf | Página: 1 | Sección: abstract (Abstract))
This paper studies the effect of...

[2] (Fuente: research_paper.pdf | Página: 2 | Sección: introduction (Introduction))
The field of machine learning...
```

## Ventajas del Sistema

✅ **Mayor Coherencia**: Las respuestas del bot se mantienen en contexto de sección
✅ **Búsqueda Específica**: Puedes pedir "muestra la conclusión" y obtienes exactamente eso
✅ **Mejor Indexación**: El sistema entiende la estructura del documento
✅ **Metadatos Ricos**: Más información para filtrar y buscar

## Configuración

En `rag_system.py`:

```python
# Al procesar PDF, decide si usar secciones
pdf_collection = rag.add_pdf(
    pdf_path,
    use_sections=True   # Por defecto True
)
```

## Limitaciones y Casos de Uso

### Funciona Bien Para:
- 📄 Papers académicos con estructura clara
- 📊 Documentos técnicos con secciones estándar (Abstract, Methods, Results, etc.)
- 🔍 Cuando necesitas información de secciones específicas

### Casos Donde Puede Fallar:
- ❌ PDFs sin estructura clara
- ❌ PDFs escaneados (OCR) donde las secciones no están bien definidas
- ❌ Documentos con nombres de sección no estándar

### Fallback Automático:
Si no se detectan secciones, el sistema:
1. Crea una única sección "content" con todo el documento
2. Procesa normalmente con chunks genéricos
3. Log: `⚠️ No se detectaron secciones. Usando documento como una sola sección.`

## Depuración y Logs

Cuando cargas un PDF, verás logs como:

```
📑 Extrayendo secciones del PDF...
✅ Sección 'abstract' detectada: 150 palabras, 1 chunks
✅ Sección 'introduction' detectada: 500 palabras, 2 chunks
✅ Sección 'methods' detectada: 800 palabras, 3 chunks
✅ Sección 'results' detectada: 600 palabras, 2 chunks
✅ Sección 'conclusion' detectada: 300 palabras, 1 chunks
✅ PDF procesado con secciones: research_paper.pdf - 9 chunks agregados
```

## Próximas Mejoras

- [ ] Detección de sub-secciones (Results -> Experiment 1, Experiment 2, etc.)
- [ ] Visualización de estructura de secciones en el frontend
- [ ] Navegación por secciones en la interfaz de chat
- [ ] Marcadores de sección en el visor de PDF
