import { useState, useEffect, useRef, useCallback } from 'react';
import { WebRTCService, ConnectionState } from '../services/webrtc';

interface UseWebRTCProps {
  onSignal: (type: string, payload: any) => void;
  onError?: (error: Error) => void;
}

export function useWebRTC({ onSignal, onError }: UseWebRTCProps) {
  const [connectionState, setConnectionState] = useState<ConnectionState>('new');
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);
  const [isMuted, setIsMuted] = useState(false);
  const [micPermission, setMicPermission] = useState<'prompt' | 'granted' | 'denied'>('prompt');
  
  const rtcService = useRef<WebRTCService | null>(null);

  // Initialize service
  useEffect(() => {
    rtcService.current = new WebRTCService({
      onConnectionStateChange: (state) => setConnectionState(state),
      onRemoteTrack: (stream) => setRemoteStream(stream),
      onSignal: (type, payload) => onSignal(type, payload),
      onError: (err) => {
        if (err.message.includes('Permission denied')) {
          setMicPermission('denied');
        }
        if (onError) onError(err);
      }
    });

    return () => {
      rtcService.current?.endCall();
    };
  }, [onSignal, onError]);

  const startCall = useCallback(async () => {
    try {
      if (!rtcService.current) return;
      await rtcService.current.initialize();
      setMicPermission('granted');
      await rtcService.current.createOffer();
    } catch (e) {
      console.error("Failed to start call", e);
    }
  }, []);

  const handleIncomingSignal = useCallback(async (type: string, payload: any) => {
    if (!rtcService.current) return;

    try {
      if (type === 'WEBRTC_OFFER') {
        if (micPermission !== 'granted') {
           await rtcService.current.initialize();
           setMicPermission('granted');
        }
        await rtcService.current.handleOffer(payload.sdp);
      } else if (type === 'WEBRTC_ANSWER') {
        await rtcService.current.handleAnswer(payload.sdp);
      } else if (type === 'WEBRTC_ICE_CANDIDATE') {
        await rtcService.current.handleIceCandidate(payload.candidate);
      }
    } catch (e) {
      console.error(`Failed to handle signal ${type}`, e);
    }
  }, [micPermission]);

  const toggleMute = useCallback(() => {
    if (rtcService.current) {
      const newMutedState = !isMuted;
      rtcService.current.toggleMute(newMutedState);
      setIsMuted(newMutedState);
    }
  }, [isMuted]);

  const endCall = useCallback(() => {
    if (rtcService.current) {
      rtcService.current.endCall();
      setRemoteStream(null);
      setConnectionState('closed');
    }
  }, []);

  return {
    connectionState,
    remoteStream,
    isMuted,
    micPermission,
    startCall,
    handleIncomingSignal,
    toggleMute,
    endCall
  };
}
