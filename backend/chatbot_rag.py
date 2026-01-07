from rag_system import RAGSystem
import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from web_search import WebSearcher
from openai import OpenAI

# Cargar variables de entorno
# Buscar .env en el directorio actual o uno arriba (root del proyecto)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
if not os.getenv("GEMINI_API_KEY"):
    load_dotenv() # Intentar carga estándar si falla la explícita

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
        
        # Inicializar buscador web
        self.searcher = WebSearcher()
        
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
            import google.genai as genai
            
            # Obtener API key (prioridad: env > config)
            api_key = os.getenv("GEMINI_API_KEY") or self.config.get("gemini", {}).get("api_key", "")
            
            if not api_key:
                print("⚠️  No se encontró GEMINI_API_KEY. Configúrala en .env o config.json")
                raise ValueError("API key de Gemini no configurada")
            
            # Nueva API de google.genai
            self.gemini_client = genai.Client(api_key=api_key)
            
            model_name = self.config.get("gemini", {}).get("model_name", "gemini-2.5-flash")
            self.gemini_model = model_name
            self.model_name = model_name
            
            print(f"✅ Conectado a Gemini API")
            print(f"🧠 Modelo: {model_name}")
            
        except ImportError:
            print("❌ google-genai no instalado. Ejecuta: pip install google-genai")
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
                    "model_name": "gemini-2.5-flash"
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
    
    def delete_pdf(self, pdf_name):
        """Elimina un PDF completamente."""
        return self.rag.delete_pdf(pdf_name)
    
    def identify_pdf_sections(self, pdf_path):
        """
        Identifica las secciones de un PDF SIN indexarlas.
        Útil para ver la estructura antes de procesarlo.
        
        Args:
            pdf_path: Ruta al PDF
            
        Returns:
            Dict con secciones identificadas
        """
        return self.rag.identify_pdf_sections(pdf_path)
    
    def show_pdf_structure(self, pdf_path):
        """
        Muestra de forma legible la estructura de secciones de un PDF.
        
        Args:
            pdf_path: Ruta al PDF
        """
        self.rag.print_pdf_structure(pdf_path)
    
    def get_response(self, user_message, use_rag=True, k=None, pdf_name=None):
        """
        Obtiene una respuesta del modelo con o sin RAG.
        Usa el proveedor configurado (Gemini o local).
        Ahora detecta automáticamente búsquedas de secciones (abstract, introducción, etc.)
        """
        # Determinar k dinámicamente si no se especifica
        if k is None:
            if self.provider == "gemini":
                k = 60 # Gemini 2.5 Flash tiene contexto masivo (1M tokens). Leemos casi todo.
            else:
                k = 8  # Local: 8 chunks * 250 palabras = ~2000 palabras (~2600 tokens). Seguro para 8k.
        
        # Obtener contexto (RAG o Web)
        context = ""
        
        # ✅ NUEVO: Detectar búsqueda de sección específica PRIMERO
        section_request = self._detect_section_request(user_message)
        if section_request and use_rag:
            section_type, section_keywords = section_request
            print(f"📑 Sección detectada: '{section_type}' (keywords: {section_keywords})")
            context = self.rag.get_section_content(section_type, pdf_name)
            if context and not context.startswith("No se encontró"):
                print(f"✅ Contenido de sección '{section_type}' recuperado ({len(context)} caracteres)")
            else:
                # Fallback a búsqueda normal si no se encuentra la sección
                print(f"⚠️ No se encontró sección '{section_type}', usando búsqueda RAG normal...")
                context = ""
        
        # Si no se detectó sección o falló, proceder con búsqueda normal
        if not context or context.startswith("No se encontró"):
            # Detectar búsqueda web explícita
            search_triggers = [
                "buscar", "investigar", "search", "web", "encuentra", "find", 
                "indaga", "rastrea", "consigue", "busca", "analiza", 
                "papers", "artículos", "articles", "quiero saber", "dame info",
                "recomienda", "recomendar", "sugiere", "tienes", "conoces", "otros paper"
            ]
            
            trigger_used = next((t for t in search_triggers if t in user_message.lower()), None)
            
            if trigger_used:
                print(f"🌍 Modo Web activado por keyword: '{trigger_used}'")
                
                idx = user_message.lower().find(trigger_used)
                clean_query = user_message[idx + len(trigger_used):].strip() if idx != -1 else user_message
                
                if len(clean_query) < 3:
                    clean_query = user_message
                for prep in ["sobre", "about", "de", "for", "en", "in", "que hablen", "mas", "del", "tema"]:
                    if clean_query.lower().startswith(prep + " "):
                        clean_query = clean_query[len(prep):].strip()
                        break
                
                if len(clean_query) < 3:
                    clean_query = user_message
                
                results = self.searcher.unified_search(clean_query)
                context = self._format_search_results(results)
                if not context:
                    context = "No se encontraron resultados en la web."
                    
            elif use_rag:
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


        system_message = "Eres un asistente útil y amable."
        
        # Construir el prompt del sistema si hay contexto
        if context and "No hay información" not in context:
            system_message = f"""Eres un asistente IA educativo y versátil.
Tu objetivo es proporcionar respuestas DETALLADAS y completas basadas en el siguiente contexto:

CONTEXTO:
{context}

INSTRUCCIONES:
1.  **Prioridad al Contexto**: Basa tu respuesta EXCLUSIVAMENTE en la información proporcionada arriba.
2.  **Extensión**: Proporciona explicaciones amplias y profundas. Evita respuestas monosílabas o demasiado breves. Si el usuario pide un resumen, hazlo sustancial.
3.  **Idioma**: Responde SIEMPRE en el mismo idioma en el que el usuario hace la pregunta.
4.  **Formato**: Usa Markdown (negritas, listas) para estructurar tu respuesta de forma clara.
5.  **Honestidad**: Si la información no está en el contexto, dilo claramente."""

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
        """
        Obtiene respuesta de Gemini API con manejo robusto de errores.
        Implementa reintentos para errores 503 y fallback a modelo local.
        """
        import time
        max_retries = 3
        retry_delay = 2  # segundos
        
        for attempt in range(max_retries):
            try:
                if system_message:
                    full_prompt = f"{system_message}\n\nPREGUNTA: {user_message}"
                else:
                    full_prompt = user_message
                
                # Nueva API de google.genai
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=full_prompt
                )
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                error_lower = error_msg.lower()
                
                # ❌ Error 503 - Servidor sobrecargado
                if "503" in error_msg or "overloaded" in error_lower or "unavailable" in error_lower:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (attempt + 1)
                        print(f"⚠️  Gemini API sobrecargada (intento {attempt + 1}/{max_retries})")
                        print(f"   Reintentando en {wait_time} segundos...")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Fallback a modelo local después de reintentos
                        print(f"⚠️  Gemini no disponible después de {max_retries} intentos")
                        print(f"   Cambiando a modelo local...")
                        try:
                            return self._get_local_response(user_message, system_message)
                        except Exception as local_error:
                            return f"⚠️ Error: Gemini API no disponible y modelo local tampoco responde. Por favor intenta más tarde.\n\nDetalles: {str(local_error)[:100]}"
                
                # ❌ Error 429 - Cuota excedida
                elif "429" in error_msg or "quota" in error_lower or "resourceexhausted" in error_lower:
                    return "⚠️ Error: Se ha excedido la cuota gratuita de Gemini API. Por favor:\n1. Espera 1 hora\n2. O cambia a modelo local (en configuración)\n3. O configura tu API key de pago"
                
                # ❌ Error 401 - No autorizado
                elif "401" in error_msg or "unauthenticated" in error_lower or "invalid.*api" in error_lower:
                    return "❌ Error de autenticación: API key de Gemini inválida o no configurada. Verifica tu .env o config.json"
                
                # ❌ Otros errores
                else:
                    print(f"❌ Error de Gemini (intento {attempt + 1}/{max_retries}): {error_msg[:100]}")
                    if attempt == max_retries - 1:
                        # Último intento falló, usar local
                        try:
                            print(f"   Fallback a modelo local...")
                            return self._get_local_response(user_message, system_message)
                        except:
                            return f"❌ Error: No se pudo conectar con Gemini ni con el modelo local. Por favor verifica:\n1. Conexión a internet\n2. API key de Gemini\n3. Servidor LMStudio si usas modelo local"
                    time.sleep(retry_delay)
                    continue
        
        return "❌ Error: No se pudo obtener respuesta de Gemini"
    
    def _get_local_response(self, user_message: str, system_message: Optional[str]) -> str:
        """Obtiene respuesta del modelo local (LMStudio)."""
        try:
            messages_to_send = self.messages.copy()
            
            if system_message:
                if not any(msg.get("role") == "system" for msg in messages_to_send):
                    messages_to_send.insert(0, {"role": "system", "content": system_message})
            
            messages_to_send.append({"role": "user", "content": f"PREGUNTA: {user_message}"})
            
            if len([m for m in messages_to_send if m.get("role") != "system"]) > 4:
                new_messages = [m for m in messages_to_send if m.get("role") == "system"]
                tail = [m for m in messages_to_send if m.get("role") != "system"][-4:]
                new_messages.extend(tail)
                messages_to_send = new_messages
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=2500
            )
            
            if not response.choices:
                return "❌ Error: El modelo local devolvió una respuesta vacía."
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

    def _format_search_results(self, results):
        """Formatea los resultados de búsqueda para el contexto."""
        if not results:
            return ""
        
        formatted = "Información encontrada en la Web/ArXiv:\n\n"
        for i, item in enumerate(results, 1):
            formatted += f"[{i}] TÍTULO: {item['title']}\n"
            formatted += f"    FUENTE: {item['source']}\n"
            formatted += f"    URL: {item['url']}\n"
            formatted += f"    RESUMEN: {item['summary'][:300]}...\n\n"
        
        return formatted
    
    def _detect_section_request(self, user_message: str) -> Optional[Tuple[str, List[str]]]:
        """
        Detecta si el usuario está pidiendo una sección específica (Abstract, Introducción, etc.)
        
        Returns:
            Tupla (section_type, matched_keywords) o None si no detecta sección
        
        Examples:
            "Show me the abstract" -> ("abstract", ["abstract"])
            "Cuál es la introducción?" -> ("introduction", ["introducción"])
            "Dame los métodos" -> ("methods", ["métodos"])
        """
        message_lower = user_message.lower()
        
        # Mapeo de secciones con sus keywords
        section_keywords = {
            "abstract": ["abstract", "resumen", "summary", "sumario", "resúmen"],
            "introduction": ["introducción", "introduccion", "introduction", "intro", "antecedentes", "introducting"],
            "methods": ["métodos", "metodos", "methodology", "metodología", "metodologia", "método", "method", "methods"],
            "results": ["resultados", "results", "findings", "hallazgos", "resultado"],
            "discussion": ["discusión", "discusion", "discussion", "análisis", "analisis"],
            "conclusion": ["conclusión", "conclusion", "conclusiones", "conclusions", "conclusão"],
            "references": ["referencias", "references", "bibliografía", "bibliografia", "bibliography"],
            "title": ["título", "titulo", "title"],
            "appendix": ["apéndice", "appendix", "anexo", "anexos", "supplement"]
        }
        
        # Frases de búsqueda que indican que se busca una sección
        section_triggers = [
            "muestra", "show", "cuál", "cual", "que es", "what is", "what's", "dame", "give me",
            "obtén", "get", "decirme", "tell me", "sección", "section", "capítulo",
            "chapter", "parte", "part", "contenido", "content", "enseña", "show me"
        ]
        
        # Verificar si hay un trigger de búsqueda de sección
        has_trigger = any(trigger in message_lower for trigger in section_triggers)
        
        if not has_trigger:
            return None
        
        # Buscar keywords de secciones en el mensaje
        for section_type, keywords in section_keywords.items():
            matched_keywords = []
            for keyword in keywords:
                if keyword in message_lower:
                    matched_keywords.append(keyword)
            
            if matched_keywords:
                return (section_type, matched_keywords)
        
        return None

    
    def generate_mindmap(self, pdf_path):
        """Genera un mapa conceptual (JSON de nodos y aristas) a partir de los chunks RAG."""
        import json
        import os

        pdf_name = os.path.basename(pdf_path)
        print(f"🧠 Generando mapa conceptual para: {pdf_name} (usando chunks RAG)")
        
        max_chunks = 30 if self.provider == "gemini" else 10
        chunks = self.rag.get_all_chunks_for_pdf(pdf_name, max_chunks=max_chunks)
        
        if not chunks:
            print(f"⚠️ No se encontraron chunks RAG para {pdf_name}, usando extracción directa como fallback")
            full_text = self.rag.extract_text_from_pdf(pdf_path)
            if not full_text:
                raise ValueError("No se pudo extraer texto del PDF")
            # Limitar caracteres también
            char_limit = 25000 if self.provider == "gemini" else 6000
            text_context = full_text[:char_limit]
        else:
            text_context = "\n\n---\n\n".join(chunks) 
            
            if self.provider != "gemini" and len(text_context) > 10000:
                print(f"⚠️ Recortando contexto para modelo local ({len(text_context)} -> 10000 chars)")
                text_context = text_context[:10000] 
        
        prompt = f"""Analiza el siguiente texto de un documento académico/técnico y genera un MAPA CONCEPTUAL.
        
TEXTO:
{text_context}

INSTRUCCIONES:
1. Identifica los conceptos más importantes (Nodos).
2. Identifica las relaciones entre ellos (Aristas/Conexiones).
3. IMPORTANTE: EL CONTENIDO DEBE ESTAR EN ESPAÑOL. Traduce los términos si es necesario.
4. Devuelve SALIDA EXCLUSIVAMENTE EN FORMATO JSON con la siguiente estructura:
{{
    "nodes": [
        {{ "id": "1", "label": "Concepto Principal", "type": "main" }},
        {{ "id": "2", "label": "Subconcepto A", "type": "sub" }}
    ],
    "edges": [
        {{ "source": "1", "target": "2", "label": "se compone de" }}
    ]
}}

IMPORTANTE:
- El JSON debe ser válido.
- No añadas texto antes ni después del JSON. NO markdown codes (```json).
- GENERA TODO EN ESPAÑOL.
"""
        
        if self.provider == "gemini":
            response_text = self._get_gemini_response(prompt, system_message="Eres un experto en síntesis y visualización de conocimiento. Devuelve solo JSON.")
        else:
            try:
                print("🧠 Solicitando mapa conceptual a modelo local...")
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "Eres un asistente experto que SOLO habla JSON. Tu tarea es extraer entidades y relaciones de textos. NO respondas con texto, SOLO JSON válido."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=3000
                )
                if not response.choices:
                    raise ValueError("El modelo local devolvió una respuesta vacía (sin opciones).")
                response_text = response.choices[0].message.content
            except Exception as e:
                print(f"❌ Error al generar mapa local: {e}")
                raise ValueError(f"Error al conectar con modelo local: {e}")
            
        clean_json = response_text
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0]
        elif "```" in clean_json:
            parts = clean_json.split("```")
            clean_json = parts[1] if len(parts) > 1 else clean_json
            
        clean_json = clean_json.strip()
        
        try:
            start = clean_json.find('{')
            end = clean_json.rfind('}') + 1
            if start != -1 and end != -1:
                clean_json = clean_json[start:end]
            
            # Limpiar caracteres de escape inválidos antes de parsear
            # Reemplazar barras invertidas mal colocadas (ej: \( -> ()
            import re
            # Eliminar barras invertidas que preceden a caracteres que no necesitan escape
            clean_json = re.sub(r'\\(["\\\\/])', r'\1', clean_json)  # Dejar solo escapes válidos
            clean_json = re.sub(r'\\(?!["\\\\/bfnrtu])', '', clean_json)  # Eliminar otras barras invertidas inválidas
            
            data = json.loads(clean_json)
            return data
        except json.JSONDecodeError as e:
            print(f"❌ Error al decodificar JSON del LLM (intento 1): {clean_json[:100]}... Error: {e}")
            
            # Fallback: intentar con json.JSONDecoder en strict=False (si es soportado) o usar ast.literal_eval
            try:
                import ast
                # Si el JSON no funciona, intentar extraer estructura manualmente
                # Buscar arrays de objetos entre [] y {}
                nodes_match = re.search(r'"nodes"\s*:\s*\[(.*?)\](?=\s*,\s*"edges"|$)', clean_json, re.DOTALL)
                edges_match = re.search(r'"edges"\s*:\s*\[(.*?)\]', clean_json, re.DOTALL)
                
                if nodes_match and edges_match:
                    nodes_str = '[' + nodes_match.group(1) + ']'
                    edges_str = '[' + edges_match.group(1) + ']'
                    
                    # Limpiar más agresivamente
                    for pattern in [r'\\(?!["\\\\/bfnrtu])', r'\\(?=[^"])', r'\\\\']:
                        nodes_str = re.sub(pattern, '', nodes_str)
                        edges_str = re.sub(pattern, '', edges_str)
                    
                    data = {
                        "nodes": json.loads(nodes_str),
                        "edges": json.loads(edges_str)
                    }
                    print(f"✅ JSON recuperado con regex (fallback)")
                    return data
            except Exception as e2:
                print(f"⚠️ Fallback también falló: {e2}")
            
            # Si todo falla, retornar estructura vacía con error
            print(f"⚠️ Usando estructura de error (JSON inválido del LLM)")
            return {
                "nodes": [{"id": "error", "label": "Error al generar mapa - Intenta de nuevo", "type": "main"}],
                "edges": []
            }

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
