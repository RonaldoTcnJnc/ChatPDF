import { useState, useEffect } from 'react';
import { Bot, Settings, ChevronLeft, ChevronRight } from 'lucide-react';
import FileUpload from './components/FileUpload';
import FileList from './components/FileList';
import ChatInterface from './components/ChatInterface';
import axios from 'axios';
import type { SystemStatus } from './types';
import './App.css';

/* New Components */
import DocumentViewer from './components/DocumentViewer';
import MindMapViewer from './components/MindMapViewer';
import { MessageSquare, FileText, Network } from 'lucide-react';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  // View Mode State
  // Removed 'chat' mode as per user request
  const [viewMode, setViewMode] = useState<'document' | 'mindmap'>('document');

  // Layout State (Collapsible Panels)
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(true);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

  // Reset view to document when file changes
  useEffect(() => {
    if (selectedFile) setViewMode('document');
  }, [selectedFile]);

  const fetchSystemStatus = async () => {
    try {
      const response = await axios.get<SystemStatus>('/api/');
      setSystemStatus(response.data);
    } catch (error) {
      console.error('Error fetching system status:', error);
    }
  };

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  const toggleProvider = async (newProvider: string) => {
    try {
      const response = await axios.post('/api/provider', { provider: newProvider });
      if (response.data.status === 'success') {
        setSystemStatus(prev => prev ? { ...prev, provider: response.data.provider, model: response.data.model } : null);
      }
    } catch (error) {
      console.error('Error switching provider:', error);
      alert('Error al cambiar de proveedor. Verifica que el backend esté corriendo.');
    }
  };

  return (
    <div className="app">
      <CollapsibleSidebar isOpen={isSidebarOpen} onToggle={() => setIsSidebarOpen(!isSidebarOpen)}>
        <div className="sidebar-header">
          <Bot size={32} />
          <h1>ChatPDF</h1>
        </div>

        <FileUpload onUploadSuccess={handleUploadSuccess} />

        <FileList
          refreshTrigger={refreshTrigger}
          onFileSelect={(file) => {
            setSelectedFile(file);
            // Default to document view on selection if not already active
            if (viewMode !== 'document' && viewMode !== 'mindmap') setViewMode('document');
          }}
          selectedFile={selectedFile}
        />

        {/* View Mode Switcher (Visible only if file selected) */}
        {selectedFile && (
          <div style={{ margin: '10px', display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#666' }}>MODO VISTA</div>
            <div style={{ display: 'flex', gap: '5px' }}>
              <button
                onClick={() => setViewMode('document')}
                title="Ver Documento"
                style={{ flex: 1, padding: '8px', background: viewMode === 'document' ? '#007bff' : '#ddd', color: viewMode === 'document' ? 'white' : 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', justifyContent: 'center' }}
              >
                <FileText size={18} />
                <span style={{ marginLeft: '8px', fontSize: '0.9rem' }}>Documento</span>
              </button>
              <button
                onClick={() => setViewMode('mindmap')}
                title="Mapa Conceptual"
                style={{ flex: 1, padding: '8px', background: viewMode === 'mindmap' ? '#007bff' : '#ddd', color: viewMode === 'mindmap' ? 'white' : 'black', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', justifyContent: 'center' }}
              >
                <Network size={18} />
                <span style={{ marginLeft: '8px', fontSize: '0.9rem' }}>Mapa</span>
              </button>
            </div>
          </div>
        )}

        <div className="settings">
          <div className="settings-header">
            <Settings size={18} />
            <span>Configuración</span>
          </div>

          {systemStatus && (
            <div className="system-info">
              <div className="info-row">
                <span className="label">Proveedor:</span>
                <select
                  value={systemStatus.provider}
                  onChange={(e) => toggleProvider(e.target.value)}
                  className="provider-select"
                >
                  <option value="gemini">Gemini (Cloud)</option>
                  <option value="local">Local (LMStudio)</option>
                </select>
              </div>
              <div className="info-row">
                <span className="label">Modelo:</span>
                <span className="value" title={systemStatus.model}>{systemStatus.model.substring(0, 15)}...</span>
              </div>
            </div>
          )}
        </div>
      </CollapsibleSidebar>

      <main className="main-content">
        {selectedFile ? (
          <div style={{ display: 'flex', flexDirection: 'row', width: '100%', height: '100%', overflow: 'hidden' }}>
            {/* Left Pane: Document or MindMap (only shows when not in 'chat' mode) */}
            <div style={{ flex: '1', minWidth: 0, height: '100%', overflow: 'hidden', borderRight: '1px solid var(--border-color)', position: 'relative' }}>
              {viewMode === 'document' && <DocumentViewer file={selectedFile} onClose={() => { }} />}
              {viewMode === 'mindmap' && <MindMapViewer pdfName={selectedFile} onClose={() => { }} />}
            </div>

            {/* Right Pane: Chat (Collapsible) */}
            <CollapsibleChatPane
              isOpen={isChatOpen}
              onToggle={() => setIsChatOpen(!isChatOpen)}
              viewMode={viewMode}
            >
              <ChatInterface selectedFile={selectedFile} useRAG={true} />
            </CollapsibleChatPane>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', flexDirection: 'column', color: 'var(--text-secondary)', width: '100%' }}>
            <Bot size={64} style={{ marginBottom: '20px', opacity: 0.5 }} />
            <h2>Bienvenido a ChatPDF</h2>
            <p>Selecciona un archivo PDF para comenzar</p>
          </div>
        )}
      </main>
    </div>
  );
}

// Collapsible Sidebar Wrapper
function CollapsibleSidebar({ children, isOpen, onToggle }: { children: React.ReactNode, isOpen: boolean, onToggle: () => void }) {
  return (
    <div style={{ position: 'relative', display: 'flex', height: '100%' }}>
      <div style={{
        width: isOpen ? '350px' : '0',
        overflow: 'hidden',
        transition: 'width 0.3s ease',
        borderRight: isOpen ? '1px solid var(--border-color)' : 'none',
        background: 'var(--bg-secondary)',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100%'
      }}>
        <div style={{ minWidth: '350px', height: '100%', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
          {children}
        </div>
      </div>

      {/* Toggle Button */}
      <button
        onClick={onToggle}
        style={{
          position: 'absolute',
          top: '50%',
          right: '-12px', /* Position outside */
          zIndex: 20,
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          border: '1px solid var(--border-color)',
          background: 'var(--bg-secondary)',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transform: 'translateY(-50%)'
        }}
        title={isOpen ? "Ocultar panel" : "Mostrar panel"}
      >
        {isOpen ? <ChevronLeft size={14} /> : <ChevronRight size={14} />}
      </button>
    </div>
  );
}

// Collapsible Chat Pane Wrapper
function CollapsibleChatPane({ children, isOpen, onToggle, viewMode }: { children: React.ReactNode, isOpen: boolean, onToggle: () => void, viewMode: string }) {
  const width = !isOpen ? '0px' : '400px';
  const display = !isOpen ? 'none' : 'flex';

  return (
    <div style={{ position: 'relative', height: '100%', display: 'flex', minWidth: 0 }}>
      <button
        onClick={onToggle}
        style={{
          position: 'absolute',
          top: '50%',
          left: '-12px',
          zIndex: 20,
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          border: '1px solid var(--border-color)',
          background: 'var(--bg-primary)',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          transform: 'translateY(-50%)'
        }}
        title={isOpen ? "Ocultar chat" : "Mostrar chat"}
      >
        {isOpen ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      <div style={{
        width: width,
        minWidth: isOpen ? '300px' : '0',
        maxWidth: '500px',
        height: '100%',
        transition: 'width 0.3s ease',
        borderLeft: isOpen ? '1px solid var(--border-color)' : 'none',
        background: 'var(--bg-primary)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <div style={{ flex: 1, display: display, overflow: 'hidden', flexDirection: 'column' }}>
          {children}
        </div>
      </div>
    </div>
  );
}

export default App;
