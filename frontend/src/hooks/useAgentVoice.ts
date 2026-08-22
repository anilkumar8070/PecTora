import { useEffect, useState, useRef, useCallback } from 'react';
import { VADService } from '../services/vad';

export type AgentState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

export function useAgentVoice(remoteStream: MediaStream | null, sessionToken: string) {
  const [agentState, setAgentState] = useState<AgentState>('IDLE');
  const [transcript, setTranscript] = useState<string>('');
  const vadServiceRef = useRef<VADService | null>(null);
  
  // Audio Context for playing TTS and routing to WebRTC
  const audioCtxRef = useRef<AudioContext | null>(null);
  const mediaStreamDestinationRef = useRef<MediaStreamAudioDestinationNode | null>(null);

  // Expose this so WebRTC can replace the local track with the Agent's synthesized voice
  const [agentStream, setAgentStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    // Setup Audio Routing
    audioCtxRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    mediaStreamDestinationRef.current = audioCtxRef.current.createMediaStreamDestination();
    setAgentStream(mediaStreamDestinationRef.current.stream);

    return () => {
      audioCtxRef.current?.close();
    };
  }, []);

  useEffect(() => {
    if (!remoteStream) return;

    vadServiceRef.current = new VADService(remoteStream, {
      onSpeechStart: () => {
        setAgentState('LISTENING');
        // Interruption: If TTS is playing, we should stop it
        if (audioCtxRef.current?.state === 'running') {
           // We can suspend context or disconnect nodes to stop TTS
        }
      },
      onSpeechEnd: async (audioBlob: Blob) => {
        setAgentState('THINKING');
        
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'turn.webm');
          formData.append('token', sessionToken);
          
          const response = await fetch('http://localhost:8000/api/voice/turn', {
            method: 'POST',
            body: formData
          });
          
          if (!response.ok) throw new Error('Backend failed to process turn');
          
          // Read the streaming audio response
          setAgentState('SPEAKING');
          const reader = response.body?.getReader();
          if (!reader) return;

          // Play chunks as they arrive
          const playChunk = async () => {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;
              
              if (audioCtxRef.current && mediaStreamDestinationRef.current && value) {
                // Decode raw bytes. In a real app we'd use a robust chunked decoder.
                // For simplicity, assuming WAV chunks or using HTMLAudioElement via Blob URLs.
                try {
                  const audioBuffer = await audioCtxRef.current.decodeAudioData(value.buffer.slice(0));
                  const source = audioCtxRef.current.createBufferSource();
                  source.buffer = audioBuffer;
                  // Route to local speakers so owner hears it
                  source.connect(audioCtxRef.current.destination);
                  // Route to WebRTC so counterparty hears it
                  source.connect(mediaStreamDestinationRef.current);
                  source.start();
                } catch (err) {
                  // Ignore chunk decode errors in simple implementation
                }
              }
            }
            setAgentState('IDLE');
          };
          
          playChunk();

        } catch (e) {
          console.error(e);
          setAgentState('IDLE');
        }
      }
    });
    
    vadServiceRef.current.start();
    
    return () => {
      vadServiceRef.current?.stop();
    };
  }, [remoteStream, sessionToken]);

  return { agentState, agentStream, transcript };
}
