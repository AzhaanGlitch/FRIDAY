import React, { useState, useEffect, useRef } from 'react';
import { Mic, Send, Cpu, Monitor, Volume2, ShieldCheck, Terminal, AppWindow } from 'lucide-react';
import { invoke } from '@tauri-apps/api/tauri';

interface Message {
  id: string;
  sender: 'user' | 'friday';
  text: string;
  action?: string;
}

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'friday', text: 'F.R.I.D.A.Y. Desktop Shell Online. How can I assist your system today?' }
  ]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [tauriStatus, setTauriStatus] = useState<string>('Initializing Desktop Layer...');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Check Tauri Native Integration
    try {
      invoke<string>('get_system_status')
        .then(status => setTauriStatus(status))
        .catch(() => setTauriStatus('Running in Web Preview Mode'));
    } catch {
      setTauriStatus('Running in Web Preview Mode');
    }

    // Connect WebSocket to Python FastAPI AI Core
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'response') {
          setMessages(prev => [
            ...prev,
            {
              id: Date.now().toString(),
              sender: 'friday',
              text: data.content,
              action: data.action !== 'none' ? data.action : undefined
            }
          ]);
        }
      } catch (err) {
        console.error('WS parse error', err);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', content: input, speak: true }));
    } else {
      // REST API Fallback
      fetch('http://localhost:8000/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: input, speak_response: true })
      })
        .then(res => res.json())
        .then(data => {
          setMessages(prev => [
            ...prev,
            {
              id: Date.now().toString(),
              sender: 'friday',
              text: data.text_response,
              action: data.action_executed
            }
          ]);
        })
        .catch(err => {
          console.error('API Error', err);
          setMessages(prev => [
            ...prev,
            {
              id: Date.now().toString(),
              sender: 'friday',
              text: 'Unable to communicate with FRIDAY Python Core API (http://localhost:8000). Please ensure backend is running.'
            }
          ]);
        });
    }

    setInput('');
  };

  const toggleVoice = () => {
    setIsListening(prev => !prev);
    if (!isListening) {
      setTimeout(() => {
        setIsListening(false);
        setInput("Open Spotify");
      }, 2500);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '24px', gap: '20px' }}>
      {/* Top Header */}
      <header className="glass-panel" style={{ padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Cpu color="#00f2ff" size={28} />
          <div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', letterSpacing: '1px' }}>F.R.I.D.A.Y. Desktop</h1>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Tauri Native Desktop Architecture Phase-1 MVP</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)', background: 'rgba(255,255,255,0.05)', padding: '4px 10px', borderRadius: '6px' }}>
            <AppWindow size={14} color="#00f2ff" />
            <span>{tauriStatus}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
            <span style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: isConnected ? '#10b981' : '#ef4444',
              boxShadow: isConnected ? '0 0 8px #10b981' : 'none'
            }} />
            {isConnected ? 'Core Connected' : 'Disconnected'}
          </div>
        </div>
      </header>

      {/* Main Content Body */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', flex: 1, minHeight: 0 }}>
        {/* Left Side: Voice Orb & System Quick Controls */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', gap: '24px' }}>
          <div className={`voice-orb ${isListening ? 'listening' : ''}`} onClick={toggleVoice}>
            <Mic color="#ffffff" size={40} />
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', textAlign: 'center' }}>
            {isListening ? 'Listening for voice commands...' : 'Click orb or speak "Hey FRIDAY"'}
          </p>

          <div style={{ width: '100%', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Quick Intents</span>
            <button className="glass-panel" style={{ padding: '10px 14px', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => { setInput("Open Spotify"); }}>
              <Monitor size={16} color="#00f2ff" /> Open Spotify
            </button>
            <button className="glass-panel" style={{ padding: '10px 14px', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => { setInput("Set volume to 40"); }}>
              <Volume2 size={16} color="#00f2ff" /> Set Volume to 40%
            </button>
            <button className="glass-panel" style={{ padding: '10px 14px', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }} onClick={() => { setInput("Take a screenshot"); }}>
              <ShieldCheck size={16} color="#00f2ff" /> Capture Screen
            </button>
          </div>
        </div>

        {/* Right Side: Conversation Console */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', padding: '20px', minHeight: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '16px' }}>
            <Terminal size={18} color="#00f2ff" />
            <span style={{ fontWeight: 600, fontSize: '14px' }}>Desktop System Command Log</span>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', paddingRight: '8px' }}>
            {messages.map(msg => (
              <div key={msg.id} style={{
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                padding: '12px 16px',
                borderRadius: '12px',
                background: msg.sender === 'user' ? 'rgba(59, 130, 246, 0.25)' : 'rgba(0, 242, 255, 0.08)',
                border: msg.sender === 'user' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid rgba(0, 242, 255, 0.2)'
              }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  {msg.sender === 'user' ? 'User' : 'FRIDAY'}
                </div>
                <div style={{ fontSize: '14px', lineHeight: '1.5' }}>{msg.text}</div>
                {msg.action && (
                  <div style={{ marginTop: '6px', fontSize: '11px', color: '#00f2ff', background: 'rgba(0,0,0,0.3)', padding: '2px 8px', borderRadius: '4px', display: 'inline-block' }}>
                    Action: {msg.action}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Input Bar */}
          <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
            <input
              type="text"
              placeholder="Type command (e.g. 'Open Spotify', 'Take a screenshot')..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              style={{
                flex: 1,
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid var(--border-glow)',
                borderRadius: '10px',
                padding: '12px 16px',
                color: '#fff',
                outline: 'none',
                fontFamily: 'inherit'
              }}
            />
            <button
              onClick={handleSend}
              style={{
                background: '#00f2ff',
                border: 'none',
                borderRadius: '10px',
                padding: '0 20px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#0a0c14',
                fontWeight: 'bold'
              }}
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

