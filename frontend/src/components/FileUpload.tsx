import { useState, useRef } from 'react';
import { Upload, FileText, Loader2 } from 'lucide-react';
import axios from 'axios';
import type { UploadResponse } from '../types';

interface FileUploadProps {
    onUploadSuccess: () => void;
}

export default function FileUpload({ onUploadSuccess }: FileUploadProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<string>('');
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        const pdfFile = files.find(file => file.name.endsWith('.pdf'));

        if (pdfFile) {
            await uploadFile(pdfFile);
        } else {
            setUploadStatus('❌ Solo se permiten archivos PDF');
            setTimeout(() => setUploadStatus(''), 3000);
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            await uploadFile(file);
        }
    };

    const uploadFile = async (file: File) => {
        setIsUploading(true);
        setUploadStatus('⏳ Subiendo archivo...');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post<UploadResponse>('/api/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            setUploadStatus(`✅ ${response.data.filename} cargado (${response.data.chunks} chunks)`);
            onUploadSuccess();

            setTimeout(() => setUploadStatus(''), 5000);
        } catch (error) {
            console.error('Upload error:', error);
            setUploadStatus('❌ Error al cargar el archivo');
            setTimeout(() => setUploadStatus(''), 5000);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <div className="file-upload-container">
            <div
                className={`drop-zone ${isDragging ? 'dragging' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                />

                {isUploading ? (
                    <Loader2 className="icon spinning" size={48} />
                ) : (
                    <Upload className="icon" size={48} />
                )}

                <h3>Cargar PDF</h3>
                <p>Arrastra un archivo o haz clic para seleccionar</p>
                <FileText className="file-icon" size={24} />
            </div>

            {uploadStatus && (
                <div className={`upload-status ${uploadStatus.includes('✅') ? 'success' : uploadStatus.includes('❌') ? 'error' : ''}`}>
                    {uploadStatus}
                </div>
            )}
        </div>
    );
}
