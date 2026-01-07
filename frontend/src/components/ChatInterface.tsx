import { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Loader2, Bot, User, Volume2, Square, Mic, MicOff } from 'lucide-react';
import axios from 'axios';
import type { Message, ChatRequest, ChatResponse } from '../types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatInterfaceProps {
    selectedFile: string | null;
    useRAG: boolean;
}

export default function ChatInterface({ selectedFile, useRAG }: ChatInterfaceProps) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [speakingMessageId, setSpeakingMessageId] = useState<number | null>(null);
    const [isListening, setIsListening] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // --- Audio Logic (TTS) ---
    const stopSpeaking = () => {
        window.speechSynthesis.cancel();
        setSpeakingMessageId(null);
    };

    const speakMessage = (text: string, index: number) => {
        if (speakingMessageId === index) {
            stopSpeaking();
            return;
        }

        stopSpeaking();
        setSpeakingMessageId(index);

        // Limpiar Markdown para lectura fluida
        const cleanText = text
            .replace(/\*\*/g, '')          // Negritas
            .replace(/\*/g, '')            // Cursivas
            .replace(/#{1,6}\s?/g, '')     // Encabezados
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Links: dejar texto
            .replace(/!\[[^\]]*\]\([^)]+\)/g, ' Imagen: ') // Imágenes
            .replace(/```[\s\S]*?```/g, ' fragmento de código ') // Bloques de código
            .replace(/`[^`]*`/g, ' código ') // Código en línea
            .replace(/>\s?/g, '')          // Blockquotes
            .trim();

        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'es-ES';

        utterance.onend = () => setSpeakingMessageId(null);
        utterance.onerror = () => setSpeakingMessageId(null);

        window.speechSynthesis.speak(utterance);
    };

    // --- Dictation Logic (Server-Side using Gemini) ---
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                await transcribeAudio(audioBlob);

                // Detener tracks para liberar microfono
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsListening(true);
            console.log("🎤 Grabación iniciada");
        } catch (error) {
            console.error("Error al acceder al micrófono:", error);
            alert("No se pudo acceder al micrófono. Verifica los permisos.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isListening) {
            mediaRecorderRef.current.stop();
            setIsListening(false);
            console.log("🎤 Grabación detenida, procesando...");
        }
    };

    const toggleListening = () => {
        if (isListening) {
            stopRecording();
        } else {
            startRecording();
        }
    };




    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        adjustTextareaHeight();
    }, [input]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const adjustTextareaHeight = () => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
        }
    };

    const sendMessage = async (textOverride?: string) => {
        const textToSend = typeof textOverride === 'string' ? textOverride : input;

        if (!textToSend.trim() || isLoading) return;

        const userMessage: Message = {
            role: 'user',
            content: textToSend.trim(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            const request: ChatRequest = {
                message: userMessage.content,
                pdf_name: selectedFile || undefined,
                use_rag: useRAG,
            };

            const response = await axios.post<ChatResponse>('/api/chat', request);

            const botMessage: Message = {
                role: 'assistant',
                content: response.data.response,
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('Chat error:', error);
            const errorMessage: Message = {
                role: 'assistant',
                content: '❌ Error al obtener respuesta. Verifica que el backend esté corriendo.',
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    // ... (helper functions)

    const transcribeAudio = async (audioBlob: Blob) => {
        setIsLoading(true); // Mostrar loading mientras transcribe
        try {
            const formData = new FormData();
            formData.append('file', audioBlob, 'recording.webm');

            const response = await axios.post('/api/transcribe', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            if (response.data.text) {
                const text = response.data.text;
                // Combinar con texto existente si lo hay
                const finalText = input ? `${input} ${text}` : text;

                // Actualizar input visualmente (opcional, pero se borrará al enviar)
                setInput(finalText);

                // Enviar automáticamente
                console.log("🚀 Enviando automáticamente:", finalText);
                await sendMessage(finalText);
            }
        } catch (error) {
            console.error("Error en transcripción:", error);
            alert("Error al transcribir el audio.");
            setIsLoading(false); // Solo quitar loading si falló, si tuvo éxito sendMessage lo maneja
        }
        // Nota: No poner setIsLoading(false) en finally aquí porque sendMessage ya pone isLoading=true
        // y si lo apagamos aquí, podría parpadear o cancelar el estado de carga del chat.
        // Solo apagamos si NO llamamos a sendMessage.
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const clearHistory = () => {
        setMessages([]);
    };

    return (
        <div className="chat-interface">
            <div className="chat-header">
                <h2>💬 Chat con RAG</h2>
                <div className="header-actions">
                    {speakingMessageId !== null && (
                        <button onClick={stopSpeaking} className="clear-btn stop-btn" title="Detener audio">
                            <Square size={18} fill="currentColor" />
                        </button>
                    )}
                    <button onClick={clearHistory} className="clear-btn" title="Limpiar historial">
                        <Trash2 size={18} />
                    </button>
                </div>
            </div>

            <div className="chat-info">
                <span className="info-badge">
                    {useRAG ? '📚 RAG Activado' : '🔇 RAG Desactivado'}
                </span>
                {selectedFile && (
                    <span className="info-badge">
                        📄 {selectedFile}
                    </span>
                )}
            </div>

            <div className="messages-container">
                {messages.length === 0 ? (
                    <div className="empty-state">
                        <Bot size={64} className="empty-icon" />
                        <h3>¡Hola! 👋</h3>
                        <p>Sube un PDF y hazme preguntas sobre su contenido</p>
                    </div>
                ) : (
                    messages.map((msg, idx) => (
                        <div key={idx} className={`message ${msg.role}`}>
                            <div className="message-icon">
                                {msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
                            </div>
                            <div className="message-content">
                                <div className="message-text">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        components={{
                                            img: ({ node, ...props }) => (
                                                <img
                                                    style={{ maxWidth: '100%', borderRadius: '8px', marginTop: '10px' }}
                                                    {...props}
                                                />
                                            )
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                                {msg.role === 'assistant' && (
                                    <button
                                        onClick={() => speakMessage(msg.content, idx)}
                                        className={`speak-btn ${speakingMessageId === idx ? 'speaking' : ''}`}
                                        title={speakingMessageId === idx ? "Detener" : "Leer en voz alta"}
                                    >
                                        {speakingMessageId === idx ? <Square size={14} /> : <Volume2 size={14} />}
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}

                {isLoading && (
                    <div className="message assistant loading">
                        <div className="message-icon">
                            <Bot size={20} />
                        </div>
                        <div className="message-content">
                            <Loader2 className="spinning" size={20} />
                            <span>Pensando...</span>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={isListening ? "Escuchando..." : "Escribe tu mensaje..."}
                    rows={1}
                    disabled={isLoading}
                />

                <button
                    onClick={toggleListening}
                    disabled={isLoading}
                    className={`icon-btn mic-btn ${isListening ? 'listening' : ''}`}
                    title="Dictar por voz"
                >
                    {isListening ? <MicOff size={20} /> : <Mic size={20} />}
                </button>

                <button
                    onClick={() => sendMessage()}
                    disabled={!input.trim() || isLoading}
                    className="send-btn"
                >
                    <Send size={20} />
                </button>
            </div>
        </div>
    );
}
