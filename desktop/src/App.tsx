import React, { useEffect, useState, useRef } from 'react';

export const App: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated'>('idle');
  const [statusText, setStatusText] = useState('System Initialized. Say "FRIDAY" to wake up.');
  const wsRef = useRef<WebSocket | null>(null);
  const isRunningRef = useRef(true);
  const loopActiveRef = useRef(false); // Prevent duplicate loops

  useEffect(() => {
    isRunningRef.current = true;
    
    // Connect WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => console.log('[FRIDAY AI] Connected to Core');

    // Start Master Voice State Loop (only once)
    if (!loopActiveRef.current) {
      loopActiveRef.current = true;
      runVoiceLoop();
    }

    return () => {
      isRunningRef.current = false;
      ws.close();
    };
  }, []);

  const runVoiceLoop = async () => {
    if (!isRunningRef.current) {
      loopActiveRef.current = false;
      return;
    }

    // Step 1: Standby / Awaiting 'FRIDAY' Wake Word
    setVoiceState('wakeword');
    setStatusText('STANDBY MODE: Say "FRIDAY" to Wake Up');

    try {
      const wakeRes = await fetch('http://localhost:8000/api/wait-wakeword?timeout=15').then(r => r.json());

      if (!isRunningRef.current) { loopActiveRef.current = false; return; }

      if (wakeRes.success && wakeRes.woken) {
        // Step 2: Wake Word Confirmed -> Start Active Voice Listening Loop
        await startActiveListeningCycle();
      } else {
        // Re-enter standby loop if timeout
        setTimeout(() => runVoiceLoop(), 300);
      }
    } catch (err) {
      console.error('WakeWord error:', err);
      setTimeout(() => runVoiceLoop(), 2000);
    }
  };

  const startActiveListeningCycle = async () => {
    if (!isRunningRef.current) { loopActiveRef.current = false; return; }

    // Step 2: Active Voice Listening Mode
    setVoiceState('listening');
    setStatusText('LISTENING FOR COMMAND...');

    try {
      const data = await fetch('http://localhost:8000/api/listen-mic?duration=7', { method: 'POST' }).then(r => r.json());

      if (!isRunningRef.current) { loopActiveRef.current = false; return; }

      if (data.success && data.response?.text_response) {
        const text = data.response.text_response;
        const action = data.response.action_executed;

        // Check for System Termination Command
        if (action === 'terminate_system' || text.toLowerCase().includes('terminating system')) {
          setVoiceState('terminated');
          setStatusText('SYSTEM TERMINATED. GOODBYE SIR.');
          isRunningRef.current = false;
          loopActiveRef.current = false;
          try {
            window.close();
          } catch (e) {}
          return;
        }

        // Step 3: Speaking / Responding — use backend-provided TTS duration
        setVoiceState('speaking');
        setStatusText(`FRIDAY: "${text}"`);

        const speakDuration = data.tts_duration_ms || Math.max(3500, text.length * 65);
        await new Promise(resolve => setTimeout(resolve, speakDuration));

        if (isRunningRef.current) {
          // Loop back to active listening after speaking finishes
          await startActiveListeningCycle();
        }
      } else if (data.error === 'Another recording is already in progress') {
        // Another recording is running (shouldn't happen with the lock, but safety)
        await new Promise(resolve => setTimeout(resolve, 2000));
        if (isRunningRef.current) {
          await startActiveListeningCycle();
        }
      } else {
        // No speech detected — wait briefly, then loop back to wakeword standby
        await new Promise(resolve => setTimeout(resolve, 500));
        if (isRunningRef.current) {
          runVoiceLoop();
        }
      }
    } catch (err) {
      console.error('Mic Listening Error:', err);
      await new Promise(resolve => setTimeout(resolve, 1500));
      if (isRunningRef.current) {
        runVoiceLoop();
      }
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

      {/* Iron Man F.R.I.D.A.Y. Reactive Core HUD Orb — no onClick to prevent duplicate loops */}
      <div className={`jarvis-core ${voiceState}`} style={{ cursor: 'default' }}>
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
