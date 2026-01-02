from openai import OpenAI
from rag_system import RAGSystem
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class ChatbotRAG:
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa el chatbot con RAG.
        Soporta múltiples proveedores: 'gemini' o 'local' (LMStudio).
        """
        self.config = self._load_config(config_path)
        
        # Determinar proveedor
        self.provider = self.config.get("provider", "local")
        self.client = None
        self.gemini_model = None
        
        # Configuración RAG
        self.rag_db_path = self.config["rag"]["db_path"]
        self.model_context_size = self.config.get("lmstudio", {}).get("model_context_size", 8192)
        
        # Reservar tokens para la respuesta
        self.reserved_tokens = 256
        self.chars_per_token = 4
        
        # Inicializar proveedor
        self._init_provider()
        
        # Inicializar sistema RAG
        self.rag = RAGSystem(
            db_path=self.rag_db_path,
            model_name=self.config["rag"]["embeddings_model"]
        )
        
        # Historial de mensajes
        self.messages = []
        
        print(f"🔵 Chatbot RAG inicializado")
        print(f"🤖 Proveedor: {self.provider}")
        print(f"📚 Base de datos RAG: {self.rag_db_path}")
    
    def _init_provider(self):
        """Inicializa el proveedor de LLM según la configuración."""
        if self.provider == "gemini":
            self._init_gemini()
        else:
            self._init_local()
    
    def _init_gemini(self):
        """Inicializa la conexión con Gemini API."""
        try:
            import google.generativeai as genai
            
            # Obtener API key (prioridad: env > config)
            api_key = os.getenv("GEMINI_API_KEY") or self.config.get("gemini", {}).get("api_key", "")
            
            if not api_key:
                print("⚠️  No se encontró GEMINI_API_KEY. Configúrala en .env o config.json")
                raise ValueError("API key de Gemini no configurada")
            
            genai.configure(api_key=api_key)
            
            model_name = self.config.get("gemini", {}).get("model_name", "gemini-2.0-flash")
            self.gemini_model = genai.GenerativeModel(model_name)
            self.model_name = model_name
            
            print(f"✅ Conectado a Gemini API")
            print(f"🧠 Modelo: {model_name}")
            
        except ImportError:
            print("❌ google-generativeai no instalado. Ejecuta: pip install google-generativeai")
            raise
        except Exception as e:
            print(f"❌ Error al conectar con Gemini: {e}")
            # Intentar fallback a local
            print("⚠️  Intentando fallback a modelo local...")
            self.provider = "local"
            self._init_local()
    
    def _init_local(self):
        """Inicializa la conexión con LMStudio (local)."""
        lmstudio_config = self.config.get("lmstudio", {})
        self.base_url = lmstudio_config.get("base_url", "http://localhost:1234/v1")
        self.model_name = lmstudio_config.get("model_name", "local-model")
        api_key = lmstudio_config.get("api_key", "not-needed")
        
        print(f"🔌 Conectando a LMStudio en: {self.base_url}")
        
        try:
            self.client = OpenAI(base_url=self.base_url, api_key=api_key)
            # Intentar listar modelos para verificar conexión real
            try:
                self.client.models.list()
            except Exception as e:
                raise ConnectionError(f"No se pudo conectar a LMStudio: {e}")
            
            print(f"✅ Conexión con LMStudio establecida")
            print(f"🧠 Modelo: {self.model_name}")
        except Exception as e:
            print(f"⚠️  No se pudo conectar a LMStudio: {e}")
            # Intentar fallback a Gemini si hay API key
            if os.getenv("GEMINI_API_KEY") or self.config.get("gemini", {}).get("api_key"):
                print("⚠️  Intentando fallback a Gemini...")
                self.provider = "gemini"
                self._init_gemini()
            else:
                raise
    
    def set_provider(self, provider: str):
        """Cambia el proveedor de LLM en tiempo de ejecución."""
        if provider not in ["gemini", "local"]:
            print(f"❌ Proveedor inválido: {provider}. Usa 'gemini' o 'local'")
            return False
        
        self.provider = provider
        self._init_provider()
        return True
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carga la configuración desde un archivo JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  No se encontró {config_path}. Usando valores por defecto.")
            return {
                "provider": "local",
                "gemini": {
                    "api_key": "",
                    "model_name": "gemini-2.0-flash"
                },
                "lmstudio": {
                    "base_url": "http://localhost:1234/v1",
                    "model_name": "local-model",
                    "api_key": "not-needed"
                },
                "rag": {
                    "db_path": "./chroma_db",
                    "embeddings_model": "all-MiniLM-L6-v2"
                }
            }
        except json.JSONDecodeError:
            print(f"❌ Error al leer {config_path}. Verifica el formato JSON.")
            raise

    def load_pdfs(self, folder_path: str):
        """Carga PDFs desde una carpeta."""
        print(f"\n📂 Cargando PDFs desde: {folder_path}")
        if not os.path.exists(folder_path):
            print(f"❌ Carpeta no encontrada: {folder_path}")
            return False
        
        self.rag.add_pdf_folder(folder_path)
        try:
            stats = self.rag.get_stats()
            print(f"✅ Total de chunks en BD: {stats['total_chunks']}")
        except AttributeError:
            print(f"⚠️  No se pudo obtener estadísticas")
        return True
    
    def load_single_pdf(self, pdf_path):
        """Carga un solo PDF."""
        if not os.path.exists(pdf_path):
            print(f"❌ Archivo no encontrado: {pdf_path}")
            return False
        
        self.rag.add_pdf(pdf_path)
        return True
    
    def get_response(self, user_message, use_rag=True, k=3, pdf_name=None):
        """
        Obtiene una respuesta del modelo con o sin RAG.
        Usa el proveedor configurado (Gemini o local).
        """
        # Obtener contexto del RAG si está activado
        context = ""
        if use_rag:
            if pdf_name:
                context = self.rag.get_context_by_pdf(user_message, pdf_name, k=k)
            else:
                context = self.rag.get_context(user_message, k=k)

        # Truncar contexto si excede la capacidad del modelo
        if context and "No hay información" not in context:
            max_tokens_for_context = max(0, self.model_context_size - self.reserved_tokens)
            max_chars = max_tokens_for_context * self.chars_per_token
            if len(context) > max_chars:
                context = context[-max_chars:]
                context = "[...contexto recortado...]\n" + context

        # Construir el prompt del sistema
        system_message = None
        if context and "No hay información" not in context:
            system_message = f"""Eres un asistente experto que trabaja ÚNICAMENTE con el contenido del documento proporcionado.

