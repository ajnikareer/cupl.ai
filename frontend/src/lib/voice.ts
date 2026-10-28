import { API_BASE, idToken } from "./api";

// Mic capture: any device sample rate -> 16 kHz mono PCM16, 40 ms frames (box-filter downsampling)
const REC_WORKLET = `
class Rec extends AudioWorkletProcessor {
  constructor(){ super(); this.ratio = sampleRate / 16000; this.pos = 0; this.acc = 0; this.n = 0; this.out = []; }
  process(inputs){
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      this.acc += ch[i]; this.n++; this.pos += 1;
      if (this.pos >= this.ratio) { this.pos -= this.ratio; this.out.push(this.acc / this.n); this.acc = 0; this.n = 0; }
    }
    if (this.out.length >= 640) {
      const pcm = new Int16Array(this.out.length);
      for (let i = 0; i < this.out.length; i++) { const s = Math.max(-1, Math.min(1, this.out[i])); pcm[i] = s < 0 ? s * 0x8000 : s * 0x7fff; }
      this.port.postMessage(pcm.buffer, [pcm.buffer]);
      this.out = [];
    }
    return true;
  }
}
registerProcessor('ww-rec', Rec);`;

export type VoiceState = "off" | "connecting" | "listening" | "speaking" | "reconnecting";

export class VoiceSession {
  ws?: WebSocket;
  ctx?: AudioContext;
  stream?: MediaStream;
  node?: AudioWorkletNode;
  inAnalyser?: AnalyserNode;
  outAnalyser?: AnalyserNode;
  outGain?: GainNode;
  nextTime = 0;
  sources: AudioBufferSourceNode[] = [];
  stopped = false;
  constructor(public onEvent: (ev: any) => void, public onState: (s: VoiceState) => void) {}

  async start() {
    this.onState("connecting");
    // AudioContext must be created inside the user's tap (iOS/Safari)
    this.ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    await this.ctx.resume();
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 } });
    const url = URL.createObjectURL(new Blob([REC_WORKLET], { type: "application/javascript" }));
    await this.ctx.audioWorklet.addModule(url);
    const src = this.ctx.createMediaStreamSource(this.stream);
    this.inAnalyser = this.ctx.createAnalyser(); this.inAnalyser.fftSize = 256;
    this.node = new AudioWorkletNode(this.ctx, "ww-rec");
    src.connect(this.inAnalyser); src.connect(this.node);
    this.outGain = this.ctx.createGain();
    this.outAnalyser = this.ctx.createAnalyser(); this.outAnalyser.fftSize = 256;
    this.outGain.connect(this.outAnalyser); this.outAnalyser.connect(this.ctx.destination);

    const wsBase = API_BASE
      ? API_BASE.replace(/^http/, "ws")
      : `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`;
    const ws = new WebSocket(wsBase + "/ws/voice");
    ws.binaryType = "arraybuffer";
    this.ws = ws;
    ws.onopen = async () => ws.send(JSON.stringify({ type: "start", token: await idToken() }));
    ws.onmessage = (m) => {
      if (typeof m.data !== "string") { this.play(m.data as ArrayBuffer); return; }
      const ev = JSON.parse(m.data);
      if (ev.type === "ready") this.onState(this.sources.length ? "speaking" : "listening");
      if (ev.type === "reconnecting") this.onState("reconnecting");
      if (ev.type === "interrupted") this.flush();
      this.onEvent(ev);
    };
    ws.onclose = () => this.stop(false);
    ws.onerror = () => this.onEvent({ type: "error", message: "Voice connection failed. You can keep chatting by text." });
    this.node.port.onmessage = (e) => { if (ws.readyState === WebSocket.OPEN) ws.send(e.data); };
  }

  play(buf: ArrayBuffer) {
    if (!this.ctx || !this.outGain || buf.byteLength < 2) return;
    const pcm = new Int16Array(buf, 0, Math.floor(buf.byteLength / 2));
    const f = new Float32Array(pcm.length);
    for (let i = 0; i < pcm.length; i++) f[i] = pcm[i] / 32768;
    const ab = this.ctx.createBuffer(1, f.length, 24000);   // browser resamples to device rate
    ab.copyToChannel(f, 0);
    const s = this.ctx.createBufferSource();
    s.buffer = ab;
    s.connect(this.outGain);
    const t = Math.max(this.ctx.currentTime + 0.03, this.nextTime);
    s.start(t);
    this.nextTime = t + ab.duration;
    this.sources.push(s);
    this.onState("speaking");
    s.onended = () => {
      this.sources = this.sources.filter((x) => x !== s);
      if (!this.sources.length && !this.stopped) this.onState("listening");
    };
  }

  flush() {
    this.sources.forEach((s) => { try { s.onended = null; s.stop(); } catch {} });
    this.sources = [];
    this.nextTime = 0;
    if (!this.stopped) this.onState("listening");
  }

  level(which: "in" | "out"): number {
    const a = which === "in" ? this.inAnalyser : this.outAnalyser;
    if (!a) return 0;
    const d = new Uint8Array(a.frequencyBinCount);
    a.getByteTimeDomainData(d);
    let sum = 0;
    for (let i = 0; i < d.length; i++) { const v = (d[i] - 128) / 128; sum += v * v; }
    return Math.min(1, Math.sqrt(sum / d.length) * 4);
  }

  sendJson(obj: any) { if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify(obj)); }

  stop(sendStop = true) {
    if (this.stopped) return;
    this.stopped = true;
    if (sendStop) this.sendJson({ type: "stop" });
    try { this.ws?.close(); } catch {}
    this.flush();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.ctx?.close().catch(() => {});
    this.onState("off");
  }
}
