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
try:
    chatbot = ChatbotRAG()
except Exception as e:
    print(f"❌ ERROR CRÍTICO al inicializar ChatbotRAG: {e}")
    import traceback
    traceback.print_exc()
    chatbot = None

class ProviderRequest(BaseModel):
    provider: str

# Endpoints
@app.get("/api/", response_model=SystemStatus)
async def get_status():
    """Devuelve el estado del sistema y configuración actual."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
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
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    try:
        print(f"[CHAT] Mensaje recibido: {request.message[:50]}...")
        
        response_text = chatbot.get_response(
            user_message=request.message,
            use_rag=request.use_rag,
            pdf_name=request.pdf_name
        )
        
        print(f"✅ Respuesta generada ({len(str(response_text))} caracteres)")
        
        return ChatResponse(
            response=response_text,
            sender="assistant"
        )
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en /api/chat: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Sube y procesa un archivo PDF."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        print(f"📂 Guardando PDF: {file.filename}")
        # Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"🔄 Procesando con RAG...")
        # Procesar con RAG
        chatbot.load_single_pdf(file_path)
        
        # Obtener estadísticas breves
        stats = chatbot.rag.get_stats()
        chunks = stats.get("total_chunks", 0)
        
        print(f"✅ PDF procesado: {chunks} chunks")
        
        return UploadResponse(
            filename=file.filename,
            status="success",
            chunks=chunks
        )
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error al subir PDF: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio usando Gemini 2.5 Flash."""
    
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    # Validar que sea audio (opcional, pero recomendado)
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="El archivo no es un audio válido.")

    try:
        # 1. Guardar archivo temporal de forma segura para Windows
        # Usamos mkstemp para evitar bloqueos de archivo
        suffix = ".webm"
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        
        print(f"📤 Archivo temporal creado: {tmp_path}")
        
        try:
            # Escribir contenido usando el file descriptor
            with os.fdopen(fd, 'wb') as tmp:
                shutil.copyfileobj(file.file, tmp)
            # El archivo se cierra automáticamente al salir del with
            
            print(f"✅ Archivo guardado temporalmente")
            
            # 2. Configurar Gemini
            api_key = os.getenv("GEMINI_API_KEY") 
            if not api_key:
                 api_key = chatbot.config.get("gemini", {}).get("api_key")
            
            if not api_key:
                 print("❌ GEMINI_API_KEY no encontrada")
                 raise HTTPException(status_code=500, detail="API Key de Gemini no encontrada")

            genai.configure(api_key=api_key)

            # 3. Subir archivo a Gemini
            print(f"📤 Subiendo audio a Gemini...")
            # Ahora es seguro abrirlo porque lo cerramos arriba
            uploaded_file = genai.upload_file(tmp_path, mime_type=file.content_type or "audio/webm")
            print(f"✅ Archivo subido: {uploaded_file.name}")
            
            # 4. Generar contenido
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            print("🎧 Solicitando transcripción...")
            response = model.generate_content(
                [uploaded_file, "Transcribe exactamente lo que se dice en este audio al español. No añadas explicaciones, solo el texto transcrito."],
            )
            
            # Borrar de la nube
            try:
                 uploaded_file.delete()
                 print("✅ Archivo eliminado de Gemini")
            except Exception as e:
                 print(f"⚠️ No se pudo eliminar archivo de Gemini: {e}")
                 
            transcribed_text = response.text.strip()
            print(f"✅ Transcripción exitosa: {transcribed_text[:50]}...")
            return TranscribeResponse(text=transcribed_text)

        finally:
            # 5. Limpieza local siempre
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                    print(f"✅ Archivo temporal eliminado: {tmp_path}")
                except Exception as e:
                    print(f"⚠️ No se pudo borrar archivo temporal: {e}")

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en transcripción: {error_msg}")
        import traceback
        traceback.print_exc()
        # Retornar el error detallado para ver en frontend
        raise HTTPException(status_code=500, detail=f"Error en transcripción: {error_msg}")


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Elimina un archivo PDF y todos sus datos asociados."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    try:
        print(f"🗑️ Eliminando archivo: {filename}")
        if chatbot.delete_pdf(filename):
            print(f"✅ Archivo eliminado: {filename}")
            return {"status": "success", "message": f"Archivo {filename} eliminado correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error al eliminar el archivo")
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error al eliminar PDF: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/api/stats", response_model=Stats)
async def get_stats():
    """Devuelve estadísticas de la base de datos RAG."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    try:
        stats_data = chatbot.rag.get_stats()
        return Stats(
            total_chunks=stats_data.get("total_chunks", 0),
            embedding_model=stats_data.get("embedding_model", "unknown"),
            database_path=stats_data.get("database_path", "./chroma_db"),
            pdfs=stats_data.get("pdfs", [])
        )
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en /api/stats: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

class SearchRequest(BaseModel):
    pdf_name: str
    query: str

class SearchResult(BaseModel):
    page: int
    text: str
    rect: Optional[List[float]] = None

@app.post("/api/pdf/search", response_model=List[SearchResult])
async def search_pdf(request: SearchRequest):
    """Busca texto dentro de un PDF usando fitz (PyMuPDF)."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    try:
        # Construir ruta completa
        pdf_path = os.path.join(UPLOAD_DIR, request.pdf_name)
        if not os.path.exists(pdf_path):
             raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")

        results = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(pdf_path)
            
            for page_num, page in enumerate(doc):
                # Búsqueda insensible a mayúsculas
                text_instances = page.search_for(request.query)
                
                # Obtener snippet de texto para cada coincidencia (básico)
                if text_instances:
                    # Si hay coincidencias, añadimos la página
                    # Para un snippet mejor, podríamos extraer texto alrededor del rect
                    # Por ahora, devolvemos un extracto simple o el texto de la instancia
                    
                    for rect in text_instances:
                        # Extraer un poco de contexto
                        expanded_rect = fitz.Rect(rect.x0 - 50, rect.y0 - 20, rect.x1 + 50, rect.y1 + 20)
                        snippet = page.get_textbox(expanded_rect)
                        
                        results.append(SearchResult(
                            page=page_num + 1, # 1-indexed para UI
                            text=snippet.replace('\n', ' ')[:100] + "...",
                            rect=[rect.x0, rect.y0, rect.x1, rect.y1]
                        ))
                        # Limitamos resultados por página para no saturar
                        if len(results) > 50: break
                if len(results) > 50: break
                
            doc.close()
            
        except ImportError:
            print("⚠️ PyMuPDF (fitz) no instalado. Usando búsqueda básica.")
            # Fallback (opcional) o error
            raise HTTPException(status_code=501, detail="Búsqueda avanzada no disponible en servidor")
            
        return results

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en búsqueda PDF: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

class MindMapRequest(BaseModel):
    pdf_name: str

# ... (existing code) ...

@app.post("/api/pdf/mindmap")
async def generate_mindmap(request: MindMapRequest):
    """Genera un mapa conceptual a partir de un PDF."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    try:
        # Construir ruta completa
        pdf_path = os.path.join(UPLOAD_DIR, request.pdf_name)
        if not os.path.exists(pdf_path):
             raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")

        print(f"🧠 Generando mapa conceptual para: {request.pdf_name}")
        mindmap_data = chatbot.generate_mindmap(pdf_path)
        return mindmap_data
    except ValueError as ve:
         raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error generando mapa: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor Backend en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
