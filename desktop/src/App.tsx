import React, { useEffect, useState, useRef } from 'react';

export const App: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated'>('idle');
  const [statusText, setStatusText] = useState('System Initialized. Awaiting "2 Claps + FRIDAY"');
  const wsRef = useRef<WebSocket | null>(null);
  const isRunningRef = useRef(true);

  useEffect(() => {
    isRunningRef.current = true;
    
    // Connect WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => console.log('[FRIDAY AI] Connected to Core');

    // Start Master Voice State Loop
    runVoiceLoop();

    return () => {
      isRunningRef.current = false;
      ws.close();
    };
  }, []);

  const runVoiceLoop = async () => {
    if (!isRunningRef.current) return;

    // Step 1: Standby / Awaiting 'FRIDAY' Wake Word
    setVoiceState('wakeword');
    setStatusText('STANDBY MODE: Say "FRIDAY" to Wake Up');


    try {
      const wakeRes = await fetch('http://localhost:8000/api/wait-wakeword?timeout=15').then(r => r.json());

      if (!isRunningRef.current) return;

      if (wakeRes.success && wakeRes.woken) {
        // Step 2: Wake Word Confirmed -> Start Active Voice Listening Loop
        await startActiveListeningCycle();
      } else {
        // Re-enter standby loop if timeout
        setTimeout(() => runVoiceLoop(), 500);
      }
    } catch (err) {
      console.error('WakeWord error:', err);
      setTimeout(() => runVoiceLoop(), 2000);
    }
  };

  const startActiveListeningCycle = async () => {
    if (!isRunningRef.current) return;

    // Step 2: Active Voice Listening Mode
    setVoiceState('listening');
    setStatusText('LISTENING FOR COMMAND...');

    try {
      const data = await fetch('http://localhost:8000/api/listen-mic?duration=4', { method: 'POST' }).then(r => r.json());

      if (!isRunningRef.current) return;

      if (data.success && data.response?.text_response) {
        const text = data.response.text_response;
        const action = data.response.action_executed;

        // Check for System Termination Command
        if (action === 'terminate_system' || text.toLowerCase().includes('terminating system')) {
          setVoiceState('terminated');
          setStatusText('SYSTEM TERMINATED. GOODBYE SIR.');
          isRunningRef.current = false;
          // Attempt to close Tauri window if running inside Tauri
          try {
            window.close();
          } catch (e) {}
          return;
        }

        // Step 3: Speaking / Responding State with High Energy Arc Animations
        setVoiceState('speaking');
        setStatusText(`FRIDAY: "${text}"`);

        const speakDuration = Math.max(3500, text.length * 65);
        setTimeout(() => {
          if (isRunningRef.current) {
            // Loop back to active listening after speaking
            startActiveListeningCycle();
          }
        }, speakDuration);
      } else {
        // Continuous Listening Loop if silent
        setTimeout(() => {
          if (isRunningRef.current) {
            startActiveListeningCycle();
          }
        }, 500);
      }
    } catch (err) {
      console.error('Mic Listening Error:', err);
      setTimeout(() => {
        if (isRunningRef.current) {
          runVoiceLoop();
        }
      }, 1500);
    }
  };

  return (
    <div className="jarvis-container">
      {/* HUD Status Text Display */}
      <div style={{
        position: 'absolute',
        top: '40px',
        textAlign: 'center',
        color: voiceState === 'speaking' ? '#a855f7' : voiceState === 'listening' ? '#00f2ff' : voiceState === 'terminated' ? '#ef4444' : '#3b82f6',
        fontFamily: 'Space Grotesk, sans-serif',
        letterSpacing: '2px',
        fontSize: '14px',
        textTransform: 'uppercase',
        textShadow: '0 0 10px currentColor',
        zIndex: 10
      }}>
        {statusText}
      </div>

      {/* Iron Man F.R.I.D.A.Y. Reactive Core HUD Orb */}
      <div className={`jarvis-core ${voiceState}`} onClick={runVoiceLoop} style={{ cursor: 'pointer' }}>
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
