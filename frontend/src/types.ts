// Type definitions for the ChatBot application

export interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export interface ChatRequest {
    message: string;
    pdf_name?: string;
    use_rag: boolean;
}

export interface ChatResponse {
    response: string;
    sources?: Record<string, any>[];
    sender: string;
}

export interface FileInfo {
    name: string;
    chunks?: number;
}

export interface UploadResponse {
    filename: string;
    status: string;
    chunks: number;
}

export interface Stats {
    total_chunks: number;
    embedding_model: string;
    database_path: string;
    pdfs?: string[];
}

export interface SystemStatus {
    status: string;
    provider: string;
    model: string;
}
