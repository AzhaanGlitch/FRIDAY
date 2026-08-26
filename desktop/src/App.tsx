import React, { useEffect, useState, useRef } from 'react';
import { HolographicReactor } from './components/HolographicReactor';

export const App: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated'>('idle');
  const [statusText, setStatusText] = useState('STANDBY MODE: Say "FRIDAY" to Wake Up');
  const [liveTranscript, setLiveTranscript] = useState<string>('System online. Awaiting wake word "FRIDAY"...');
  const wsRef = useRef<WebSocket | null>(null);
  const isRunningRef = useRef(true);
  const loopActiveRef = useRef(false);

  useEffect(() => {
    isRunningRef.current = true;
    
    // Connect WebSocket
    const ws = new WebSocket('http://localhost:8000/ws'.replace('http', 'ws'));
    wsRef.current = ws;

    ws.onopen = () => console.log('[FRIDAY AI] Connected to Core');

    // Start Master Voice Loop
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

    // Step 1: Initial Standby / Awaiting 'FRIDAY' Wake Word
    setVoiceState('wakeword');
    setStatusText('STANDBY MODE: Say "FRIDAY" to Wake Up');

    try {
      const wakeRes = await fetch('http://localhost:8000/api/wait-wakeword?timeout=15').then(r => r.json());

      if (!isRunningRef.current) { loopActiveRef.current = false; return; }

      if (wakeRes.success && wakeRes.woken) {
        // Step 2: Wake Word Confirmed -> Enter Infinite Active Listening Loop
        setLiveTranscript('Heard: "FRIDAY" → System ACTIVE & Listening continuously...');
        await startContinuousActiveListeningLoop();
      } else {
        // Continue standby check
        setTimeout(() => runVoiceLoop(), 100);
      }
    } catch (err) {
      console.error('WakeWord error:', err);
      setTimeout(() => runVoiceLoop(), 1500);
    }
  };

  /**
   * Infinite Active Listening Loop:
   * Once woken up by "FRIDAY", it stays in active listening mode continuously.
   * Only exits if you say "Terminate the system".
   */
  const startContinuousActiveListeningLoop = async () => {
    while (isRunningRef.current) {
      setVoiceState('listening');
      setStatusText('F.R.I.D.A.Y. ACTIVE: Listening for your command...');

      try {
        const data = await fetch('http://localhost:8000/api/listen-mic?duration=4.5', { method: 'POST' }).then(r => r.json());

        if (!isRunningRef.current) break;

        if (data.success && data.response?.text_response) {
          const text = data.response.text_response;
          const action = data.response.action_executed;
          const transcribed = data.transcribed_command || '';

          // Live HUD display update (bottom left)
          setLiveTranscript(`Heard: "${transcribed}" → ${action !== 'none' ? `[Action: ${action}]` : 'Conversational'}`);

          // Check Termination Command
          if (action === 'terminate_system' || text.toLowerCase().includes('terminating system')) {
            setVoiceState('terminated');
            setStatusText('SYSTEM TERMINATED. GOODBYE SIR.');
            setLiveTranscript('System terminated.');
            isRunningRef.current = false;
            loopActiveRef.current = false;
            try {
              window.close();
            } catch (e) {}
            return;
          }

          // Speaking state
          setVoiceState('speaking');
          setStatusText(`FRIDAY: "${text}"`);

          const speakDuration = data.tts_duration_ms || Math.max(1000, text.length * 40);
          await new Promise(resolve => setTimeout(resolve, speakDuration));

          // Immediately loop back to listening for next command
          continue;
        } else {
          // No sound / silence in this window -> update HUD but STAY in active listening mode!
          setLiveTranscript('Listening... (Say any command or "Terminate the system")');
          await new Promise(resolve => setTimeout(resolve, 200));
        }
      } catch (err) {
        console.error('Mic Listening Error:', err);
        await new Promise(resolve => setTimeout(resolve, 800));
      }
    }
  };

  return (
    <div className="jarvis-container">
      {/* 3D Holographic React + Three.js + Framer Motion Arc Reactor Core */}
      <HolographicReactor voiceState={voiceState} />

      {/* Subtle Greyish Bottom-Left Status HUD */}
      <div style={{
        position: 'fixed',
        bottom: '16px',
        left: '20px',
        maxWidth: '420px',
        fontSize: '11px',
        fontFamily: 'monospace',
        color: '#94a3b8',
        opacity: 0.65,
        letterSpacing: '0.5px',
        lineHeight: 1.4,
        pointerEvents: 'none',
        zIndex: 50,
        textShadow: '0 1px 2px rgba(0,0,0,0.8)'
      }}>
        <span style={{ color: '#38bdf8', opacity: 0.8 }}>● FRIDAY_CORE:</span> {liveTranscript}
      </div>
    </div>
  );
};

export default App;
