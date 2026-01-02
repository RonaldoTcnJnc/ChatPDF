from openai import OpenAI
from rag_system import RAGSystem
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

class ChatbotRAG:
    def __init__(self, config_path: str = "config.json"):
        """
        Inicializa el chatbot con RAG.
        Carga la configuración desde config.json por defecto.
        """
        self.config = self._load_config(config_path)
        
        # Configuración de LMStudio
        self.base_url = self.config["lmstudio"]["base_url"]
        self.model_name = self.config["lmstudio"]["model_name"]
        self.api_key = self.config["lmstudio"]["api_key"]
        
        # Configuración RAG
        self.rag_db_path = self.config["rag"]["db_path"]
        self.model_context_size = self.config["lmstudio"].get("model_context_size", 8192) # Default
        
        # Reservar tokens para la respuesta y mensajes del sistema (reducido para más contexto)
        self.reserved_tokens = 256
        # Aproximación: caracteres por token (heurística)
        self.chars_per_token = 4
        
        print(f"🔌 Conectando a LMStudio en: {self.base_url}")
        print(f"🧠 Modelo: {self.model_name}")
        
        try:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            # Verificación rápida de conexión (opcional, puede ralentizar inicio)
            # self.client.models.list()
            print("✅ Conexión con LMStudio establecida.")
        except Exception as e:
            print(f"⚠️  No se pudo conectar a LMStudio: {e}")
            print("   Asegúrate de que LMStudio esté corriendo y el servidor local activado.")
            # Opcional: raise la excepción o salir si la conexión es crítica
            raise

        # Inicializar sistema RAG
        self.rag = RAGSystem(
            db_path=self.rag_db_path,
            model_name=self.config["rag"]["embeddings_model"]
        )
        
        # Historial de mensajes
        self.messages = []
        
        print("🔵 Chatbot RAG inicializado")
        print(f"🤖 Modelo: {self.model_name}")
        print(f"📚 Base de datos RAG: {self.rag_db_path}")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Carga la configuración desde un archivo JSON."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  No se encontró {config_path}. Usando valores por defecto.")
            return {
                "lmstudio": {
                    "base_url": "http://localhost:1234/v1",
                    "model_name": "lmstudio-community/Meta-Llama-3-8B-Instruct",
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
        """
        Carga PDFs desde una carpeta.
        
        Args:
            folder_path: Ruta a la carpeta con PDFs
        """
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
        """
        Carga un solo PDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
        """
        if not os.path.exists(pdf_path):
            print(f"❌ Archivo no encontrado: {pdf_path}")
            return False
        
        self.rag.add_pdf(pdf_path)
        return True
    
    def get_response(self, user_message, use_rag=True, k=3, pdf_name=None):
        """
        Obtiene una respuesta del modelo con o sin RAG.
        
        Args:
            user_message: Mensaje del usuario
            use_rag: Si se debe usar RAG para recuperar contexto
            k: Número de documentos relevantes a recuperar
            
        Returns:
            Respuesta del modelo
        """
        # Obtener contexto del RAG si está activado
        context = ""
        if use_rag:
            if pdf_name:
                context = self.rag.get_context_by_pdf(user_message, pdf_name, k=k)
                print(f"\n📚 Contexto recuperado desde PDF '{pdf_name}'")
                print(f"   Largo: {len(context)} caracteres")
                print(f"   Primeros 200 chars: {context[:200]}...")
            else:
                context = self.rag.get_context(user_message, k=k)
                print(f"\n📚 Contexto recuperado (global)")
                print(f"   Largo: {len(context)} caracteres")

        # Verificar si hay contexto válido
        print(f"✓ context no vacío: {bool(context)}")
        print(f"✓ 'No hay información' en context: {'No hay información' in context}")

        # Truncar contexto si excede la capacidad del modelo (aproximación por caracteres)
        if context and "No hay información" not in context:
            max_tokens_for_context = max(0, self.model_context_size - self.reserved_tokens)
            max_chars = max_tokens_for_context * self.chars_per_token
            if len(context) > max_chars:
                # Mantener la parte más relevante (la última parte suele contener respuestas/fragmentos útiles)
                context = context[-max_chars:]
                context = "[...contexto recortado...]\n" + context
                print(f"⚠️ Contexto recortado a {max_chars} caracteres para ajustarse al modelo")

        # Preparar mensajes para el modelo
        messages_to_send = self.messages.copy()

        # Agregar el contexto del RAG como parte del mensaje si está disponible
        print(f"✓ Antes de agregar context: {len(messages_to_send)} mensajes, context={bool(context) and 'No hay información' not in context}")
        
        if context and "No hay información" not in context:
            print(f"✓ AGREGANDO CONTEXTO AL SYSTEM MESSAGE")
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

            # Agregar contexto como mensaje de sistema
            if not any(msg.get("role") == "system" for msg in messages_to_send):
                messages_to_send.insert(0, {"role": "system", "content": system_message})
                print(f"✓ System message insertado ({len(system_message)} chars)")
        else:
            print(f"✗ NO SE AGREGÓ CONTEXTO (context vacío o contiene 'No hay información')")

        # Agregar mensaje del usuario
        user_content = f"PREGUNTA: {user_message}"
        messages_to_send.append({"role": "user", "content": user_content})

        # --- Gestión del tamaño total del prompt para evitar overflow de tokens ---
        # Estimación simple de tokens basada en caracteres
        def estimate_tokens(text: str) -> int:
            if not text:
                return 0
            return max(1, int(len(text) / self.chars_per_token))

        # Si el historial es muy largo (más de 2 turnos), recortar solo ese historial, NO el system message
        if len([m for m in messages_to_send if m.get("role") != "system"]) > 8:
            new_messages = []
            # Mantener todos los system messages
            for m in messages_to_send:
                if m.get("role") == "system":
                    new_messages.append(m)
            # Mantener solo los últimos 4 turnos de historial (user/assistant pairs)
            tail = [m for m in messages_to_send if m.get("role") != "system"]
            tail = tail[-8:]
            new_messages.extend(tail)
            messages_to_send = new_messages
            print(f"📝 Historial recortado a los últimos 4 turnos para caber en el contexto")
        
        # Obtener respuesta del modelo
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=1000
            )
            
            bot_message = response.choices[0].message.content
            
            # Guardar en historial
            self.messages.append({"role": "user", "content": user_message})
            self.messages.append({"role": "assistant", "content": bot_message})
            
            return bot_message
            
        except Exception as e:
            return f"❌ Error al obtener respuesta: {e}"
    
    def clear_chat_history(self):
        """Limpia el historial de chat."""
        self.messages = []
        print("✅ Historial de chat limpiado")
    
    def show_stats(self):
        """Muestra estadísticas del sistema."""
        try:
            stats = self.rag.get_stats()
            print("\n📊 Estadísticas del Sistema:")
            print(f"  - Chunks en BD: {stats['total_chunks']}")
            print(f"  - Modelo de embeddings: {stats['embedding_model']}")
            print(f"  - Ruta BD: {stats['database_path']}")
        except AttributeError:
            print("\n⚠️  No se pueden obtener las estadísticas en este momento")
    
    def interactive_chat(self, folder_path=None):
        """
        Inicia un chat interactivo.
        
        Args:
            folder_path: Carpeta con PDFs a cargar (opcional)
        """
        if folder_path:
            self.load_pdfs(folder_path)
        
        print("\n" + "="*60)
        print("🔵 Chat iniciado (escribe 'salir' para terminar)")
        print("Comandos especiales:")
        print("  - 'limpiar': Limpia el historial de chat")
        print("  - 'stats': Muestra estadísticas")
        print("  - 'cargar /ruta/pdf': Carga un PDF")
        print("="*60 + "\n")
        
        while True:
            try:
                user_input = input("Tú: ").strip()
                
                if not user_input:
                    continue
                
                # Comandos especiales
                if user_input.lower() in ["salir", "exit", "quit"]:
                    print("👋 Chat finalizado.")
                    break
                
                elif user_input.lower() == "limpiar":
                    self.clear_chat_history()
                    print("✅ Historial limpiado\n")
                    continue
                
                elif user_input.lower() == "stats":
                    self.show_stats()
                    print()
                    continue
                
                elif user_input.lower().startswith("cargar "):
                    ruta = user_input[7:].strip()
                    if ruta.endswith(".pdf"):
                        self.load_single_pdf(ruta)
                    else:
                        self.load_pdfs(ruta)
                    print()
                    continue
                
                # Chat normal con RAG
                print("\n⏳ Procesando...")
                response = self.get_response(user_input, use_rag=True)
                print(f"🤖 Modelo: {response}\n")
                
            except KeyboardInterrupt:
                print("\n👋 Chat interrumpido.")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")


if __name__ == "__main__":
    # Ejemplo de uso
    chatbot = ChatbotRAG()
    
    # Crear carpeta para PDFs si no existe
    pdf_folder = "./pdfs"
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
        print(f"📂 Carpeta creada: {pdf_folder}")
        print(f"⚠️  Coloca tus PDFs en: {pdf_folder}")
    
    # Iniciar chat interactivo
    chatbot.interactive_chat(folder_path=pdf_folder)
