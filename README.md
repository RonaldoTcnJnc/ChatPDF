# 🤖 ChatBot RAG con Voz (Local & Gemini)

Un sistema avanzado de **Chat con PDFs** que combina la privacidad de modelos locales (vía LMStudio) con la potencia de la nube (Gemini 1.5/2.5 Flash), todo controlado por voz.

---

## 1. ¿Qué es este proyecto?

Este es un **Asistente de Inteligencia Artificial Fullstack** diseñado para permitirte "chatear" con tus propios documentos PDF. A diferencia de ChatGPT estándar, este sistema tiene acceso directo a tus archivos privados dentro de tu ordenador.

**Características Únicas:**
- **🎙️ Dictado por Voz Real**: Habla naturalmente en español. El sistema transcribe tu voz usando modelos de Google (Gemini) para una precisión perfecta.
- **🧠 Doble Motor de IA**: Elige entre **Gemini 2.5 Flash** (rápido/nube) o **Modelos Locales** (privacidad total/offline vía LMStudio).
- **📄 RAG (Retrieval-Augmented Generation)**: Tus PDFs se procesan y buscan semánticamente para dar respuestas basas en HECHOS, no alucinaciones.

---

## 2. ¿Cómo funciona?

El sistema sigue un flujo de datos moderno:

1.  **Ingesta**: Subes un PDF (vía Web o Carpeta). El backend lo lee y divide en "chunks" (fragmentos).
2.  **Vectorización**: `Sentence-Transformers` convierte el texto en vectores numéricos.
3.  **Almacenamiento**: Se guardan en `ChromaDB`, una base de datos vectorial local.
4.  **Búsqueda**: Cuando preguntas, el sistema busca los chunks más relevantes.
5.  **Generación**: Envía `Tu Pregunta + Contexto Encontrado` a la IA (Gemini/Llama) para generar la respuesta.

**Arquitectura Técnica:**
- **Frontend**: React + Vite + TypeScript (Interfaz moderna y rápida).
- **Backend**: FastAPI + Python (API robusta y gestión de IA).
- **IA/LLM**: Google Generative AI SDK + OpenAI Client (para LMStudio).

---

## 3. Instalación y Ejecución

Para una guía paso a paso desde cero, ver [SETUP.md](./SETUP.md).

### Paso A: Backend (Python)
```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar API Key (crear archivo .env)
echo "GEMINI_API_KEY=tu_clave_aqui" > .env

# Iniciar Servidor
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso B: Frontend (React)
```bash
cd frontend
# Instalar dependencias node
npm install
# Iniciar Interfaz
npm run dev
```
🔗 Abrir: `http://localhost:5173`

---

## 4. Estructura del Proyecto

```
chatbot2/
├── backend/             # 🧠 Lógica del servidor
│   ├── main.py          # API FastAPI (Endpoints)
│   ├── chatbot_rag.py   # Orquestador del Chatbot
│   └── rag_system.py    # Motor RAG (ChromaDB)
├── frontend/            # 🎨 Interfaz Web
│   └── src/
│       └── components/  # ChatInterface, etc.
├── pdfs/               # 📄 Carpeta de almacenamiento de PDFs
├── chroma_db/          # 💾 Base de datos vectorial (Persistente)
├── requirements.txt    # Librerías Python
└── README.md           # Documentación
```

---

## 5. Configuración Avanzada

Puedes ajustar el comportamiento del RAG editando `config.json` (se crea tras el primer uso) o directamente en el código:

### Parámetros de RAG (`config.json`)
```json
{
  "rag": {
    "chunk_size": 500,       // Palabras por fragmento (más alto = más contexto, más lento)
    "chunk_overlap": 100,    // Palabras repetidas entre fragmentos para continuidad
    "embeddings_model": "all-MiniLM-L6-v2", // Modelo ligero y rápido
    "db_path": "./chroma_db"
  }
}
```

### Configuración de Modelos
- **Gemini**: Se configura en `.env`. Modelo por defecto: `gemini-2.5-flash`.
- **Local (LMStudio)**: Por defecto busca en `http://localhost:1234/v1`. Puedes cambiar esto en `chatbot_rag.py` o `config.json`.

---

## 6. Solución de Problemas (Troubleshooting)

### ❌ Error 500 al Transcribir Audio
- **Causa**: Falta la API Key o bloqueo de archivos temporales.
- **Solución**: 
  1. Verifica que `.env` tenga `GEMINI_API_KEY`.
  2. Reinicia el backend si acabas de crear el `.env`.

### ❌ "No hay información en la base de datos"
- **Causa**: No has subido PDFs o la carpeta `pdfs/` está vacía.
- **Solución**: Usa el botón de **Clip 📎** en el chat para subir un documento, o copia archivos manualmente a la carpeta `pdfs/` y reinicia.

### ❌ El Frontend no conecta (Network Error)
- **Causa**: El backend no está corriendo o el puerto 8000 está ocupado.
- **Solución**: Asegúrate de ver el mensaje "Application startup complete" en la terminal de Python.

---
*Proyecto Open Source - Combina lo mejor de la Nube y el Local.*
