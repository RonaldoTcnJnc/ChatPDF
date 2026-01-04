import { useEffect, useState } from 'react';
import { FileText, Database, Layers, Trash2 } from 'lucide-react';
import axios from 'axios';
import type { Stats } from '../types';

interface FileListProps {
    refreshTrigger: number;
    onFileSelect: (filename: string | null) => void;
    selectedFile: string | null;
    onDeleteSuccess?: () => void; // Optional prop to trigger refresh from parent if needed
}

export default function FileList({ refreshTrigger, onFileSelect, selectedFile }: FileListProps) {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchStats();
    }, [refreshTrigger]);

    const fetchStats = async () => {
        try {
            const response = await axios.get<Stats>('/api/stats');
            setStats(response.data);
        } catch (error) {
            console.error('Error fetching stats:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (filename: string) => {
        if (!confirm(`¿Estás seguro de eliminar ${filename}? Esta acción no se puede deshacer.`)) return;

        try {
            await axios.delete(`/api/files/${filename}`);
            if (selectedFile === filename) {
                onFileSelect(null);
            }
            fetchStats();
        } catch (error) {
            console.error('Error deleting file:', error);
            alert('Error al eliminar el archivo');
        }
    };

    if (loading) {
        return (
            <div className="file-list">
                <h3>📚 Documentos</h3>
                <p className="loading-text">Cargando...</p>
            </div>
        );
    }

    return (
        <div className="file-list">
            <h3>📚 Documentos</h3>

            {stats && (
                <div className="stats-summary">
                    <div className="stat-item">
                        <Database size={16} />
                        <span>{stats.total_chunks} chunks</span>
                    </div>
                    <div className="stat-item">
                        <Layers size={16} />
                        <span>{stats.embedding_model}</span>
                    </div>
                </div>
            )}

            <div className="files-container">
                {stats?.pdfs && stats.pdfs.length > 0 ? (
                    <>
                        <button
                            className={`file-item ${selectedFile === null ? 'selected' : ''}`}
                            onClick={() => onFileSelect(null)}
                        >
                            <FileText size={18} />
                            <span>Todos los documentos</span>
                        </button>

                        {stats.pdfs.map((filename) => (
                            <div key={filename} className={`file-row ${selectedFile === filename ? 'selected' : ''}`}>
                                <button
                                    className="file-select-btn"
                                    onClick={() => onFileSelect(filename)}
                                >
                                    <FileText size={18} />
                                    <span>{filename}</span>
                                </button>
                                <button
                                    className="file-delete-btn"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDelete(filename);
                                    }}
                                    title="Eliminar archivo"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                    </>
                ) : (
                    <p className="no-files">No hay documentos cargados</p>
                )}
            </div>
        </div>
    );
}
