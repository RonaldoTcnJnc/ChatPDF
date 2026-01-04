import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

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
        
        # Cargar modelo de embeddings
        self.embedding_model = SentenceTransformer(model_name)
        
        # Diccionario para almacenar colecciones por PDF
        self.collections = {}
        
        # Colección principal para búsquedas globales
        self.collection = self.client.get_or_create_collection(
            name="papers",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Cargar colecciones existentes
        self._load_existing_collections()
        
        print(f"✅ RAG inicializado con ChromaDB en: {db_path}")
    
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
        # ChromaDB requiere nombres: 3-512 chars, [a-zA-Z0-9._-], sin espacios ni caracteres especiales
        import hashlib
        # Crear un hash único del nombre del PDF
        hash_value = hashlib.md5(pdf_name.encode()).hexdigest()[:8]
        # Usar solo caracteres válidos
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in pdf_name.lower())
        # Limitar longitud y asegurar que empiece y termine con carácter válido
        safe_name = safe_name[:50].rstrip("_").rstrip(".").rstrip("-")
        collection_name = f"pdf_{hash_value}_{safe_name}"[:60]
        return collection_name
    
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
        Extrae texto de un PDF usando PyMuPDF, intentando detectar secciones.
        """
        if not os.path.exists(pdf_path):
            return ""

        import re

        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            
            # Preparar carpeta de imágenes para este PDF
            pdf_name = os.path.basename(pdf_path)
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in pdf_name)
            images_dir = os.path.join(os.path.dirname(self.db_path), "static", "images", safe_name)
            
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)

            # Patrones comunes de encabezados (Español e Inglés)
            header_patterns = [
                r"^(?:\d+\.?\s*)?(?:abstract|resumen)\s*$",
                r"^(?:\d+\.?\s*)?(?:keywords|palabras\s*clave)\s*$",
                r"^(?:\d+\.?\s*)?(?:introduction|introducci[oó]n)\s*$",
                r"^(?:\d+\.?\s*)?(?:background|antecedentes)\s*$",
                r"^(?:\d+\.?\s*)?(?:literature\s*review|revisi[oó]n\s*literaria)\s*$",
                r"^(?:\d+\.?\s*)?(?:methodology|methods|metodolog[ií]a|material(?:s)?\s*(?:and|&|y)\s*method(?:s)?|material(?:es)?\s*y\s*m[eé]todos)\s*$",
                r"^(?:\d+\.?\s*)?(?:results|resultados|hallazgos)\s*$",
                r"^(?:\d+\.?\s*)?(?:discussion|discusi[oó]n)\s*$",
                r"^(?:\d+\.?\s*)?(?:conclusions?|conclusiones)\s*$",
                r"^(?:\d+\.?\s*)?(?:acknowledg(?:e)?ments?|agradecimientos)\s*$",
                r"^(?:\d+\.?\s*)?(?:references|referencias|bibliograf[ií]a)\s*$",
                r"^(?:\d+\.?\s*)?(?:appendices|appendix|ap[eé]ndices?|anexos?|supplementary\s*material|material\s*suplementario)\s*$"
            ]
                
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Obtener bloques de texto para analizar estructura
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            line_text = "".join([span["text"] for span in line["spans"]]).strip()
                            
                            # Comprobar si es un encabezado
                            is_header = False
                            for pattern in header_patterns:
                                if re.match(pattern, line_text, re.IGNORECASE):
                                    # Normalizar nombre de sección (quitar números, mayúsculas)
                                    clean_section = re.sub(r"^\d+\.?\s*", "", line_text).capitalize()
                                    text += f"\n\n[[SECTION: {clean_section}]]\n\n"
                                    is_header = True
                                    break
                            
                            if not is_header:
                                text += line_text + " "
                        text += "\n"

                # Extraer imágenes (código existente)
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        image_filename = f"page_{page_num+1}_img_{img_index+1}.{image_ext}"
                        image_path = os.path.join(images_dir, image_filename)
                        
                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)
                            
                        img_url = f"/static/images/{safe_name}/{image_filename}"
                        text += f"\n\n![Imagen de página {page_num+1}]({img_url})\n\n"
                    except:
                        pass

            doc.close()
            print(f"✅ Texto estructurado extraído de: {pdf_path}")
            return text
        except Exception as e:
            print(f"❌ Error al extraer PDF {pdf_path}: {e}")
            return None


    def chunk_text(self, text, chunk_size=250, overlap=50):
        """
        Divide el texto en chunks y detecta metadatos de sección.
        Returns: Lista de tuplas (chunk_text, section_metadata_dict)
        """
        import re
        
        # Regex para encontrar marcadores de sección inyectados
        section_regex = r"\[\[SECTION: (.*?)\]\]"
        
        # Segmentar por marcadores primero para asignar secciones
        # Esto es simple: recorremos y mantenemos "current_section"
        
        words = []
        # Pre-procesar para dividir texto y marcadores. 
        # Tokenización básica manteniendo los marcadores intactos es difícil con split simple.
        # Usaremos iteración.
        
        current_section = "General"
        chunks_with_metadata = []
        
        # Dividir por marcadores de sección
        parts = re.split(section_regex, text)
        
        # parts[0] es texto pre-seccion (General). 
        # parts[1] es nombre sección 1. parts[2] es contenido sección 1.
        # parts[3] es nombre sección 2. parts[4] es contenido sección 2...
        
        # Procesar parte inicial (General)
        if parts[0].strip():
            current_words = parts[0].split()
            for i in range(0, len(current_words), chunk_size - overlap):
                chunk = " ".join(current_words[i:i + chunk_size])
                if chunk.strip():
                    chunks_with_metadata.append((chunk, {"section": "General"}))
        
        # Procesar resto
        for i in range(1, len(parts), 2):
            section_name = parts[i].strip()
            section_content = parts[i+1]
            
            section_words = section_content.split()
            if not section_words:
                continue
                
            for j in range(0, len(section_words), chunk_size - overlap):
                chunk = " ".join(section_words[j:j + chunk_size])
                if chunk.strip():
                    chunks_with_metadata.append((chunk, {"section": section_name}))
        
        return chunks_with_metadata
    
    def add_pdf(self, pdf_path, metadata=None):
        """
        Procesa y agrega un PDF al sistema RAG en su propia colección.
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return
        
        # chunk_text ahora devuelve lista de (texto, metadatos_seccion)
        chunks_data = self.chunk_text(text)
        
        # Preparar metadata base
        if metadata is None:
            metadata = {}
        pdf_name = os.path.basename(pdf_path)
        metadata["source"] = pdf_name
        metadata["pdf_path"] = pdf_path
        
        pdf_collection = self._get_or_create_pdf_collection(pdf_name)
        
        for i, (chunk, section_meta) in enumerate(chunks_data):
            try:
                embedding = self.embedding_model.encode(chunk).tolist()
                chunk_id = f"chunk_{i}"
                
                # Combinar metadata base con metadata de sección
                full_metadata = metadata.copy()
                full_metadata.update(section_meta) # Añade 'section': 'Introducción', etc.
                
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
        """
        results = self.retrieve(query, k)
        
        if not results:
            return "No hay información en la base de datos."
        
        context = "Información relevante de los documentos:\n\n"
        for i, (doc, meta) in enumerate(results, 1):
            source = meta.get("source", "Desconocido")
            section = meta.get("section", "General")
            context += f"[{i}] (Fuente: {source} | Sección: {section})\n{doc}\n\n"
        
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
        pdf_count = len(self.collections)
        return {
            "total_chunks": count,
            "total_pdfs": pdf_count,
            "database_path": self.db_path,
            "embedding_model": self.model_name,
            "pdfs": list(self.collections.keys())
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
        """
        results = self.retrieve_by_pdf(query, pdf_name, k)

        if not results:
            return f"No hay información en el archivo: {pdf_name}"
        
        context = f"Información relevante de {pdf_name}:\n\n"
        for i, (doc, meta) in enumerate(results, 1):
            section = meta.get("section", "General")
            context += f"[{i}] (Sección: {section})\n{doc}\n\n"
        
        return context

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
