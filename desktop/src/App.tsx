import React, { useEffect, useState, useRef } from 'react';
import { GradientOrb } from './components/GradientOrb';

export const App: React.FC = () => {
  const [voiceState, setVoiceState] = useState<'idle' | 'wakeword' | 'listening' | 'speaking' | 'terminated'>('idle');
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

    try {
      const wakeRes = await fetch('http://localhost:8000/api/wait-wakeword?timeout=15').then(r => r.json());

      if (!isRunningRef.current) { loopActiveRef.current = false; return; }

      if (wakeRes.success && wakeRes.woken) {
        // Step 2: Wake Word Confirmed -> Enter Infinite Active Listening Loop
        setLiveTranscript('Heard: "FRIDAY" → System ACTIVE');
        await startContinuousActiveListeningLoop();
      } else {
        // Continue standby check
        setTimeout(() => runVoiceLoop(), 50);
      }
    } catch (err) {
      console.error('WakeWord error:', err);
      setTimeout(() => runVoiceLoop(), 1000);
    }
  };

  /**
   * Helper: Wait until background speech playback finishes with zero lag
   */
  const waitForSpeechToFinish = async (maxWaitSeconds = 12) => {
    const startTime = Date.now();
    // Brief initial grace period for TTS thread to register
    await new Promise(r => setTimeout(r, 200));

    while (Date.now() - startTime < maxWaitSeconds * 1000) {
      try {
        const res = await fetch('http://localhost:8000/api/is-speaking').then(r => r.json());
        if (!res.speaking) {
          break;
        }
      } catch (e) {
        break;
      }
      await new Promise(r => setTimeout(r, 120));
    }
  };

  /**
   * Infinite Active Listening Loop:
   * Real-time zero-delay speech animations + listening cycle.
   */
  const startContinuousActiveListeningLoop = async () => {
    while (isRunningRef.current) {
      setVoiceState('listening');

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
            setLiveTranscript('System terminated.');
            isRunningRef.current = false;
            loopActiveRef.current = false;
            try {
              window.close();
            } catch (e) {}
            return;
          }

          // Instantly trigger Speaking animation with zero delay!
          setVoiceState('speaking');

          // Wait exactly while audio is playing, then smoothly transition back to listening
          await waitForSpeechToFinish();

          // Immediately loop back to listening for next command
          continue;
        } else {
          // Silence or background noise window
          setLiveTranscript('Listening... (Say any command or "Terminate the system")');
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      } catch (err) {
        console.error('Mic Listening Error:', err);
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }
  };

  return (
    <div style={{ width: '100vw', height: '100vh', overflow: 'hidden', background: '#07090e', position: 'relative' }}>
      {/* GPU Shader Gradient Orb (Audio-reactive synchronized fluid glow) */}
      <GradientOrb voiceState={voiceState} />

      {/* Subtle Greyish Bottom-Left Status HUD */}
      <div style={{
        position: 'fixed',
        bottom: '16px',
        left: '20px',
        maxWidth: '420px',
        fontSize: '11px',
        fontFamily: 'monospace',
        color: '#94a3b8',
        opacity: 0.7,
        letterSpacing: '0.5px',
        lineHeight: 1.4,
        pointerEvents: 'none',
        zIndex: 50,
        textShadow: '0 1px 3px rgba(0,0,0,0.9)'
      }}>
        {liveTranscript}
      </div>
    </div>
  );
};

export default App;
