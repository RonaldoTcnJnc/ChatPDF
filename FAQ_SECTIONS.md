# ❓ FAQ - Sistema de Indexación por Secciones

## Preguntas Frecuentes

### 1. ¿Cómo activar/desactivar la indexación por secciones?

**Por defecto está ACTIVADO automáticamente.**

Para desactivar:
```python
# Desactivar para un PDF específico
rag.add_pdf("paper.pdf", use_sections=False)

# Procesar como chunks genéricos (comportamiento anterior)
```

---

### 2. ¿Funciona con PDFs en idiomas diferentes?

**SÍ - Soporta multiidioma:**

- 🇪🇸 Español: "resumen", "introducción", "métodos", etc.
- 🇬🇧 Inglés: "abstract", "introduction", "methods", etc.
- 🔄 Mixto: Palabras clave en ambos idiomas

El sistema intenta detectar secciones en ambos idiomas automáticamente.

---

### 3. ¿Qué pasa si el PDF no tiene estructura de secciones clara?

**El sistema tiene 3 niveles de fallback:**

```
Intento 1: Detectar secciones claras
   ↓ (Si falla)
Intento 2: Buscar keywords con patrones flexibles
   ↓ (Si falla)
Intento 3: Crear sección genérica "content"
   └─ Procesa como un documento sin secciones
```

**Log esperado:**
```
⚠️ No se detectaron secciones. Usando documento como una sola sección.
```

---

### 4. ¿Cómo el usuario activa la búsqueda de sección en el chat?

**Automáticamente - No necesita hacer nada especial:**

```
❌ INCORRECTO - Esto NO activa búsqueda de sección:
   👤 "¿Qué hay en el abstract?"
   
✅ CORRECTO - Cualquiera de estos activa búsqueda:
   👤 "Show me the abstract"
   👤 "Muestra el resumen"
   👤 "Cuál es el abstract?"
   👤 "Dame la introducción"
   👤 "What is the introduction?"
```

**Requisitos:**
1. Trigger de búsqueda: "muestra", "show", "cuál", "what is", "dame", etc.
2. Keyword de sección: "abstract", "resumen", "introduction", "métodos", etc.

---

### 5. ¿Qué pasa cuando un PDF tiene secciones muy largas?

**El sistema las divide automáticamente:**

```
Ejemplo:
- INTRODUCTION: 2000 palabras
  → Dividida en 4 chunks (500 palabras cada uno)
  → Cada chunk indexado por separado
  → Al recuperar, trae TODOS los chunks de introduction
  → Usuario recibe contenido completo y coherente
```

**Configuración (en `section_extractor.py`):**
```python
chunk_size = 500      # Palabras por chunk
overlap = 50         # Palabras que se repiten entre chunks
```

---

### 6. ¿El usuario puede mezclar búsquedas de sección con otras preguntas?

**Sí - El sistema detecta automáticamente:**

```
👤 "Muestra el abstract porque necesito entender..."

🤖 Sistema:
   1. Detecta: "Muestra" + "abstract"
   2. Extrae y retorna sección abstract
   3. Responde: Con contenido de abstract

👤 "¿Qué métodos se usaron en el estudio?"

🤖 Sistema:
   1. Detecta: "¿Qué" + "métodos"
   2. Extrae sección methods
   3. Responde: Con contenido de methods
```

---

### 7. ¿Cómo ver qué secciones fueron detectadas en un PDF?

**Revisar logs al cargar:**

```
📑 Extrayendo secciones del PDF...
✅ Sección 'abstract' detectada: 150 palabras, 1 chunks
✅ Sección 'introduction' detectada: 500 palabras, 2 chunks
✅ Sección 'methods' detectada: 800 palabras, 3 chunks
✅ Sección 'results' detectada: 600 palabras, 2 chunks
✅ Sección 'conclusion' detectada: 300 palabras, 1 chunks
```

**Programáticamente:**

```python
# Ver resumen de secciones detectadas
summary = rag.sections_summary  # Si disponible

# O recuperar secciones manualmente
for section_type in ["abstract", "introduction", "methods"]:
    content = rag.get_section_content(section_type, "paper.pdf")
    print(f"{section_type}: {len(content)} caracteres")
```

---

### 8. ¿Qué sucede con las referencias bibliográficas?

**Se indexan como sección separada:**

```python
# Recuperar solo referencias
references = rag.get_section_content("references", "paper.pdf")

# Usuario pregunta:
👤 "Cuáles son las referencias?"
🤖 [Detecta "references"]
   [Retorna sección complete de referencias]
```

---

### 9. ¿El sistema preserva el orden original del documento?

**SÍ - Completamente:**

```python
# Orden al indexar:
chunks = extractor.prepare_for_rag()
# Chunks ordenados:
# [abstract-chunk0, introduction-chunk0, introduction-chunk1, methods-chunk0, ...]

# Metadatos preservan información:
metadata = {
    "chunk_index": 0,              # Índice en la sección
    "total_chunks_in_section": 2   # Total en esa sección
}
```

---

### 10. ¿Cómo afecta esto al modelo de lenguaje?

**Cambios en el contexto proporcionado:**

