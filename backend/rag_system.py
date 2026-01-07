import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import time

import chromadb
import pymupdf
from sentence_transformers import SentenceTransformer

class RAGSystem:
    def __init__(self, db_path: str = "./chroma_db", model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa el sistema RAG con ChromaDB y embeddings locales.
        
        Args:
            db_path: Ruta donde se almacenará la base de datos ChromaDB
            model_name: Modelo de embeddings (all-MiniLM-L6-v2 es rápido y ligero)
        """
        self.db_path = db_path
        self.model_name = model_name
        
        # Ensure db_path is absolute relative to this file if it's the default
        if self.db_path == "./chroma_db":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, "chroma_db")
        
        # Inicializar cliente ChromaDB (versión nueva)
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Cargar modelo de embeddings con reintentos
        self.embedding_model = self._load_embedding_model(model_name)
        
        # Diccionario para almacenar colecciones por PDF
        self.collections = {}
        
        # Colección principal para búsquedas globales
        self.collection = self.client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Cargar colecciones existentes
        self._load_existing_collections()
        
        print(f"OK: RAG inicializado con ChromaDB en: {db_path}")
    
    def _load_embedding_model(self, model_name: str):
        """Carga el modelo de embeddings con reintentos en caso de error de conectividad."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                print(f"[RAG] Cargando modelo de embeddings: {model_name}...")
                model = SentenceTransformer(model_name, trust_remote_code=True)
                print(f"OK: Modelo cargado correctamente")
                return model
            except KeyboardInterrupt:
                print(f"[RAG] Descarga interrumpida. Reintentando...")
                time.sleep(retry_delay)
            except Exception as e:
                error_str = str(e)
                if attempt < max_retries - 1:
                    if any(x in error_str for x in ["Connection", "timeout", "socket", "ssl"]):
                        print(f"[RAG] Error de conectividad (intento {attempt + 1}/{max_retries}): {error_str[:50]}...")
                        print(f"[RAG] Reintentando en {retry_delay} segundos...")
                        time.sleep(retry_delay)
                    else:
                        raise
                else:
                    print(f"ERROR: No se pudo cargar el modelo tras {max_retries} intentos")
                    raise
    
    def _load_existing_collections(self):
        """Carga todas las colecciones de PDFs existentes."""
        try:
            all_collections = self.client.list_collections()
            for col in all_collections:
                if col.name.startswith("pdf_"):
                    # Recuperar el nombre original del PDF del metadata o usar el nombre de la colección
                    try:
                        # Obtener un documento para leer el metadata
                        data = col.get()
                        if data and data["metadatas"] and len(data["metadatas"]) > 0:
                            pdf_name = data["metadatas"][0].get("source", col.name)
                        else:
                            pdf_name = col.name
                    except:
                        pdf_name = col.name
                    self.collections[pdf_name] = col
        except:
            pass
    
    def _get_collection_name(self, pdf_name):
        """Genera un nombre de colección válido para ChromaDB."""
        import hashlib
        import unicodedata
        
        # ChromaDB requiere nombres: 3-512 chars, [a-zA-Z0-9._-], sin espacios ni caracteres especiales
        # Crear un hash único del nombre del PDF
        hash_value = hashlib.md5(pdf_name.encode()).hexdigest()[:8]
        
        # Normalizar caracteres Unicode (ó -> o, á -> a, etc.)
        normalized = unicodedata.normalize('NFKD', pdf_name)
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        
        # Usar solo caracteres válidos: [a-zA-Z0-9._-]
        safe_name = "".join(c if c.isalnum() or c in "._-" else "" for c in normalized.lower())
        
        # Limitar longitud y asegurar que empiece y termine con carácter válido
        safe_name = safe_name[:40].strip("_").strip(".").strip("-")
        
        # Asegurar que no esté vacío y tenga longitud mínima
        if not safe_name or len(safe_name) < 1:
            safe_name = "pdf"
        
        collection_name = f"pdf_{hash_value}_{safe_name}"
        
        # Validar que el nombre final sea válido
        if len(collection_name) < 3:
            collection_name = f"pdf_{hash_value}"
        
        return collection_name[:512]
    
    def _get_or_create_pdf_collection(self, pdf_name):
        """Obtiene o crea una colección para un PDF específico."""
        collection_name = self._get_collection_name(pdf_name)
        
        if pdf_name not in self.collections:
            self.collections[pdf_name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine", "pdf": pdf_name}
            )
        
        return self.collections[pdf_name]
    
    def extract_text_from_pdf(self, pdf_path):
        """
        Extrae texto de un PDF preservando la información de página.
        Soporta:
        - PDFs con texto embebido (extracción nativa)
        - PDFs escaneados (OCR con EasyOCR)
        Returns: Lista de diccionarios [{'text': str, 'page': int}]
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"El archivo PDF no existe: {pdf_path}")

        # Validar que es un PDF
        try:
            with open(pdf_path, 'rb') as f:
                header = f.read(4)
                if header != b'%PDF':
                    raise ValueError(f"El archivo no es un PDF válido (header: {header})")
        except Exception as e:
            raise ValueError(f"Error al validar PDF: {e}")

        doc = None
        pages_data = []
        
        try:
            doc = pymupdf.open(pdf_path)
            
            # Primer intento: Extraer texto nativo
            print(f"[OCR] Intentando extracción de texto nativo...")
            native_text_found = False
            
            for page_num, page in enumerate(doc):
                try:
                    text = page.get_text()
                    if text.strip():
                        pages_data.append({
                            "text": text,
                            "page": page_num + 1,
                            "method": "native"
                        })
                        native_text_found = True
                except Exception as e:
                    print(f"⚠️ Error al extraer página nativa {page_num + 1}: {e}")
                    continue
            
            # Si encontró texto nativo, retornar
            if native_text_found and pages_data:
                print(f"✅ Texto extraído (nativo) de: {pdf_path} ({len(pages_data)} páginas)")
                return pages_data
            
            # Segundo intento: OCR si no hay texto nativo
            print(f"[OCR] No se encontró texto nativo. Intentando OCR...")
            pages_data = []
            
            try:
                import easyocr
            except ImportError:
                raise ImportError("EasyOCR no está instalado. Ejecuta: pip install easyocr")
            
            # Inicializar OCR (primero en español, luego inglés para máxima compatibilidad)
            print(f"[OCR] Inicializando modelo OCR (primera ejecución puede tardar)...")
            reader = easyocr.Reader(['es', 'en'], gpu=False)  # gpu=False para evitar problemas
            
            for page_num, page in enumerate(doc):
                try:
                    print(f"[OCR] Procesando página {page_num + 1}...")
                    
                    # Convertir página a imagen
                    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))  # 2x zoom para mejor OCR
                    img_data = pix.tobytes("png")
                    
                    # Guardar temporalmente
                    import io
                    from PIL import Image
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Aplicar OCR
                    results = reader.readtext(img, detail=0)  # detail=0 retorna solo texto
                    text = "\n".join(results)
                    
                    if text.strip():
                        pages_data.append({
                            "text": text,
                            "page": page_num + 1,
                            "method": "ocr"
                        })
                    else:
                        pages_data.append({
                            "text": f"[Página vacía o no legible]",
                            "page": page_num + 1,
                            "method": "ocr"
                        })
                        
                except Exception as e:
                    print(f"⚠️ Error en OCR página {page_num + 1}: {e}")
                    pages_data.append({
                        "text": f"[Error al procesar página]",
                        "page": page_num + 1,
                        "method": "error"
                    })
                    continue
            
            if not pages_data:
                raise ValueError(f"No se pudo extraer texto del PDF: {pdf_path}")
            
            print(f"✅ Texto extraído (OCR) de: {pdf_path} ({len(pages_data)} páginas)")
            return pages_data
            
        except pymupdf.FileError as e:
            raise ValueError(f"Estructura PDF corrupta o inválida: {e}")
        except Exception as e:
            print(f"❌ Error al extraer PDF {pdf_path}: {e}")
            raise
        finally:
            if doc:
                try:
                    doc.close()
                except:
                    pass


    def chunk_text(self, pages_data, chunk_size=500, overlap=50):
        """
        Divide el contenido de las páginas en chunks, preservando el número de página.
        Args:
            pages_data: Lista de dicts [{'text': str, 'page': int}]
        Returns: 
            Lista de tuplas (chunk_text, metadata_dict)
            donde metadata_dict incluye {'page': int}
        """
        chunks_with_metadata = []
        
        for page_entry in pages_data:
            text = page_entry['text']
            page_num = page_entry['page']
            
            words = text.split()
            if not words:
                continue
                
            for i in range(0, len(words), chunk_size - overlap):
                chunk = " ".join(words[i:i + chunk_size])
                if len(chunk) > 50: # Ignorar chunks muy pequeños
                    chunks_with_metadata.append((
                        chunk, 
                        {"page": page_num}
                    ))
        
        return chunks_with_metadata
    
    def add_pdf(self, pdf_path, metadata=None):
        """
        Procesa y agrega un PDF al sistema RAG en su propia colección.
        """
        try:
            pages_data = self.extract_text_from_pdf(pdf_path)
        except Exception as e:
            print(f"❌ Error al procesar PDF {pdf_path}: {e}")
            raise
        
        # chunk_text procesa esa lista y devuelve chunks con metadata de página
        chunks_data = self.chunk_text(pages_data)
        
        # Preparar metadata base
        if metadata is None:
            metadata = {}
        pdf_name = os.path.basename(pdf_path)
        metadata["source"] = pdf_name
        metadata["pdf_path"] = pdf_path
        
        pdf_collection = self._get_or_create_pdf_collection(pdf_name)
        
        for i, (chunk, page_meta) in enumerate(chunks_data):
            try:
                embedding = self.embedding_model.encode(chunk).tolist()
                chunk_id = f"chunk_{i}"
                
                # Combinar metadata base con metadata de página
                full_metadata = metadata.copy()
                full_metadata.update(page_meta)  # ✅ Agregar número de página
                
                # Agregar a colecciones
                pdf_collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[full_metadata]
                )
                
                self.collection.add(
                    ids=[f"{pdf_name}_{i}"],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[full_metadata]
                )
            except Exception as e:
                print(f"❌ Error al procesar chunk {i}: {e}")
        
        print(f"✅ PDF procesado: {pdf_name} - {len(chunks_data)} chunks agregados con estructura")
    
    def add_pdf_folder(self, folder_path):
        """
        Procesa todos los PDFs en una carpeta.
        
        Args:
            folder_path: Ruta a la carpeta con PDFs
        """
        pdf_files = list(Path(folder_path).glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️  No se encontraron PDFs en: {folder_path}")
            return
        
        for pdf_file in pdf_files:
            self.add_pdf(str(pdf_file))
    
    def retrieve(self, query, k=3):
        """
        Recupera los chunks más relevantes para una consulta.
        Returns:
            Lista de tuplas (documento, metadata)
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        if not results or not results["documents"] or not results["documents"][0]:
            return []
        
        # Combinar documentos y metadatos
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
        
        return list(zip(docs, metas))
    
    def get_context(self, query, k=3):
        """
        Obtiene el contexto formateado para el modelo.
        Returns: str (context_text)
        """
        results = self.retrieve(query, k)
        
        if not results:
            return "No hay información en la base de datos."
        
        context = "Información relevante de los documentos:\n\n"
        seen_pages = set()
        
        for i, (doc, meta) in enumerate(results, 1):
            source = meta.get("source", "Desconocido")
            page = meta.get("page")
            context += f"[{i}] (Fuente: {source}"
            if page:
                context += f" | Página: {page}"
            context += f")\n{doc}\n\n"
            
            # Registrar que hemos visto esta página
            if page and (source, page) not in seen_pages:
                seen_pages.add((source, page))
        
        return context
    
    def clear_database(self):
        """
        Limpia la base de datos ChromaDB completamente.
        """
        try:
            # Eliminar todas las colecciones de PDFs
            for pdf_name in list(self.collections.keys()):
                try:
                    collection_name = self._get_collection_name(pdf_name)
                    self.client.delete_collection(name=collection_name)
                except:
                    pass
            
            # Limpiar diccionario de colecciones
            self.collections.clear()
            
            # Eliminar colección principal
            self.client.delete_collection(name="papers")
            
            # Recrear colección principal
            self.collection = self.client.get_or_create_collection(
                name="papers",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ Base de datos limpiada completamente")
        except Exception as e:
            print(f"⚠️  Error al limpiar BD: {e}")
            # Si falla, intentar reiniciar
            try:
                self.collection = self.client.get_or_create_collection(
                    name="papers",
                    metadata={"hnsw:space": "cosine"}
                )
                self.collections.clear()
                print("✅ Base de datos reiniciada")
            except Exception as e2:
                print(f"❌ Error crítico al reiniciar BD: {e2}")
    
    def get_stats(self):
        """
        Obtiene estadísticas de la base de datos.
        """
        count = self.collection.count()
        
        # Obtener lista de PDFs reales del directorio de uploads
        pdf_list = []
        try:
            # Usar ruta absoluta del directorio pdfs (en el mismo backend)
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            pdfs_dir = os.path.join(backend_dir, "pdfs")
            pdfs_dir = os.path.abspath(pdfs_dir)
            
            print(f"[STATS] Buscando PDFs en: {pdfs_dir}")
            
            if os.path.exists(pdfs_dir):
                pdf_list = sorted([f for f in os.listdir(pdfs_dir) if f.lower().endswith(".pdf")])
                print(f"[STATS] Encontrados {len(pdf_list)} PDFs: {pdf_list}")
            else:
                print(f"[STATS] ⚠️ Directorio no existe: {pdfs_dir}")
        except Exception as e:
            print(f"[STATS] ❌ Error al listar PDFs: {e}")
        
        # Si no hay archivos en el directorio pero sí en memoria, limpiar memoria
        if not pdf_list and self.collections:
            print(f"[STATS] ⚠️ Limpiando {len(self.collections)} colecciones huérfanas de memoria")
            self.collections.clear()
        
        return {
            "total_chunks": count,
            "total_pdfs": len(pdf_list),
            "database_path": self.db_path,
            "embedding_model": self.model_name,
            "pdfs": pdf_list
        }
    
    def retrieve_by_pdf(self, query, pdf_name, k=3):
        """
        Recupera chunks solo del PDF especificado.
        Returns: Lista de tuplas (doc, metadata)
        """
        key = self._find_pdf_key(pdf_name)
        if not key:
            return []

        pdf_collection = self.collections[key]
        query_embedding = self.embedding_model.encode(query).tolist()
        
        try:
            results = pdf_collection.query(
                query_embeddings=[query_embedding],
                n_results=k
            )
            
            if not results or not results["documents"] or not results["documents"][0]:
                return []
            
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            
            return list(zip(docs, metas))
        except Exception as e:
            print(f"❌ Error en búsqueda por PDF: {e}")
            return []
    
    def get_context_by_pdf(self, query, pdf_name, k=3):
        """
        Obtiene contexto formateado solo del PDF especificado.
        Returns: str (context_text)
        """
        results = self.retrieve_by_pdf(query, pdf_name, k)

        if not results:
            return f"No hay información en el archivo: {pdf_name}"
        
        context = f"Información relevante de {pdf_name}:\n\n"
        seen_pages = set()
        
        for i, (doc, meta) in enumerate(results, 1):
            page = meta.get("page")
            context += f"[{i}]"
            if page:
                context += f" (Página: {page})"
            context += f"\n{doc}\n\n"
            
            # Registrar que hemos visto esta página
            if page and page not in seen_pages:
                seen_pages.add(page)
        
        return context

    def get_all_chunks_for_pdf(self, pdf_name, max_chunks=50):
        """
        Recupera TODOS los chunks indexados de un PDF específico.
        Útil para generar mapas conceptuales basados en el contenido procesado por RAG.
        Returns: Lista de strings (texto de cada chunk)
        """
        key = self._find_pdf_key(pdf_name)
        if not key:
            print(f"⚠️ PDF '{pdf_name}' no encontrado en colecciones")
            return []

        pdf_collection = self.collections[key]
        
        try:
            # Get all documents from the collection (no query, just retrieve)
            results = pdf_collection.get(
                limit=max_chunks,
                include=["documents", "metadatas"]
            )
            
            if not results or not results["documents"]:
                return []
            
            return results["documents"]
        except Exception as e:
            print(f"❌ Error obteniendo chunks del PDF: {e}")
            return []

    def delete_pdf(self, pdf_name):
        """
        Elimina un PDF completamente del sistema RAG.
        """
        try:
            key = self._find_pdf_key(pdf_name)
            if not key:
                print(f"⚠️  PDF no encontrado: {pdf_name}")
                return False
            
            # Obtener la colección
            pdf_collection = self.collections.get(key)
            if pdf_collection:
                try:
                    collection_name = self._get_collection_name(key)
                    self.client.delete_collection(name=collection_name)
                    del self.collections[key]
                    print(f"✅ PDF eliminado de ChromaDB: {key}")
                except Exception as e:
                    print(f"⚠️  Error al eliminar colección: {e}")
            
            # Eliminar archivo físico si existe
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            pdfs_dir = os.path.join(backend_dir, "pdfs")
            file_path = os.path.join(pdfs_dir, pdf_name)
            
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"✅ Archivo eliminado: {file_path}")
                except Exception as e:
                    print(f"⚠️  Error al eliminar archivo: {e}")
            
            return True
        except Exception as e:
            print(f"❌ Error al eliminar PDF: {e}")
            return False
    
    def _find_pdf_key(self, pdf_name):
        """Intenta localizar la clave de `self.collections` que corresponde al `pdf_name`.

        Realiza varias estrategias: coincidencia exacta, case-insensitive, sin extensión,
        y búsqueda por substring. Devuelve la clave encontrada o None.
        """
        if not pdf_name:
            return None

        # Si ya existe exacto
        if pdf_name in self.collections:
            return pdf_name

        # Comparar case-insensitive
        lower_name = pdf_name.lower()
        for key in self.collections.keys():
            if key.lower() == lower_name:
                return key

        # Comparar sin extensión
        name_no_ext = Path(pdf_name).stem.lower()
        for key in self.collections.keys():
            if Path(key).stem.lower() == name_no_ext:
                return key

        # Substring match (buscar la key que contiene el nombre o viceversa)
        for key in self.collections.keys():
            if name_no_ext in key.lower() or key.lower() in lower_name:
                return key

        return None