DOCUMENTO A ANALIZAR:
{context}

INSTRUCCIONES CRUCIALES:
1. Lee y comprende el documento anterior
2. Responde SOLO con información del documento
3. Si es un resumen, sintetiza los puntos principales del documento
4. Sé conciso pero completo
5. Si algo no está en el documento, dilo claramente

Responde en español, de forma clara y directa."""

        # Obtener respuesta según el proveedor
        if self.provider == "gemini":
            bot_message = self._get_gemini_response(user_message, system_message)
        else:
            bot_message = self._get_local_response(user_message, system_message)
        
        # Guardar en historial
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": bot_message})
        
        return bot_message
    
    def _get_gemini_response(self, user_message: str, system_message: Optional[str]) -> str:
        """Obtiene respuesta de Gemini API."""
        try:
            # Construir el prompt completo
            if system_message:
                full_prompt = f"{system_message}\n\nPREGUNTA: {user_message}"
            else:
                full_prompt = user_message
            
            # Obtener respuesta
            response = self.gemini_model.generate_content(full_prompt)
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                return "⚠️ Error: Se ha excedido la cuota gratuita de Gemini API. Por favor, espera unos minutos o cambia al modelo Local."
            return f"❌ Error al obtener respuesta de Gemini: {e}"
    
    def _get_local_response(self, user_message: str, system_message: Optional[str]) -> str:
        """Obtiene respuesta del modelo local (LMStudio)."""
        try:
            messages_to_send = self.messages.copy()
            
            # Agregar mensaje de sistema si existe
            if system_message:
                if not any(msg.get("role") == "system" for msg in messages_to_send):
                    messages_to_send.insert(0, {"role": "system", "content": system_message})
            
            # Agregar pregunta del usuario
            messages_to_send.append({"role": "user", "content": f"PREGUNTA: {user_message}"})
            
            # Limitar historial si es muy largo
            if len([m for m in messages_to_send if m.get("role") != "system"]) > 8:
                new_messages = [m for m in messages_to_send if m.get("role") == "system"]
                tail = [m for m in messages_to_send if m.get("role") != "system"][-8:]
                new_messages.extend(tail)
                messages_to_send = new_messages
            
            # Obtener respuesta
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Error al obtener respuesta local: {e}"
    
    def clear_chat_history(self):
        """Limpia el historial de chat."""
        self.messages = []
        print("✅ Historial de chat limpiado")
    
    def show_stats(self):
        """Muestra estadísticas del sistema."""
        try:
            stats = self.rag.get_stats()
            print("\n📊 Estadísticas del Sistema:")
            print(f"  - Proveedor: {self.provider}")
            print(f"  - Modelo: {self.model_name}")
            print(f"  - Chunks en BD: {stats['total_chunks']}")
            print(f"  - Modelo de embeddings: {stats['embedding_model']}")
            print(f"  - Ruta BD: {stats['database_path']}")
        except AttributeError:
            print("\n⚠️  No se pueden obtener las estadísticas en este momento")
    
    def interactive_chat(self, folder_path=None):
        """Inicia un chat interactivo."""
        if folder_path:
            self.load_pdfs(folder_path)
        
        print("\n" + "="*60)
        print(f"🔵 Chat iniciado con proveedor: {self.provider}")
        print("Comandos especiales:")
        print("  - 'salir': Termina el chat")
        print("  - 'limpiar': Limpia el historial")
        print("  - 'stats': Muestra estadísticas")
        print("  - 'gemini': Cambiar a Gemini")
        print("  - 'local': Cambiar a modelo local")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("Tú: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ["salir", "exit", "quit"]:
                    print("👋 Chat finalizado.")
                    break
                
                elif user_input.lower() == "limpiar":
                    self.clear_chat_history()
                    continue
                
                elif user_input.lower() == "stats":
                    self.show_stats()
                    continue
                
                elif user_input.lower() == "gemini":
                    self.set_provider("gemini")
                    continue
                
                elif user_input.lower() == "local":
                    self.set_provider("local")
                    continue
                
                elif user_input.lower().startswith("cargar "):
                    ruta = user_input[7:].strip()
                    if ruta.endswith(".pdf"):
                        self.load_single_pdf(ruta)
                    else:
                        self.load_pdfs(ruta)
                    continue
                
                print("\n⏳ Procesando...")
                response = self.get_response(user_input, use_rag=True)
                print(f"🤖 {self.provider.capitalize()}: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Chat interrumpido.")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    chatbot = ChatbotRAG()
    
    pdf_folder = "./pdfs"
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
        print(f"📂 Carpeta creada: {pdf_folder}")
        print(f"⚠️  Coloca tus PDFs en: {pdf_folder}")
    
    chatbot.interactive_chat(folder_path=pdf_folder)
