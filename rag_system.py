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
        Extrae texto de un PDF usando PyMuPDF.
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Texto extraído del PDF
        """
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text()
            doc.close()
            print(f"✅ Texto extraído de: {pdf_path}")
            return text
        except Exception as e:
            print(f"❌ Error al extraer PDF {pdf_path}: {e}")
            return None
    
    def chunk_text(self, text, chunk_size=500, overlap=100):
        """
        Divide el texto en chunks más pequeños para mejor recuperación.
        
        Args:
            text: Texto a dividir
            chunk_size: Tamaño de cada chunk (palabras)
            overlap: Solapamiento entre chunks
            
        Returns:
            Lista de chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def add_pdf(self, pdf_path, metadata=None):
        """
        Procesa y agrega un PDF al sistema RAG en su propia colección.
        
        Args:
            pdf_path: Ruta al PDF
            metadata: Información adicional sobre el documento
        """
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return
        
        chunks = self.chunk_text(text)
        
        # Preparar metadata
        if metadata is None:
            metadata = {}
        pdf_name = os.path.basename(pdf_path)
        metadata["source"] = pdf_name
        metadata["pdf_path"] = pdf_path
        
        # Obtener colección específica para este PDF
        pdf_collection = self._get_or_create_pdf_collection(pdf_name)
        
        # Generar embeddings y agregar a la colección del PDF
        for i, chunk in enumerate(chunks):
            try:
                embedding = self.embedding_model.encode(chunk).tolist()
                chunk_id = f"chunk_{i}"
                
                # Agregar a la colección específica del PDF
                pdf_collection.add(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[metadata]
                )
                
                # También agregar a la colección principal para búsquedas globales
                self.collection.add(
                    ids=[f"{pdf_name}_{i}"],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[metadata]
                )
            except Exception as e:
                print(f"❌ Error al procesar chunk {i}: {e}")
        
        print(f"✅ PDF procesado: {pdf_name} - {len(chunks)} chunks agregados")
    
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
        
        Args:
            query: Pregunta del usuario
            k: Número de resultados a devolver
            
        Returns:
            Lista de chunks relevantes
        """
        # Generar embedding de la consulta
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Buscar en ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        if not results or not results["documents"] or not results["documents"][0]:
            return []
        
        return results["documents"][0]
    
    def get_context(self, query, k=3):
        """
        Obtiene el contexto formateado para el modelo.
        
        Args:
            query: Pregunta del usuario
            k: Número de documentos relevantes
            
        Returns:
            String con el contexto formateado
        """
        docs = self.retrieve(query, k)
        
        if not docs:
            return "No hay información en la base de datos."
        
        context = "Información relevante de los documentos:\n\n"
        for i, doc in enumerate(docs, 1):
            context += f"[{i}] {doc}\n\n"
        
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
        
        Args:
            query: Pregunta del usuario
            pdf_name: Nombre del PDF a buscar
            k: Número de resultados
            
        Returns:
            Lista de chunks del PDF especificado
        """
        # Intentar localizar la clave de la colección del PDF de forma robusta
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
            
            return results["documents"][0]
        except Exception as e:
            print(f"❌ Error en búsqueda por PDF: {e}")
            return []
    
    def get_context_by_pdf(self, query, pdf_name, k=3):
        """
        Obtiene contexto formateado solo del PDF especificado.
        
        Args:
            query: Pregunta del usuario
            pdf_name: Nombre del PDF
            k: Número de documentos
            
        Returns:
            String con contexto formateado
        """
        docs = self.retrieve_by_pdf(query, pdf_name, k)

        if not docs:
            return f"No hay información en el archivo: {pdf_name}"
        
        context = f"Información relevante de {pdf_name}:\n\n"
        for i, doc in enumerate(docs, 1):
            context += f"[{i}] {doc}\n\n"
        
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
