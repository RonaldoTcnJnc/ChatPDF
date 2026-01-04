from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import shutil
import os
import tempfile
import pathlib
import google.generativeai as genai
from chatbot_rag import ChatbotRAG

# Modelos Pydantic (coincidentes con frontend/src/types.ts)
class ChatRequest(BaseModel):
    message: str
    pdf_name: Optional[str] = None
    use_rag: bool

class TranscribeResponse(BaseModel):
    text: str

class ChatResponse(BaseModel):
    response: str
    sender: str

class Stats(BaseModel):
    total_chunks: int
    embedding_model: str
    database_path: str
    pdfs: Optional[List[str]] = []

class UploadResponse(BaseModel):
    filename: str
    status: str
    chunks: int

class SystemStatus(BaseModel):
    status: str
    provider: str
    model: str

# Configuración
app = FastAPI(title="Chatbot RAG API")

from fastapi.staticfiles import StaticFiles

# Habilitar CORS para el frontend (Vite corre en puerto 5173 normalmente)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringir a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos para imágenes
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Directorios
UPLOAD_DIR = "./pdfs"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Instancia global del chatbot
chatbot = ChatbotRAG()

class ProviderRequest(BaseModel):
    provider: str

# Endpoints
@app.get("/api/", response_model=SystemStatus)
async def get_status():
    """Devuelve el estado del sistema y configuración actual."""
    return SystemStatus(
        status="online",
        provider=chatbot.provider,
        model=chatbot.model_name
    )

@app.post("/api/provider")
async def set_provider(request: ProviderRequest):
    """Cambia el proveedor del modelo (gemini o local)."""
    if chatbot.set_provider(request.provider):
        return {"status": "success", "provider": chatbot.provider, "model": chatbot.model_name}
    else:
        raise HTTPException(status_code=400, detail="Proveedor inválido")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Procesa un mensaje de chat con o sin RAG."""
    try:
        response_text = chatbot.get_response(
            user_message=request.message,
            use_rag=request.use_rag,
            pdf_name=request.pdf_name
        )
        
        return ChatResponse(
            response=response_text,
            sender="assistant"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Sube y procesa un archivo PDF."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Procesar con RAG
        chatbot.load_single_pdf(file_path)
        
        # Obtener estadísticas breves (hack para sacar # chunks)
        # Idealmente chatbot.rag.add_pdf devolvería el número de chunks
        stats = chatbot.rag.get_stats()
        
        return UploadResponse(
            filename=file.filename,
            status="success",
            chunks=stats.get("total_chunks", 0) # Esto es el total global, pero sirve por ahora
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio usando Gemini 1.5 Flash."""
    
    # Validar que sea audio (opcional, pero recomendado)
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="El archivo no es un audio válido.")

    try:
        # 1. Guardar archivo temporal de forma segura para Windows
        # Usamos mkstemp para evitar bloqueos de archivo
        suffix = ".webm"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        
        try:
            # Escribir contenido usando el file descriptor
            with os.fdopen(fd, 'wb') as tmp:
                shutil.copyfileobj(file.file, tmp)
            # El archivo se cierra automáticamente al salir del with
            
            # 2. Configurar Gemini
            api_key = os.getenv("GEMINI_API_KEY") 
            if not api_key:
                 api_key = chatbot.config.get("gemini", {}).get("api_key")
            
            if not api_key:
                 raise HTTPException(status_code=500, detail="API Key de Gemini no encontrada")

            genai.configure(api_key=api_key)

            # 3. Subir archivo a Gemini
            print(f"📤 Subiendo audio a Gemini: {tmp_path}")
            # Ahora es seguro abrirlo porque lo cerramos arriba
            uploaded_file = genai.upload_file(tmp_path, mime_type=file.content_type or "audio/webm")
            
            # 4. Generar contenido
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            print("🎧 Solicitando transcripción...")
            response = model.generate_content(
                [uploaded_file, "Transcribe exactamente lo que se dice en este audio al español. No añadas explicaciones, solo el texto transcrito."],
            )
            
            # Borrar de la nube
            try:
                 uploaded_file.delete()
            except:
                 pass 
                 
            print(f"✅ Transcripción exitosa: {response.text[:50]}...")
            return TranscribeResponse(text=response.text.strip())

        finally:
            # 5. Limpieza local siempre
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as e:
                    print(f"⚠️ No se pudo borrar archivo temporal: {e}")

    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        # Retornar el error detallado para ver en frontend
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Elimina un archivo PDF y todos sus datos asociados."""
    try:
        if chatbot.delete_pdf(filename):
            return {"status": "success", "message": f"Archivo {filename} eliminado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar el archivo")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Devuelve estadísticas de la base de datos RAG."""
    try:
        stats_data = chatbot.rag.get_stats()
        return Stats(
            total_chunks=stats_data.get("total_chunks", 0),
            embedding_model=stats_data.get("embedding_model", "unknown"),
            database_path=stats_data.get("database_path", "./chroma_db"),
            pdfs=stats_data.get("pdfs", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor Backend en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
