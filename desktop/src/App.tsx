import React, { useState, useEffect, useRef } from 'react';
import { Mic, Send, Cpu, Monitor, Volume2, ShieldCheck, Terminal, HardDrive, BatteryCharging, Activity } from 'lucide-react';

interface Message {
  id: string;
  sender: 'user' | 'friday';
  text: string;
  action?: string;
}

interface Telemetry {
  cpu_percent: number;
  ram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  disk_percent: number;
  battery: { percent: number; power_plugged: boolean };
}

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', sender: 'friday', text: 'FRIDAY Online. How can I assist your system today?' }
  ]);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [telemetry, setTelemetry] = useState<Telemetry>({
    cpu_percent: 0,
    ram_percent: 0,
    ram_used_gb: 0,
    ram_total_gb: 0,
    disk_percent: 0,
    battery: { percent: 100, power_plugged: true }
  });

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Fetch stored persistent conversation history from SQLite
    fetch('http://localhost:8000/api/history')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.history && data.history.length > 0) {
          setMessages(data.history);
        }
      })
      .catch(() => {});

    // Connect WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;


    ws.onopen = () => setIsConnected(true);
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
    ws.onclose = () => setIsConnected(false);

    // Stream System Telemetry every 3 seconds
    const interval = setInterval(() => {
      fetch('http://localhost:8000/api/system-status')
        .then(res => res.json())
        .then(data => {
          if (data.success && data.metrics) {
            setTelemetry(data.metrics);
          }
        })
        .catch(() => {});
    }, 3000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, []);

  const handleSend = () => {
    if (!input.trim()) return;
    const userMsg: Message = { id: Date.now().toString(), sender: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'text', content: input, speak: true }));
    } else {
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
        });
    }
    setInput('');
  };

  const triggerMicListen = () => {
    setIsListening(true);
    fetch('http://localhost:8000/api/listen-mic?duration=4', { method: 'POST' })
      .then(res => res.json())
      .then(data => {
        setIsListening(false);
        if (data.success && data.transcribed_command) {
          setMessages(prev => [
            ...prev,
            { id: Date.now().toString(), sender: 'user', text: data.transcribed_command },
            {
              id: (Date.now() + 1).toString(),
              sender: 'friday',
              text: data.response.text_response,
              action: data.response.action_executed
            }
          ]);
        } else {
          setMessages(prev => [
            ...prev,
            { id: Date.now().toString(), sender: 'friday', text: `Mic error: ${data.error || 'No speech detected'}` }
          ]);
        }
      })
      .catch(() => setIsListening(false));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', padding: '20px', gap: '16px' }}>
      {/* Top Header & Telemetry Bar */}
      <header className="glass-panel" style={{ padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Cpu color="#00f2ff" size={26} />
          <div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', letterSpacing: '1px' }}>F.R.I.D.A.Y.</h1>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>System Monitoring & AI OS Layer</p>
          </div>
        </div>

        {/* Live Telemetry Metrics */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={14} color="#00f2ff" />
            <span>CPU: <strong>{telemetry.cpu_percent}%</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <HardDrive size={14} color="#3b82f6" />
            <span>RAM: <strong>{telemetry.ram_percent}%</strong> ({telemetry.ram_used_gb}GB)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <BatteryCharging size={14} color="#10b981" />
            <span>Battery: <strong>{telemetry.battery.percent}%</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '10px' }}>
            <span style={{
              width: '8px', height: '8px', borderRadius: '50%',
              backgroundColor: isConnected ? '#10b981' : '#ef4444',
              boxShadow: isConnected ? '0 0 8px #10b981' : 'none'
            }} />
            {isConnected ? 'Online' : 'Offline'}
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '16px', flex: 1, minHeight: 0 }}>
        {/* Left Side: Voice Orb & Quick Actions */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px', gap: '20px' }}>
          <div className={`voice-orb ${isListening ? 'listening' : ''}`} onClick={triggerMicListen}>
            <Mic color="#ffffff" size={36} />
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center' }}>
            {isListening ? 'Recording mic... Speak now' : 'Click Orb to start Voice Recording'}
          </p>

          <div style={{ width: '100%', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>Quick Intents</span>
            <button className="glass-panel" style={{ padding: '8px 12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }} onClick={() => { setInput("start coding mode"); }}>
              <Terminal size={14} color="#00f2ff" /> Start Coding Mode
            </button>
            <button className="glass-panel" style={{ padding: '8px 12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }} onClick={() => { setInput("Set volume to 40"); }}>
              <Volume2 size={14} color="#00f2ff" /> Set Volume to 40%
            </button>
            <button className="glass-panel" style={{ padding: '8px 12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px' }} onClick={() => { setInput("Take a screenshot"); }}>
              <ShieldCheck size={14} color="#00f2ff" /> Capture Screen
            </button>
          </div>
        </div>

        {/* Right Side: Command Log Console */}
        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', padding: '16px', minHeight: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Monitor size={16} color="#00f2ff" />
              <span style={{ fontWeight: 600, fontSize: '13px' }}>FRIDAY Operating Console</span>
            </div>
            <button
              onClick={() => {
                fetch('http://localhost:8000/api/clear-history', { method: 'POST' })
                  .then(() => setMessages([{ id: Date.now().toString(), sender: 'friday', text: 'Cleared conversation history.' }]));
              }}
              style={{ background: 'transparent', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#ef4444', padding: '3px 8px', borderRadius: '4px', fontSize: '10px', cursor: 'pointer' }}
            >
              Clear Memory
            </button>
          </div>


          <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '10px', paddingRight: '6px' }}>
            {messages.map(msg => (
              <div key={msg.id} style={{
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                padding: '10px 14px',
                borderRadius: '10px',
                background: msg.sender === 'user' ? 'rgba(59, 130, 246, 0.25)' : 'rgba(0, 242, 255, 0.08)',
                border: msg.sender === 'user' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid rgba(0, 242, 255, 0.2)'
              }}>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginBottom: '3px' }}>
                  {msg.sender === 'user' ? 'User' : 'FRIDAY'}
                </div>
                <div style={{ fontSize: '13px', lineHeight: '1.4' }}>{msg.text}</div>
                {msg.action && (
                  <div style={{ marginTop: '5px', fontSize: '10px', color: '#00f2ff', background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: '4px', display: 'inline-block' }}>
                    Action: {msg.action}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Input Bar */}
          <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
            <input
              type="text"
              placeholder="Type command or click Voice Orb to speak..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              style={{
                flex: 1,
                background: 'rgba(0,0,0,0.4)',
                border: '1px solid var(--border-glow)',
                borderRadius: '8px',
                padding: '10px 14px',
                color: '#fff',
                outline: 'none',
                fontFamily: 'inherit',
                fontSize: '13px'
              }}
            />
            <button
              onClick={handleSend}
              style={{
                background: '#00f2ff',
                border: 'none',
                borderRadius: '8px',
                padding: '0 16px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#0a0c14',
                fontWeight: 'bold'
              }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
