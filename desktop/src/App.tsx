import React, { useEffect, useState, useRef } from 'react';

export const App: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'idle' | 'listening' | 'speaking'>('listening');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 1. Automatically start listening on application startup
    startListening();

    // 2. Connect WebSocket to listen to backend AI responses
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => console.log('[FRIDAY AI] Connected');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'response') {
          // AI speaking state animation
          setVoiceState('speaking');
          const speakDuration = Math.max(3500, (data.content || '').length * 65);
          setTimeout(() => {
            // Auto resume listening state after speech finishes
            startListening();
          }, speakDuration);
        }
      } catch (err) {
        console.error('WS Error:', err);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const startListening = () => {
    setVoiceState('listening');
    fetch('http://localhost:8000/api/listen-mic?duration=5', { method: 'POST' })
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.response?.text_response) {
          setVoiceState('speaking');
          const speakDuration = Math.max(3500, (data.response.text_response || '').length * 65);
          setTimeout(() => {
            startListening();
          }, speakDuration);
        } else {
          // Continuous loop - restart listening if silent or finished
          setTimeout(() => {
            startListening();
          }, 800);
        }
      })
      .catch(() => {
        setTimeout(() => {
          startListening();
        }, 2000);
      });
  };

  return (
    <div className="jarvis-container">
      {/* Iron Man F.R.I.D.A.Y. Reactive Core HUD Orb */}
      <div className={`jarvis-core ${voiceState}`}>
        {/* Core Nucleus */}
        <div className="core-nucleus"></div>

        {/* Inner Arc Reactor Node Ring */}
        <div className="inner-node-ring">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="node-segment" style={{ transform: `rotate(${i * 30}deg) translateY(-44px)` }} />
          ))}
        </div>

        {/* Rotating Arc Rings */}
        <div className="ring ring-outer-1"></div>
        <div className="ring ring-outer-2"></div>
        <div className="ring ring-outer-3"></div>

        {/* Frequency Sound Wave Pulses */}
        <div className="wave-pulse wave-1"></div>
        <div className="wave-pulse wave-2"></div>
        <div className="wave-pulse wave-3"></div>
      </div>
    </div>
  );
};

export default App;
