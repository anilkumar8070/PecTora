export interface VADCallbacks {
  onSpeechStart: () => void;
  onSpeechEnd: (audioBlob: Blob) => void;
}

export class VADService {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private mediaRecorder: MediaRecorder | null = null;
  private audioChunks: Blob[] = [];
  
  private silenceTimer: number | null = null;
  private monitorInterval: number | null = null;
  private isSpeaking = false;
  
  // Configurable thresholds
  private readonly silenceThresholdMs = 1500; // 1.5 seconds of silence means turn is over
  private readonly volumeThreshold = 10; // minimum amplitude out of 255 to be considered speech

  constructor(private stream: MediaStream, private callbacks: VADCallbacks) {}

  public start() {
    this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const source = this.audioContext.createMediaStreamSource(this.stream);
    
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 512;
    this.analyser.smoothingTimeConstant = 0.4;
    source.connect(this.analyser);

    // Prepare recording
    this.mediaRecorder = new MediaRecorder(this.stream);
    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.audioChunks.push(e.data);
    };

    this.mediaRecorder.onstop = () => {
      const blob = new Blob(this.audioChunks, { type: 'audio/webm' });
      this.audioChunks = [];
      this.callbacks.onSpeechEnd(blob);
    };

    // Start continuous analysis
    this.monitor();
  }

  private monitor() {
    if (!this.analyser) return;
    
    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    
    this.monitorInterval = window.setInterval(() => {
      if (!this.analyser) return;
      this.analyser.getByteFrequencyData(dataArray);
      
      // Calculate average volume
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sum += dataArray[i];
      }
      const averageVolume = sum / dataArray.length;

      if (averageVolume > this.volumeThreshold) {
        // Human is speaking
        if (!this.isSpeaking) {
          this.isSpeaking = true;
          this.callbacks.onSpeechStart();
          if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
            this.mediaRecorder.start(100); // chunk every 100ms
          }
        }
        
        // Reset silence timer since we heard noise
        if (this.silenceTimer) {
          clearTimeout(this.silenceTimer);
          this.silenceTimer = null;
        }
      } else {
        // Silence
        if (this.isSpeaking && !this.silenceTimer) {
          this.silenceTimer = window.setTimeout(() => {
            // Human stopped speaking
            this.isSpeaking = false;
            if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
              this.mediaRecorder.stop();
            }
          }, this.silenceThresholdMs);
        }
      }
    }, 100);
  }

  public stop() {
    if (this.monitorInterval) clearInterval(this.monitorInterval);
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
    }
    if (this.audioContext) {
      this.audioContext.close();
    }
  }
}
