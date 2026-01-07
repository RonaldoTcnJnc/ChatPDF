from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import shutil
import os
import tempfile
from pathlib import Path
import google.genai as genai
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

class MindMapRequest(BaseModel):
    pdf_name: str

class MindMapResponse(BaseModel):
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

class SearchRequest(BaseModel):
    pdf_name: str
    query: str

class SearchResultItem(BaseModel):
    text: str
    page: int
    source: str

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
UPLOAD_DIR = os.path.abspath("./pdfs")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
    print(f"[INIT] 📂 Directorio de PDFs creado: {UPLOAD_DIR}")

# Instancia global del chatbot
chatbot = None
try:
    print("[INIT] Inicializando ChatbotRAG...")
    chatbot = ChatbotRAG()
    print("[INIT] ✅ ChatbotRAG inicializado correctamente")
except Exception as e:
    print(f"[INIT] ❌ ERROR CRÍTICO al inicializar ChatbotRAG: {e}")
    import traceback
    traceback.print_exc()
    print("[INIT] El servidor continuará funcionando sin RAG hasta que se resuelva el problema")

class ProviderRequest(BaseModel):
    provider: str

# Endpoint para servir PDFs
@app.get("/pdfs/{filename}")
async def get_pdf(filename: str):
    """Sirve archivos PDF con headers correctos."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Seguridad: evitar path traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIR)):
        print(f"[PDF] ❌ Intento de path traversal: {filename}")
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if not os.path.exists(file_path):
        print(f"[PDF] ❌ Archivo no encontrado: {file_path}")
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {filename}")
    
    if not file_path.endswith(".pdf"):
        print(f"[PDF] ❌ No es un PDF: {file_path}")
        raise HTTPException(status_code=403, detail="Solo se permiten archivos PDF")
    
    file_size = os.path.getsize(file_path)
    print(f"[PDF] 📄 Sirviendo: {filename} ({file_size} bytes)")
    
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )

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
        error_detail = "Chatbot no inicializado - Revisa los logs del servidor para más detalles"
        print(f"[UPLOAD] ❌ {error_detail}")
        raise HTTPException(status_code=503, detail=error_detail)
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos PDF")
    
    # Sanitizar nombre del archivo
    import unicodedata
    import re
    
    # Obtener solo el nombre base, quitando todas las extensiones (ej: proyecto.docx.pdf -> proyecto)
    name_without_ext = os.path.splitext(file.filename)[0]  # Quita solo la última ext
    # Pero si tiene múltiples puntos, quitar solo después del primer punto
    if '.' in name_without_ext:
        name_without_ext = name_without_ext.split('.')[0]
    
    # Normalizar el nombre
    normalized = unicodedata.normalize('NFKD', name_without_ext)
    normalized = normalized.encode('ascii', 'ignore').decode('ascii')
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', normalized)
    safe_name = safe_name.strip('_-') or 'document'
    
    # Reconstruir con extensión .pdf (sin prefijo hash, ya que el nombre original es suficiente)
    safe_filename = f"{safe_name}.pdf"
    
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    try:
        print(f"[UPLOAD] 📂 Guardando PDF: {safe_filename}")
        print(f"[UPLOAD] 📍 Ruta completa: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no se guardó correctamente: {file_path}")
        
        file_size = os.path.getsize(file_path)
        print(f"[UPLOAD] ✅ Archivo guardado: {file_size} bytes")
        
        # Validar que es un PDF válido
        with open(file_path, 'rb') as f:
            header = f.read(4)
            if header != b'%PDF':
                raise ValueError(f"El archivo no es un PDF válido (header: {header})")
        
        print(f"[UPLOAD] ✅ PDF válido detectado")
        print(f"[UPLOAD] 🔄 Procesando con RAG...")
        # Procesar con RAG
        chatbot.load_single_pdf(file_path)
        
        # Obtener estadísticas breves
        stats = chatbot.rag.get_stats()
        chunks = stats.get("total_chunks", 0)
        
        print(f"[UPLOAD] ✅ PDF procesado: {chunks} chunks")
        
        return UploadResponse(
            filename=safe_filename,
            status="success",
            chunks=chunks
        )
    except Exception as e:
        error_msg = str(e)
        print(f"[UPLOAD] ❌ Error al subir PDF: {error_msg}")
        import traceback
        traceback.print_exc()
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[UPLOAD] 🗑️ Archivo eliminado por error: {file_path}")
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Error al procesar PDF: {error_msg}")

@app.post("/api/pdf/mindmap", response_model=MindMapResponse)
async def generate_mindmap_endpoint(request: MindMapRequest):
    """Genera un mapa conceptual (nodes/edges) a partir de un PDF cargado."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")

    pdf_name = request.pdf_name
    file_path = os.path.join(UPLOAD_DIR, pdf_name)

    # Seguridad: evitar path traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIR)):
        print(f"[MINDMAP] ❌ Intento de path traversal: {pdf_name}")
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if not os.path.exists(file_path):
        print(f"[MINDMAP] ❌ Archivo no encontrado: {file_path}")
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {pdf_name}")

    try:
        data = chatbot.generate_mindmap(file_path)
        nodes = data.get("nodes", []) if isinstance(data, dict) else []
        edges = data.get("edges", []) if isinstance(data, dict) else []
        return MindMapResponse(nodes=nodes, edges=edges)
    except Exception as e:
        error_msg = str(e)
        print(f"[MINDMAP] ❌ Error generando mapa para {pdf_name}: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/pdf/search", response_model=List[SearchResultItem])
async def search_pdf(request: SearchRequest):
    """Busca texto en un PDF cargado."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")

    pdf_name = request.pdf_name
    query = request.query
    file_path = os.path.join(UPLOAD_DIR, pdf_name)

    # Seguridad: evitar path traversal
    if not os.path.abspath(file_path).startswith(os.path.abspath(UPLOAD_DIR)):
        print(f"[SEARCH] ❌ Intento de path traversal: {pdf_name}")
        raise HTTPException(status_code=403, detail="Acceso denegado")

    if not os.path.exists(file_path):
        print(f"[SEARCH] ❌ Archivo no encontrado: {file_path}")
        raise HTTPException(status_code=404, detail=f"Archivo no encontrado: {pdf_name}")

    try:
        print(f"[SEARCH] 🔍 Buscando '{query}' en {pdf_name}")
        # Usar RAG para buscar en el PDF específico
        results = chatbot.rag.retrieve_by_pdf(query, pdf_name, k=10)
        
        # Formatear resultados
        search_results = []
        for doc, meta in results:
            page_num = meta.get("page", 1)  # Defecto a página 1 si no viene
            if not isinstance(page_num, int) or page_num <= 0:
                page_num = 1
            search_results.append(SearchResultItem(
                text=doc,
                page=page_num,
                source=pdf_name
            ))
        
        # ✅ Ordenar por número de página ascendente
        search_results.sort(key=lambda x: x.page)
        
        print(f"[SEARCH] ✅ {len(search_results)} resultados encontrados (ordenados por página)")
        return search_results
    except Exception as e:
        error_msg = str(e)
        print(f"[SEARCH] ❌ Error buscando en {pdf_name}: {error_msg}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio usando Gemini 2.5 Flash."""
    
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot no inicializado")
    
    # Validar que sea audio (opcional, pero recomendado)
    if file.content_type and not file.content_type.startswith("audio/"):
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

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Iniciando servidor Backend en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
