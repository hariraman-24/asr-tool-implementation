/**
 * MeetBrief - Web Audio API Recorder & Waveform Visualizer
 * Captures 16kHz mono PCM WAV directly in browser for privacy and speed.
 */

class AudioRecorder {
  constructor() {
    this.audioContext = null;
    this.mediaStream = null;
    this.analyser = null;
    this.scriptProcessor = null;
    this.pcmData = [];
    this.isRecording = false;
    this.startTime = null;
    this.timerInterval = null;
    this.animationFrameId = null;
    this.canvas = null;
    this.canvasCtx = null;
  }

  async start(canvasId, timerElementId) {
    if (this.isRecording) return;

    this.pcmData = [];
    this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: 16000
    });

    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true
      }
    });

    const source = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 256;

    // Buffer size 4096, 1 input channel, 1 output channel
    this.scriptProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
    this.scriptProcessor.onaudioprocess = (e) => {
      if (!this.isRecording) return;
      const channelData = e.inputBuffer.getChannelData(0);
      this.pcmData.push(new Float32Array(channelData));
    };

    source.connect(this.analyser);
    this.analyser.connect(this.scriptProcessor);
    this.scriptProcessor.connect(this.audioContext.destination);

    this.isRecording = true;
    this.startTime = Date.now();

    // Start UI timer
    if (timerElementId) {
      const timerEl = document.getElementById(timerElementId);
      this.timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
        const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const s = String(elapsed % 60).padStart(2, '0');
        if (timerEl) timerEl.textContent = `${m}:${s}`;
      }, 500);
    }

    // Start canvas visualizer
    if (canvasId) {
      this.canvas = document.getElementById(canvasId);
      if (this.canvas) {
        this.canvasCtx = this.canvas.getContext('2d');
        this._drawWaveform();
      }
    }
  }

  stop() {
    if (!this.isRecording) return null;

    this.isRecording = false;
    clearInterval(this.timerInterval);
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }

    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
    }

    if (this.audioContext) {
      this.audioContext.close();
    }

    // Clear canvas
    if (this.canvasCtx && this.canvas) {
      this.canvasCtx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    // Merge PCM buffers into standard 16kHz WAV Blob
    return this._encodeWavBlob(this.pcmData, 16000);
  }

  _drawWaveform() {
    if (!this.isRecording || !this.analyser || !this.canvasCtx) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    this.analyser.getByteTimeDomainData(dataArray);

    const width = this.canvas.width;
    const height = this.canvas.height;

    this.canvasCtx.fillStyle = 'rgba(11, 15, 25, 0.4)';
    this.canvasCtx.fillRect(0, 0, width, height);

    this.canvasCtx.lineWidth = 2.5;
    this.canvasCtx.strokeStyle = '#06b6d4';
    this.canvasCtx.beginPath();

    const sliceWidth = width / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
      const v = dataArray[i] / 128.0;
      const y = (v * height) / 2;

      if (i === 0) {
        this.canvasCtx.moveTo(x, y);
      } else {
        this.canvasCtx.lineTo(x, y);
      }
      x += sliceWidth;
    }

    this.canvasCtx.lineTo(width, height / 2);
    this.canvasCtx.stroke();

    this.animationFrameId = requestAnimationFrame(() => this._drawWaveform());
  }

  _encodeWavBlob(buffers, sampleRate) {
    let totalLength = 0;
    for (let buf of buffers) totalLength += buf.length;

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (let buf of buffers) {
      merged.set(buf, offset);
      offset += buf.length;
    }

    // Convert Float32 to 16-bit PCM WAV
    const buffer = new ArrayBuffer(44 + merged.length * 2);
    const view = new DataView(buffer);

    // RIFF chunk
    this._writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + merged.length * 2, true);
    this._writeString(view, 8, 'WAVE');

    // fmt sub-chunk
    this._writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // Linear PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true); // Block align
    view.setUint16(34, 16, true); // Bits per sample

    // data sub-chunk
    this._writeString(view, 36, 'data');
    view.setUint32(40, merged.length * 2, true);

    // Write samples
    let index = 44;
    for (let i = 0; i < merged.length; i++) {
      let s = Math.max(-1, Math.min(1, merged[i]));
      view.setInt16(index, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
      index += 2;
    }

    return new Blob([view], { type: 'audio/wav' });
  }

  _writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }

  // Auditory feedback generator using Web Audio API synthesis
  static playFeedbackSound(type = 'success') {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;
      if (type === 'success') {
        // High-pitched pleasant dual chime
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.setValueAtTime(659.25, now + 0.1); // E5
        osc.frequency.setValueAtTime(783.99, now + 0.2); // G5
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
        osc.start(now);
        osc.stop(now + 0.5);
      } else {
        // Warning low buzz
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(220, now);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.start(now);
        osc.stop(now + 0.35);
      }
    } catch (e) {
      // AudioContext policy fallback
    }
  }
}

window.AudioRecorder = AudioRecorder;
