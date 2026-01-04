# 📚 RAG Chatbot v2 - Guía de Uso (Fullstack)

Un sistema RAG (Retrieval-Augmented Generation) avanzado que combina un Backend potente (FastAPI) con un Frontend moderno (React), permitiendo chat con voz y texto usando modelos Locales o Gemini.

## 🚀 Instalación Rápida

### Backend (Python)
```bash
pip install -r requirements.txt
```

### Frontend (React)
```bash
cd frontend
npm install
```

## 📁 Estructura del Proyecto

```
chatbot2/
├── backend/             # 🧠 Lógica del servidor
│   ├── main.py          # API FastAPI
│   ├── chatbot_rag.py   # Motor del Chatbot
│   └── rag_system.py    # Sistema RAG (ChromaDB)
├── frontend/            # 🎨 Interfaz de Usuario
│   └── src/components/  # Componentes React
├── pdfs/               # 📄 Carpeta para tus PDFs
├── requirements.txt    # Dependencias Python
├── SETUP.md            # Guía detallada de instalación
└── .env                # Variables de entorno (API Keys)
```

## 💻 Uso del Chatbot

A diferencia de la versión anterior de script único, este sistema corre un servidor y una interfaz web.

### Paso 1: Iniciar Backend
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Paso 2: Iniciar Frontend
```bash
# En otra terminal
cd frontend
npm run dev
```
Abre `http://localhost:5173` en tu navegador.

## 🎮 Interfaz y Comandos

Ya no necesitas comandos de terminal. La interfaz web te permite:

| Acción | Descripción |
|--------|-------------|
| **🎤 Micrófono** | **NUEVO**: Haz clic para grabar. Al parar, se transcribe tu voz automáticamente con Gemini 2.5 Flash y se envía. |
| **📎 Clip** | Sube PDFs directamente desde el navegador. |
| **💬 Chat** | Escribe o habla. El modelo responderá usando tus documentos. |
| **🔄 Local/Gemini** | El sistema elige automáticamente o puedes configurar el proveedor en el backend. |

## 📄 Preparar tus PDFs

Tienes dos opciones:

1.  **Subida Web**: Usa el botón de clip en el chat.
2.  **Carpeta Manual**:
    *   Crea una carpeta `pdfs` en la raíz (si no existe).
    *   Coloca tus archivos ahí.
    *   El sistema los indexará al iniciarse o al pedírselo.

## 🔧 Configuración Avanzada

### Variables de Entorno (.env)
Crea un archivo `.env` en la raíz:
```env
GEMINI_API_KEY=tu_clave_de_google_aistudio
```

### Configuración del RAG (config.json)
Si existe `config.json`, puedes ajustar:
```json
{
  "rag": {
    "chunk_size": 500,
    "chunk_overlap": 100,
    "embeddings_model": "all-MiniLM-L6-v2"
  }
}
```

## 📊 Cómo Funciona el RAG Actual

```
[Voz del Usuario] → [Transcribir con Gemini] → [Texto]
                                                  ↓
                                          [Buscar en ChromaDB]
                                                  ↓
[Gemini/Local LLM] ← [Contexto PDF] + [Pregunta]
        ↓
[Respuesta al Frontend]
```

## 🛠️ Troubleshooting

### Error: "Error 500 en Transcripción"
- Verifica que tienes la `GEMINI_API_KEY` en tu archivo `.env`.
- Revisa que tu conexión a internet funcione (para llamar a Gemini).

### El frontend no conecta
- Asegúrate de que el backend está corriendo en el puerto 8000.
- Revisa la consola del navegador (F12) para ver errores de red.

### Permisos de Micrófono
- El navegador te pedirá permiso la primera vez. Si lo deniegas, no podrás usar el dictado.

## 📚 Características Nuevas

✅ **Dictado por Voz Full**: Transcripción servidor-servidor de alta calidad.
✅ **Interfaz React**: Mucho más rápida y amigable que la terminal.
✅ **Gestión de Archivos**: Sube y borra PDFs desde la UI.
✅ **Doble Motor**: Cambia entre Gemini (Nube) y Local (LMStudio) fácilmente.

## 🚀 Próximos Pasos

1.  **Mejorar UI**: Agregar temas oscuro/claro.
2.  **Historial Persistente**: Guardar chats en base de datos.
3.  **Más Modelos**: Soportar OpenAI o Anthropic.

---

¿Dudas? Revisa `SETUP.md` para una instalación paso a paso desde cero.
