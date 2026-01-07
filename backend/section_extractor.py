"""
Módulo para extraer y organizar secciones de PDFs académicos.
Divide documentos por secciones (Abstract, Introducción, etc.)
y las indexa por tipo de sección en lugar de por chunks genéricos.
"""

import re
from typing import List, Dict, Tuple, Optional

class SectionExtractor:
    """
    Extrae secciones de PDFs académicos y las organiza de forma estructurada.
    """
    
    # Patrones de secciones reconocidas (multilingües)
    SECTION_PATTERNS = {
        "title": {
            "keywords": ["título", "titulo", "title", "headline", "encabezado"],
            "order": 0
        },
        "abstract": {
            "keywords": ["resumen", "abstract", "summary", "sumario", "resúmen"],
            "order": 1
        },
        "introduction": {
            "keywords": ["introducción", "introduccion", "introduction", "intro", "antecedentes"],
            "order": 2
        },
        "methods": {
            "keywords": ["métodos", "metodos", "methodology", "metodología", "metodologia", "método", "method"],
            "order": 3
        },
        "results": {
            "keywords": ["resultados", "results", "findings", "hallazgos", "resultado"],
            "order": 4
        },
        "discussion": {
            "keywords": ["discusión", "discusion", "discussion", "análisis", "analisis"],
            "order": 5
        },
        "conclusion": {
            "keywords": ["conclusión", "conclusion", "conclusiones", "conclusions", "conclusão"],
            "order": 6
        },
        "references": {
            "keywords": ["referencias", "references", "bibliografía", "bibliografia", "bibliography"],
            "order": 7
        },
        "appendix": {
            "keywords": ["apéndice", "appendix", "anexo", "anexos", "supplement"],
            "order": 8
        }
    }
    
    def __init__(self):
        """Inicializa el extractor de secciones."""
        self.full_text = ""
        self.sections = {}
        
    def extract_sections(self, text: str, pages_data: List[Dict]) -> Dict[str, Dict]:
        """
        Extrae secciones de un documento de texto.
        
        Args:
            text: Texto completo del documento
            pages_data: Lista de dicts con 'text' y 'page'
        
        Returns:
            Dict con estructura {
                'section_type': {
                    'title': str,
                    'content': str,
                    'start_page': int,
                    'end_page': int,
                    'word_count': int,
                    'chunks': List[str]  # Dividido en sub-chunks si es muy grande
                }
            }
        """
        self.full_text = text
        self.sections = {}
        
        # Encontrar todos los headers de sección
        section_markers = self._find_section_markers(text)
        
        if not section_markers:
            # Si no detecta secciones, crear una sola sección "content"
            print("⚠️  No se detectaron secciones. Usando documento como una sola sección.")
            return self._create_default_section(text, pages_data)
        
        # Extraer contenido de cada sección
        for i, (section_type, position, original_title) in enumerate(section_markers):
            # Determinar dónde termina esta sección (donde comienza la siguiente)
            start_pos = position
            if i + 1 < len(section_markers):
                end_pos = section_markers[i + 1][1]
            else:
                end_pos = len(text)
            
            # Extraer contenido
            section_content = text[start_pos:end_pos].strip()
            
            # Remover el título del contenido si está al principio
            section_content = re.sub(
                f"^{re.escape(original_title)}\\s*",
                "",
                section_content,
                flags=re.IGNORECASE
            ).strip()
            
            if section_content:
                # Determinar página (aproximado)
                start_page, end_page = self._find_section_pages(
                    section_content, pages_data, start_pos
                )
                
                # Dividir en chunks si es muy grande (>1000 palabras)
                chunks = self._create_section_chunks(section_content)
                
                self.sections[section_type] = {
                    'title': original_title,
                    'content': section_content,
                    'start_page': start_page,
                    'end_page': end_page,
                    'word_count': len(section_content.split()),
                    'chunks': chunks,
                    'chunk_count': len(chunks)
                }
                
                print(f"✅ Sección '{section_type}' detectada: {len(section_content.split())} palabras, {len(chunks)} chunks")
        
        return self.sections
    
    def _find_section_markers(self, text: str) -> List[Tuple[str, int, str]]:
        """
        Encuentra todas las posiciones de headers de sección en el texto.
        Soporta varios formatos: markdown, headers numerados, etc.
        
        Returns:
            Lista de tuples (section_type, position_in_text, original_title)
            ordenada por posición
        """
        markers = []
        
        for section_type, config in self.SECTION_PATTERNS.items():
            keywords = config['keywords']
            
            for keyword in keywords:
                # Patrón 1: "## Abstract" o "# Abstract" (markdown)
                pattern1 = rf"^#{1,4}\s+{re.escape(keyword)}\s*$"
                
                # Patrón 2: "ABSTRACT" (todo mayúsculas, posiblemente con números)
                pattern2 = rf"^(?:\d+[.\)]?\s*)?{re.escape(keyword.upper())}\s*$"
                
                # Patrón 3: "Abstract:" o "Abstract." (con dos puntos o punto)
                pattern3 = rf"^(?:\d+[.\)]?\s*)?{re.escape(keyword)}\s*[:.]"
                
                # Patrón 4: Palabra sola en línea (sensible al contexto)
                pattern4 = rf"(?:^|\n)\s*({re.escape(keyword)})\s*(?:\n|:|\.|\d+[.\)])"
                
                patterns = [pattern1, pattern2, pattern3, pattern4]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                    
                    for match in matches:
                        # Buscar el título completo (desde el inicio de la línea)
                        line_start = text.rfind('\n', 0, match.start()) + 1
                        line_end = text.find('\n', match.start())
                        if line_end == -1:
                            line_end = len(text)
                        
                        original_title = text[line_start:line_end].strip()
                        
                        if original_title:  # Solo si encontramos un título válido
                            # Usar el inicio del match como posición
                            markers.append((section_type, match.start(), original_title))
        
        # Eliminar duplicados y ordenar por posición
        unique_markers = {}
        for section_type, pos, title in markers:
            # Priorizar por distancia más cercana (primeros matches)
            if pos not in unique_markers or len(title) > len(unique_markers[pos][2]):
                unique_markers[pos] = (section_type, pos, title)
        
        markers = sorted(unique_markers.values(), key=lambda x: x[1])
        return markers
    
    def _find_section_pages(self, section_content: str, pages_data: List[Dict], 
                           start_pos: int) -> Tuple[int, int]:
        """
        Determina las páginas aproximadas donde está la sección.
        """
        if not pages_data:
            return 1, 1
        
        # Búsqueda simple: contar caracteres
        char_count = 0
        start_page = 1
        
        for page_info in pages_data:
            page_text = page_info['text']
            char_count += len(page_text)
            
            if char_count >= start_pos:
                start_page = page_info['page']
                break
        
        # Aproximar página final
        end_page = start_page + max(1, len(section_content.split()) // 300)
        
        return start_page, min(end_page, len(pages_data))
    
    def _create_section_chunks(self, content: str, chunk_size: int = 500, 
                              overlap: int = 50) -> List[str]:
        """
        Divide el contenido de una sección en chunks más pequeños.
        
        Args:
            content: Contenido de la sección
            chunk_size: Palabras por chunk
            overlap: Palabras que se repiten entre chunks
        
        Returns:
            Lista de chunks de texto
        """
        words = content.split()
        if len(words) <= chunk_size:
            return [content]
        
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            if len(chunk.strip()) > 50:  # Ignorar chunks muy pequeños
                chunks.append(chunk)
        
        return chunks
    
    def _create_default_section(self, text: str, pages_data: List[Dict]) -> Dict:
        """
        Crea una sección por defecto cuando no se detectan secciones específicas.
        """
        chunks = self._create_section_chunks(text)
        
        start_page = pages_data[0]['page'] if pages_data else 1
        end_page = pages_data[-1]['page'] if pages_data else 1
        
        return {
            "content": {
                'title': 'Contenido',
                'content': text,
                'start_page': start_page,
                'end_page': end_page,
                'word_count': len(text.split()),
                'chunks': chunks,
                'chunk_count': len(chunks)
            }
        }
    
    def get_section_content(self, section_type: str) -> Optional[str]:
        """Obtiene el contenido completo de una sección."""
        if section_type in self.sections:
            return self.sections[section_type]['content']
        return None
    
    def get_section_summary(self) -> Dict[str, Dict]:
        """
        Retorna un resumen de todas las secciones detectadas.
        """
        summary = {}
        for section_type, data in self.sections.items():
            summary[section_type] = {
                'title': data['title'],
                'word_count': data['word_count'],
                'pages': f"{data['start_page']}-{data['end_page']}",
                'chunks': data['chunk_count']
            }
        return summary
    
    def prepare_for_rag(self) -> List[Tuple[str, Dict]]:
        """
        Prepara los datos de secciones para ser indexados en el RAG.
        
        Returns:
            Lista de tuplas (chunk_text, metadata_dict)
            donde metadata incluye 'section_type', 'page', etc.
        """
        chunks_with_metadata = []
        
        for section_type, section_data in self.sections.items():
            # Usar los chunks pre-divididos de la sección
            for chunk_idx, chunk in enumerate(section_data['chunks']):
                metadata = {
                    'section_type': section_type,
                    'section_title': section_data['title'],
                    'page': section_data['start_page'],
                    'end_page': section_data['end_page'],
                    'chunk_index': chunk_idx,
                    'total_chunks_in_section': len(section_data['chunks'])
                }
                chunks_with_metadata.append((chunk, metadata))
        
        return chunks_with_metadata
