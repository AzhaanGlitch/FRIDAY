import React, { useEffect, useState, useRef } from 'react';

export const App: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated'>('idle');
  const [statusText, setStatusText] = useState('STANDBY MODE: Say "FRIDAY" to Wake Up');
  const [liveTranscript, setLiveTranscript] = useState<string>('System online. Awaiting voice trigger.');
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

    // Step 1: Standby / Awaiting 'FRIDAY' Wake Word
    setVoiceState('wakeword');
    setStatusText('STANDBY MODE: Say "FRIDAY" to Wake Up');

    try {
      const wakeRes = await fetch('http://localhost:8000/api/wait-wakeword?timeout=15').then(r => r.json());

      if (!isRunningRef.current) { loopActiveRef.current = false; return; }

      if (wakeRes.success && wakeRes.woken) {
        // Step 2: Wake Word Confirmed -> Active Voice Listening
        setLiveTranscript('Heard: "FRIDAY" → Listening for your command...');
        await startActiveListeningCycle();
      } else {
        // Continue loop
        setTimeout(() => runVoiceLoop(), 100);
      }
    } catch (err) {
      console.error('WakeWord error:', err);
      setTimeout(() => runVoiceLoop(), 1500);
    }
  };

  const startActiveListeningCycle = async () => {
    if (!isRunningRef.current) { loopActiveRef.current = false; return; }

    setVoiceState('listening');
    setStatusText('LISTENING FOR COMMAND...');

    try {
      const data = await fetch('http://localhost:8000/api/listen-mic?duration=6', { method: 'POST' }).then(r => r.json());

      if (!isRunningRef.current) { loopActiveRef.current = false; return; }

      if (data.success && data.response?.text_response) {
        const text = data.response.text_response;
        const action = data.response.action_executed;
        const transcribed = data.transcribed_command || '';

        // Live HUD display update (bottom left)
        setLiveTranscript(transcribed ? `Heard: "${transcribed}" → ${action !== 'none' ? `[Action: ${action}]` : 'Conversational'}` : text);

        // Check Termination
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

        if (isRunningRef.current) {
          await startActiveListeningCycle();
        }
      } else {
        // No command caught -> return to standby
        setLiveTranscript('No input heard. Returning to standby.');
        await new Promise(resolve => setTimeout(resolve, 300));
        if (isRunningRef.current) {
          runVoiceLoop();
        }
      }
    } catch (err) {
      console.error('Mic Listening Error:', err);
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (isRunningRef.current) {
        runVoiceLoop();
      }
    }
  };

  return (
    <div className="jarvis-container">
      {/* 3D Orbital Loader AI Core */}
      <div className={`orbital-loader ${voiceState}`} style={{ cursor: 'default' }}>
        <div className="core-system">
          <div className="core-micro-center"></div>
          <div className="core-inner-glow"></div>
          <div className="core-thin-ring"></div>
          <div className="core-secondary-ring"></div>
          <div className="core-outer-ring"></div>
          <div className="core-halo"></div>
        </div>

        <div className="pulse-system">
          <div className="pulse-ring pulse-ring-1"></div>
          <div className="pulse-ring pulse-ring-2"></div>
          <div className="pulse-ring pulse-ring-3"></div>
        </div>

        <div className="orbit-system">
          <div className="orbit-1">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-circle"></div>
              <div className="object-trail"></div>
            </div>
          </div>
          <div className="orbit-2">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-ring"></div>
            </div>
          </div>
          <div className="orbit-3">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-bright-point"></div>
            </div>
          </div>
          <div className="orbit-4">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-diamond"></div>
            </div>
          </div>
          <div className="orbit-5">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-line"></div>
            </div>
          </div>
          <div className="orbit-6">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-square"></div>
            </div>
          </div>
          <div className="orbit-7">
            <div className="orbit-path"></div>
            <div className="orbit-object-wrapper">
              <div className="orbit-object obj-fragment"></div>
            </div>
          </div>
        </div>

        <div className="particle-system">
          <div className="particle p1"></div>
          <div className="particle p2"></div>
          <div className="particle p3"></div>
          <div className="particle p4"></div>
          <div className="particle p5"></div>
          <div className="particle p6"></div>
          <div className="particle p7"></div>
          <div className="particle p8"></div>
          <div className="particle p9"></div>
          <div className="particle p10"></div>
          <div className="particle p11"></div>
          <div className="particle p12"></div>
          <div className="particle p13"></div>
          <div className="particle p14"></div>
          <div className="particle p15"></div>
        </div>

        <div className="energy-fragments">
          <div className="energy-fragment ef1"></div>
          <div className="energy-fragment ef2"></div>
          <div className="energy-fragment ef3"></div>
        </div>
      </div>

      {/* Subtle Greyish Bottom-Left Status HUD */}
      <div style={{
        position: 'fixed',
        bottom: '16px',
        left: '20px',
        maxWidth: '380px',
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
