import { useState, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { Search, ChevronLeft, ChevronRight, X } from 'lucide-react';
import axios from 'axios';

// Configure worker for Vite
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

interface SearchResult {
    page: number;
    text: string;
    rect: number[];
}

interface DocumentViewerProps {
    file: string | null;
    onClose: () => void;
}

export default function DocumentViewer({ file, onClose }: DocumentViewerProps) {
    const [numPages, setNumPages] = useState<number>(0);
    const [pageNumber, setPageNumber] = useState<number>(1);
    const [scale, setScale] = useState(1.0);
    const [error, setError] = useState<string | null>(null);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    const [query, setQuery] = useState('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [showResults, setShowResults] = useState(false);

    useEffect(() => {
        setPageNumber(1);
        setSearchResults([]);
        setQuery('');
        setError(null);
        setPdfUrl(null);
        setLoading(true);

        // Cargar el PDF desde el backend
        if (file) {
            const pdfPath = `http://localhost:8000/pdfs/${file}`;
            setPdfUrl(pdfPath);
            setLoading(false);
        }
    }, [file]);

    function onDocumentLoadSuccess({ numPages }: { numPages: number }): void {
        setNumPages(numPages);
        setError(null);
    }

    function onDocumentLoadError(error: Error): void {
        console.error("PDF load error:", error);
        const errorMessage = error.message || 'Estructura PDF inválida';
        
        // Si es un error 404, el archivo no existe
        if (errorMessage.includes('404')) {
            setError(`El archivo PDF no existe en el servidor. Por favor, carga nuevamente el PDF.`);
        } else if (errorMessage.includes('Invalid PDF')) {
            setError(`Error: El archivo no es un PDF válido`);
        } else {
            setError(`Error al cargar el PDF: ${errorMessage}`);
        }
    }

    const handleSearch = async () => {
        if (!query.trim() || !file) return;

        // Limpiar resaltados anteriores
        const marks = document.querySelectorAll('mark');
        marks.forEach(mark => {
            const parent = mark.parentNode;
            while (mark.firstChild) {
                parent?.insertBefore(mark.firstChild, mark);
            }
            parent?.removeChild(mark);
        });

        setIsSearching(true);
        try {
            const response = await axios.post('/api/pdf/search', {
                pdf_name: file,
                query: query
            });
            setSearchResults(response.data);
            setShowResults(true);
            
            // Resaltar en la página actual después de los resultados
            setTimeout(() => {
                highlightSearchTerm();
            }, 100);
        } catch (error) {
            console.error("Search failed", error);
            alert("Error en la búsqueda");
        } finally {
            setIsSearching(false);
        }
    };

    const handleResultClick = (page: number) => {
        setPageNumber(page);
        // Desplazarse al resultado usando la palabra de búsqueda
        setTimeout(() => {
            highlightSearchTerm();
        }, 100);
    };

    const highlightSearchTerm = () => {
        if (!query.trim()) return;
        
        // Buscar y resaltar la palabra en el texto visible del PDF
        const textLayer = document.querySelector('.react-pdf__Page__textContent');
        if (textLayer) {
            const walker = document.createTreeWalker(
                textLayer,
                NodeFilter.SHOW_TEXT,
                null,
                false
            );

            const nodesToReplace: { node: Node; regex: RegExp }[] = [];
            let currentNode;
            const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');

            while ((currentNode = walker.nextNode())) {
                if (regex.test(currentNode.textContent || '')) {
                    nodesToReplace.push({ node: currentNode, regex });
                }
            }

            nodesToReplace.forEach(({ node, regex }) => {
                const span = document.createElement('span');
                const parts = (node.textContent || '').split(regex);
                parts.forEach((part, idx) => {
                    if (regex.test(part)) {
                        const mark = document.createElement('mark');
                        mark.style.backgroundColor = 'yellow';
                        mark.style.textDecoration = 'underline';
                        mark.style.color = 'black';
                        mark.textContent = part;
                        span.appendChild(mark);
                    } else {
                        span.appendChild(document.createTextNode(part));
                    }
                });
                node.parentNode?.replaceChild(span, node);
            });
        }
    };

    if (!file) return null;

    return (
        <div className="document-viewer-container" style={{ display: 'flex', height: '100%', position: 'relative', overflow: 'hidden', minWidth: 0 }}>
            {/* Sidebar de Búsqueda */}
            <div className={`viewer-sidebar ${showResults ? 'open' : ''}`} style={{
                width: showResults ? '300px' : '0',
                minWidth: 0,
                overflow: 'hidden',
                transition: 'width 0.3s',
                borderRight: '1px solid var(--border-color)',
                background: 'var(--bg-secondary)',
                display: 'flex',
                flexDirection: 'column',
                flexShrink: 0
            }}>
                <div style={{ padding: '10px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ color: 'var(--text-primary)', margin: 0 }}>Resultados</h3>
                    <button onClick={() => setShowResults(false)} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}><X size={16} /></button>
                </div>
                <div style={{ padding: '10px', overflowY: 'auto', flex: 1 }}>
                    {searchResults.length === 0 && <p style={{ color: 'var(--text-secondary)' }}>No hay resultados.</p>}
                    {searchResults.map((result, idx) => (
                        <div
                            key={idx}
                            onClick={() => handleResultClick(result.page)}
                            style={{
                                padding: '10px',
                                borderBottom: '1px solid var(--border-color)',
                                cursor: 'pointer',
                                background: result.page === pageNumber ? 'rgba(99, 102, 241, 0.2)' : 'transparent',
                                color: 'var(--text-primary)'
                            }}
                        >
                            <div style={{ fontWeight: 'bold', fontSize: '0.9em' }}>Página {result.page}</div>
                            <div style={{ fontSize: '0.8em', color: 'var(--text-secondary)' }}>"{result.text}"</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Viewer */}
            <div className="viewer-main" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                {/* Toolbar */}
                <div className="viewer-toolbar" style={{
                    padding: '10px',
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    borderBottom: '1px solid var(--border-color)'
                }}>
                    <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
                        <ChevronLeft /> Volver
                    </button>

                    <div style={{ flex: 1 }}></div>

                    <div className="search-box" style={{ display: 'flex', alignItems: 'center', background: 'var(--bg-primary)', borderRadius: '4px', padding: '2px 5px', border: '1px solid var(--border-color)' }}>
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            placeholder="Buscar..."
                            style={{ border: 'none', outline: 'none', padding: '5px', background: 'transparent', color: 'var(--text-primary)' }}
                        />
                        <button onClick={handleSearch} disabled={isSearching} style={{ border: 'none', background: 'transparent', cursor: 'pointer' }}>
                            <Search size={16} color="var(--text-secondary)" />
                        </button>
                    </div>

                    <button onClick={() => setShowResults(!showResults)} style={{ marginLeft: '10px', color: 'var(--text-primary)', background: 'transparent', border: 'none', cursor: 'pointer' }}>
                        {searchResults.length} Resultados
                    </button>

                    <div style={{ borderLeft: '1px solid var(--border-color)', height: '20px', margin: '0 10px' }}></div>

                    <button onClick={() => setScale(s => Math.max(0.5, s - 0.1))} title="Zoom Out" style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer' }}> - </button>
                    <span style={{ fontSize: '0.8em' }}>{Math.round(scale * 100)}%</span>
                    <button onClick={() => setScale(s => Math.min(2.0, s + 0.1))} title="Zoom In" style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer' }}> + </button>

                    <div style={{ borderLeft: '1px solid #666', height: '20px', margin: '0 10px' }}></div>

                    <button disabled={pageNumber <= 1} onClick={() => setPageNumber(prev => prev - 1)}>
                        <ChevronLeft size={20} />
                    </button>
                    <span>Page {pageNumber} of {numPages}</span>
                    <button disabled={pageNumber >= numPages} onClick={() => setPageNumber(prev => prev + 1)}>
                        <ChevronRight size={20} />
                    </button>
                </div>

                {/* PDF Rendering Area */}
                <div style={{
                    flex: 1,
                    background: '#525659',
                    overflow: 'auto',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '20px'
                }}>
                    {error ? (
                        <div style={{
                            color: '#ff6b6b',
                            textAlign: 'center',
                            padding: '20px',
                            background: 'rgba(255, 107, 107, 0.1)',
                            borderRadius: '8px',
                            border: '1px solid #ff6b6b'
                        }}>
                            <p style={{ fontWeight: 'bold' }}>Error al cargar PDF</p>
                            <p style={{ fontSize: '0.9em' }}>{error}</p>
                            <p style={{ fontSize: '0.85em', color: '#aaa' }}>Verifica que el archivo existe y es un PDF válido</p>
                        </div>
                    ) : loading ? (
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            height: '100%'
                        }}>
                            <p>Cargando PDF...</p>
                        </div>
                    ) : pdfUrl ? (
                        <Document
                            file={pdfUrl}
                            onLoadSuccess={onDocumentLoadSuccess}
                            onLoadError={onDocumentLoadError}
                            onItemClick={({ pageNumber }) => setPageNumber(pageNumber)}
                        >
                            <Page pageNumber={pageNumber} scale={scale}>
                                {searchResults
                                    .filter(r => r.page === pageNumber)
                                    .map((result, idx) => {
                                        if (!result.rect) return null;
                                        const [x0, y0, x1, y1] = result.rect;
                                        return (
                                            <div
                                                key={idx}
                                                style={{
                                                    position: 'absolute',
                                                    left: x0 * scale,
                                                    top: y0 * scale,
                                                    width: (x1 - x0) * scale,
                                                    height: (y1 - y0) * scale,
                                                    backgroundColor: 'rgba(255, 255, 0, 0.4)',
                                                    border: '1px solid rgba(255, 165, 0, 0.8)',
                                                    pointerEvents: 'none'
                                                }}
                                            />
                                        );
                                    })
                                }
                            </Page>
                        </Document>
                    ) : null
                }
                </div>
            </div>
        </div>
    );
}