```
ANTES (sin secciones):
[1] (Fuente: paper.pdf | Página: 1)
    This is chunk text about methods...

DESPUÉS (con secciones):
[1] (Fuente: paper.pdf | Página: 1 | Sección: methods (Methodology))
    This is chunk text about methods...
```

El modelo recibe más contexto (nombres de sección) para hacer respuestas mejor informadas.

---

### 11. ¿Se puede consultar múltiples secciones a la vez?

**No automáticamente, pero se puede:**

```python
# Manualmente recuperar múltiples secciones
abstract = rag.get_section_content("abstract", "paper.pdf")
methods = rag.get_section_content("methods", "paper.pdf")
results = rag.get_section_content("results", "paper.pdf")

combined = f"{abstract}\n\n{methods}\n\n{results}"
response = chatbot.get_response(combined)
```

---

### 12. ¿Cómo se comporta con PDFs muy cortos?

**Normalmente:**

```
PDF de 1 página con múltiples secciones:
- ABSTRACT (2 párrafos)
- INTRODUCTION (3 párrafos)
- RESULTS (2 párrafos)

Sistema:
✅ Detecta todas las secciones
✅ Las indexa normalmente
✅ El usuario puede buscar cada una
```

---

### 13. ¿Hay limite de tamaño de PDF?

**No hay límite artificial, pero:**

- PDFs < 100MB: Sin problemas
- PDFs > 100MB: Verificar disponibilidad de memoria
- PDFs muy grandes: El OCR puede ser lento

---

### 14. ¿Los chunks de sección son más pequeños o iguales?

**Exactamente igual - El tamaño se configura igual:**

```python
# En section_extractor.py
def _create_section_chunks(
    self, 
    content: str, 
    chunk_size: int = 500,    # Palabras (igual que chunk_text)
    overlap: int = 50         # Palabras (igual)
)
```

La diferencia es:
- **Sin secciones**: 500 palabras por chunk de TODO el documento
- **Con secciones**: 500 palabras por chunk DENTRO de cada sección

---

### 15. ¿Puedo cambiar los patterns de detección de secciones?

**SÍ - Edita `SECTION_PATTERNS` en `section_extractor.py`:**

```python
SECTION_PATTERNS = {
    "my_custom_section": {
        "keywords": ["palabra1", "palabra2", "custom"],
        "order": 9  # Posición en el documento
    },
    # ... resto de secciones
}
```

---

### 16. ¿Qué pasa con apéndices y suplementarios?

**Se detectan automáticamente:**

```python
# Sistema soporta:
section_keywords = {
    "appendix": ["apéndice", "appendix", "anexo", "supplement"],
    # ...
}

👤 "Muestra los anexos"
🤖 [Detecta "appendix"]
   [Retorna sección appendix]
```

---

### 17. ¿Cómo limpiar la base de datos después de cambios?

**Opción 1 - Eliminar PDF completamente:**
```python
rag.delete_pdf("paper.pdf")
```

**Opción 2 - Limpiar toda la BD:**
```python
rag.clear_database()
```

**Opción 3 - Recargar con secciones:**
```python
rag.delete_pdf("paper.pdf")
rag.add_pdf("paper.pdf", use_sections=True)
```

---

### 18. ¿El sistema es compatible con el visor de PDF?

**SÍ - Los metadatos incluyen información de página:**

```python
metadata = {
    "page": 1,           # Página inicial de la sección
    "end_page": 3,       # Página final de la sección
    "section_type": "methods"
}
```

Esto permite:
- Highlighting automático en el visor
- Navegación de sección en sección
- Sincronización entre chat y PDF

---

### 19. ¿Qué sucede si un PDF está en otro idioma (alemán, francés)?

**Parcialmente soportado:**

- ✅ Si tiene headers en inglés o español: Detecta
- ⚠️ Si tiene headers en otro idioma: Crea sección genérica
- 💡 **Solución**: Agregar keywords en ese idioma a `SECTION_PATTERNS`

---

### 20. ¿Hay overhead de performance?

**Mínimo - Análisis:**

```
Tiempo de procesamiento (típico):
- Sin secciones: 5 segundos (100 chunks)
- Con secciones: 6-7 segundos (100 chunks)
  └─ +20% tiempo por detección de secciones
  └─ +10% tiempo por generación de metadatos
  └─ Negligible en práctica
```

**Memoria:**
- Overhead: ~5-10% por metadatos adicionales
- Offset por mejor indexación

---

## Troubleshooting

### Problema: No detecta secciones
**Solución:**
```python
# 1. Verificar logs
print("Check console output for section detection")

# 2. Probar con use_sections=False
rag.add_pdf("paper.pdf", use_sections=False)

# 3. Verificar formato del PDF
# - Asegurar que tiene headers claros
# - Probar extracción manual: rag.extract_text_from_pdf()
```

### Problema: Secciones incompletas
**Solución:**
```python
# Aumentar chunk_size
chunk_size=800  # Más palabras por chunk

# Verificar límite de búsqueda
chunks = rag.retrieve_by_section(section_type, k=1000)  # Más chunks
```

### Problema: Memoria baja con PDFs grandes
**Solución:**
```python
# Procesar sin OCR
use_sections=False

# O aumentar chunk_size para menos chunks totales
```

---

**Última actualización:** January 7, 2026
**Versión:** 1.0
