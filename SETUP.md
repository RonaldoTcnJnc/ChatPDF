# � Sistema RAG Chatbot con Soporte de Voz (Gemini & Local)

Este proyecto es un chatbot avanzado que te permite:
1.  **Chatear con tus PDFs** (RAG: Retrieval Augmented Generation).
2.  **Hablarle por voz** y recibir transcripciones automáticas en español.
3.  **Usar Modelos Potentes**: Gemini 1.5/2.5 Flash (Google) o modelos Locales (LMStudio).

---

## 📋 Requisitos Previos

Antes de empezar, necesitas instalar:

1.  **Python 3.10+**: [Descargar aquí](https://www.python.org/downloads/)
    *   *Importante*: Marca la casilla "Add Python to PATH" al instalar.
2.  **Node.js (para el Frontend)**: [Descargar versión LTS](https://nodejs.org/)

---

## 🛠️ Instalación desde Cero

Sigue estos pasos para instalar todo lo necesario.

### 1. Clonar o Descargar el Proyecto
Si tienes git:
```bash
git clone <tu-repositorio>
cd chatbot2
```
O simplemente descarga y descomprime el ZIP.

### 2. Configurar el Backend (Python)

Abre una terminal en la carpeta principal `chatbot2`:

```bash
# Opcional: Crear entorno virtual (recomendado)
python -m venv venv
# Activar en Windows:
venv\Scripts\activate
# Activar en Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar el Frontend (React)

En la misma terminal (o una nueva), ve a la carpeta `frontend`:

```bash
cd frontend
npm install
```

### 4. Configurar Variables de Entorno (.env)

Crea un archivo llamado `.env` en la carpeta principal `chatbot2` y pega tu clave de API de Gemini:

```env
GEMINI_API_KEY=tu_clave_aqui_consiguela_en_aistudio.google.com
```

---

## ▶️ Cómo Ejecutarlo

Necesitarás **dos terminales** abiertas:

### Terminal 1: Backend
```bash
# Desde la carpeta chatbot2
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
*Verás un mensaje: "Application startup complete".*

### Terminal 2: Frontend
```bash
# Desde la carpeta chatbot2/frontend
npm run dev
```
*Abre el link que aparece (usualmente `http://localhost:5173`) en tu navegador.*

---

## �️ Cómo Usar el Dictado por Voz
1. Haz clic en el icono del **Micrófono** en el chat.
2. Habla tu pregunta.
3. Haz clic de nuevo para enviar.
4. El audio se transcribirá automáticamente usando Gemini y se enviará.

---
## � Solución de Problemas Comunes

- **Error en `pip install`**: Asegúrate de tener instalado "C++ Build Tools" si Windows se queja al compilar `chromadb`.
- **Error 500 en Transcripción**: Verifica que `GEMINI_API_KEY` sea correcta en `.env`.
- **No graba audio**: Dale permiso al navegador para acceder a tu micrófono.

¡Disfruta tu Chatbot! 🤖
