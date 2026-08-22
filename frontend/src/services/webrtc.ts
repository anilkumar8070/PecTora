// WebRTC Service to handle Peer-to-Peer Audio

export type ConnectionState = 'new' | 'connecting' | 'connected' | 'disconnected' | 'failed' | 'closed';

export interface WebRTCServiceCallbacks {
  onConnectionStateChange: (state: ConnectionState) => void;
  onRemoteTrack: (stream: MediaStream) => void;
  onSignal: (type: string, payload: any) => void; // Used to send signaling data via WebSocket
  onError: (error: Error) => void;
}

export class WebRTCService {
  private peerConnection: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private callbacks: WebRTCServiceCallbacks;
  
  // STUN servers for NAT traversal
  private config: RTCConfiguration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  constructor(callbacks: WebRTCServiceCallbacks) {
    this.callbacks = callbacks;
  }

  public async initialize(audioConstraints: MediaStreamConstraints = { audio: true, video: false }): Promise<void> {
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia(audioConstraints);
      this.createPeerConnection();
    } catch (err) {
      this.callbacks.onError(err instanceof Error ? err : new Error('Failed to get user media'));
      throw err;
    }
  }

  private createPeerConnection() {
    this.peerConnection = new RTCPeerConnection(this.config);

    // Add local tracks to peer connection
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => {
        if (this.localStream && this.peerConnection) {
          this.peerConnection.addTrack(track, this.localStream);
        }
      });
    }

    // Handle ICE candidates
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.callbacks.onSignal('WEBRTC_ICE_CANDIDATE', { candidate: event.candidate });
      }
    };

    // Handle connection state changes
    this.peerConnection.onconnectionstatechange = () => {
      if (this.peerConnection) {
        this.callbacks.onConnectionStateChange(this.peerConnection.connectionState as ConnectionState);
      }
    };

    // Handle incoming media tracks
    this.peerConnection.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        this.callbacks.onRemoteTrack(event.streams[0]);
      }
    };
  }

  public async createOffer(): Promise<void> {
    if (!this.peerConnection) return;
    
    try {
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);
      this.callbacks.onSignal('WEBRTC_OFFER', { sdp: this.peerConnection.localDescription });
    } catch (err) {
      this.callbacks.onError(err instanceof Error ? err : new Error('Failed to create offer'));
    }
  }

  public async handleOffer(offer: RTCSessionDescriptionInit): Promise<void> {
    if (!this.peerConnection) this.createPeerConnection();
    
    try {
      await this.peerConnection!.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await this.peerConnection!.createAnswer();
      await this.peerConnection!.setLocalDescription(answer);
      this.callbacks.onSignal('WEBRTC_ANSWER', { sdp: this.peerConnection!.localDescription });
    } catch (err) {
      this.callbacks.onError(err instanceof Error ? err : new Error('Failed to handle offer'));
    }
  }

  public async handleAnswer(answer: RTCSessionDescriptionInit): Promise<void> {
    if (!this.peerConnection) return;
    
    try {
      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (err) {
      this.callbacks.onError(err instanceof Error ? err : new Error('Failed to handle answer'));
    }
  }

  public async handleIceCandidate(candidateInit: RTCIceCandidateInit): Promise<void> {
    if (!this.peerConnection) return;
    
    try {
      await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidateInit));
    } catch (err) {
      this.callbacks.onError(err instanceof Error ? err : new Error('Failed to handle ICE candidate'));
    }
  }

  public toggleMute(muted: boolean): void {
    if (this.localStream) {
      this.localStream.getAudioTracks().forEach(track => {
        track.enabled = !muted;
      });
    }
  }

  public endCall(): void {
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
    this.callbacks.onConnectionStateChange('closed');
  }
}
