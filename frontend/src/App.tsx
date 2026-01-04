import { useState, useEffect } from 'react';
import { Bot, Settings } from 'lucide-react';
import FileUpload from './components/FileUpload';
import FileList from './components/FileList';
import ChatInterface from './components/ChatInterface';
import axios from 'axios';
import type { SystemStatus } from './types';
import './App.css';

function App() {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [useRAG, setUseRAG] = useState(true);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);

  useEffect(() => {
    fetchSystemStatus();
  }, []);

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
      <aside className="sidebar">
        <div className="sidebar-header">
          <Bot size={32} />
          <h1>ChatPDF</h1>
        </div>

        <FileUpload onUploadSuccess={handleUploadSuccess} />

        <FileList
          refreshTrigger={refreshTrigger}
          onFileSelect={setSelectedFile}
          selectedFile={selectedFile}
        />

        <div className="settings">
          <div className="settings-header">
            <Settings size={18} />
            <span>Configuración</span>
          </div>

          <label className="toggle-option">
            <input
              type="checkbox"
              checked={useRAG}
              onChange={(e) => setUseRAG(e.target.checked)}
            />
            <span>Usar RAG</span>
          </label>

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
      </aside>

      <main className="main-content">
        <ChatInterface selectedFile={selectedFile} useRAG={useRAG} />
      </main>
    </div>
  );
}

export default App;

