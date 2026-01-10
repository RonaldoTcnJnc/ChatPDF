# 📚 RAG Chatbot - Guía de Uso

Un sistema RAG (Retrieval-Augmented Generation) local que mejora tu chatbot Llama 3 con información de PDFs.

## 🚀 Instalación Rápida

```bash
pip install -r requirements.txt
```
# Artículo Académico

Sistema ChatBot RAG con Voz para Procesamiento
Inteligente de Documentos Científico

[](Procesamiento_Inteligente_de_Documentos_Científicos_mediante_Modelos_de_Lenguaje_y_Aprendizaje.pdf)



## 📁 Estructura del Proyecto

```
chatbot2/
├── a.py                 # Script original (puedes reemplazarlo)
├── chatbot_rag.py       # ✨ Chatbot mejorado con RAG
├── rag_system.py        # 🧠 Sistema RAG principal
├── requirements.txt     # Dependencias
├── README.md            # Este archivo
├── pdfs/               # 📄 Carpeta para tus PDFs (crear manualmente)
└── chroma_db/          # Base de datos de embeddings (se crea automáticamente)
```

## 💻 Uso del Chatbot

### Método 1: Chat Interactivo Simple

```bash
python chatbot_rag.py
```

Esto iniciará un chat interactivo donde:
- Los PDFs se cargarán automáticamente desde la carpeta `./pdfs/`
- Cada pregunta buscará información relevante en los documentos
- El modelo usará el contexto para generar respuestas más precisas

### Método 2: Uso Programático

```python
from chatbot_rag import ChatbotRAG

# Inicializar
chatbot = ChatbotRAG(
    base_url="http://localhost:1234/v1",
    model_name="lmstudio-community/Meta-Llama-3-8B-Instruct",
    rag_db_path="./chroma_db"
)

# Cargar PDFs
chatbot.load_pdfs("./pdfs")

# O cargar un PDF específico
chatbot.load_single_pdf("./papers/research_paper.pdf")

# Obtener respuesta
response = chatbot.get_response("¿Cuál es el tema principal del paper?")
print(response)

# Ver estadísticas
chatbot.show_stats()
```

## 🎮 Comandos del Chat Interactivo

Dentro del chat, puedes usar estos comandos:

| Comando | Descripción |
|---------|-------------|
| `salir`, `exit`, `quit` | Termina el chat |
| `limpiar` | Limpia el historial de conversación |
| `stats` | Muestra estadísticas del sistema |
| `cargar /ruta/pdf` | Carga un PDF específico |
| `cargar /ruta/carpeta` | Carga todos los PDFs de una carpeta |

## 📄 Preparar tus PDFs

1. Crea una carpeta `pdfs` en el directorio del proyecto:
   ```bash
   mkdir pdfs
   ```

2. Coloca tus PDFs de investigación o papers en esa carpeta:
   ```
   pdfs/
   ├── paper1.pdf
   ├── paper2.pdf
   ├── research.pdf
   └── ...
   ```

3. Inicia el chatbot - los PDFs se cargarán automáticamente

## 🔧 Configuración Avanzada

### Personalizar el Tamaño de Chunks

En `rag_system.py`, modifica el método `chunk_text()`:

```python
def chunk_text(self, text, chunk_size=500, overlap=100):
    # chunk_size: número de palabras por chunk (aumentar = contexto más largo)
    # overlap: palabras que se repiten entre chunks (mejor continuidad)
```

### Cambiar el Modelo de Embeddings

En `chatbot_rag.py`:

```python
chatbot = ChatbotRAG(
    rag_db_path="./chroma_db"
    # Modelos disponibles:
    # - "all-MiniLM-L6-v2" (por defecto, rápido)
    # - "all-mpnet-base-v2" (más preciso, más lento)
    # - "multilingual-e5-base" (multiidioma)
)
```

### Número de Documentos a Recuperar

En el método `get_response()`:

```python
response = chatbot.get_response(
    user_message,
    use_rag=True,
    k=5  # Cambiar a 5, 10, etc. para más contexto
)
```

## 📊 Cómo Funciona el RAG

```
[Pregunta del Usuario]
        ↓
[Generar Embedding]
        ↓
[Buscar en ChromaDB] ← Recupera chunks similares
        ↓
[Preparar Contexto] ← Información relevante
        ↓
[Enviar al Modelo] → [Llama 3 Genera Respuesta]
        ↓
[Respuesta Mejorada]
```

## 🛠️ Troubleshooting

### Error: "No hay información en la base de datos"
- Verifica que los PDFs estén en la carpeta `pdfs/`
- Usa el comando `stats` para ver cuántos chunks se han cargado
- Carga manualmente con: `cargar ./pdfs`

### El modelo no responde
- Asegúrate de que LMStudio esté corriendo en `localhost:1234`
- Prueba con el script original `a.py` primero
- Verifica que el modelo está cargado en LMStudio

### Los embeddings son lentos
- El modelo `all-MiniLM-L6-v2` es el más rápido
- Reduce el tamaño de los PDFs
- Aumenta `chunk_size` en el método `chunk_text()`

## 📚 Características

✅ Extracción automática de PDFs con PyMuPDF  
✅ Embeddings locales con Sentence Transformers  
✅ Base de datos vectorial con ChromaDB  
✅ Recuperación rápida y precisa de información  
✅ Historial de conversación  
✅ Modelos locales (sin API externa)  
✅ Interfaz interactiva amigable  

## 🚀 Próximos Pasos

1. **Mejorar contexto**: Ajusta `chunk_size` y `overlap`
2. **Más precisión**: Cambia el modelo de embeddings
3. **Base de datos persistente**: Usa ChromaDB para guardar embeddings
4. **Interfaz web**: Agrega una UI con Gradio o Streamlit
5. **Búsqueda semántica**: Experimenta con diferentes `k` values

## 📝 Notas

- Los PDFs se procesan una sola vez y se guardan en `chroma_db/`
- Los embeddings son ligeros (~26MB para el modelo por defecto)
- Recomendado para papers, papers de investigación, documentos técnicos
- Funciona completamente offline (después de cargar los modelos)

---

¿Preguntas? Consulta la documentación de ChromaDB y Sentence Transformers para más opciones.
