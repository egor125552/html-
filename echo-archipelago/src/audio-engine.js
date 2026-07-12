"use strict";

const ROOT = "https://raw.githubusercontent.com/lavenderdotpet/CC0-Public-Domain-Sounds/main/";
export const SOUND_URLS = Object.freeze({
  water: ROOT + "40-cc0-water-splash-slime-sfx/loop_water_03.ogg",
  rain: ROOT + "40-cc0-water-splash-slime-sfx/loop_rain.ogg",
  engine: ROOT + "30-cc0-sfx-loops/machine_03.ogg",
  pump: ROOT + "30-cc0-sfx-loops/pump_01.ogg",
  sonar: ROOT + "50-cc0-sci-fi-sfx/beep_02.ogg",
  sonarNear: ROOT + "50-cc0-sci-fi-sfx/beep_03.ogg",
  collision: ROOT + "100-CC0-wood-metal-SFX/metal_hit_03.ogg",
  splash: ROOT + "40-cc0-water-splash-slime-sfx/splash_06.ogg",
  rope: ROOT + "100-CC0-wood-metal-SFX/wood_hit_04.ogg",
  rescue: ROOT + "50-cc0-sci-fi-sfx/terminal_04.ogg",
  repair: ROOT + "100-cc0-sfx-2/sfx100v2_metal_04.ogg",
  win: ROOT + "50-cc0-sci-fi-sfx/terminal_09.ogg",
  deny: ROOT + "50-cc0-sci-fi-sfx/retro_beep_02.ogg",
});

export class AudioEngine {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.buffers = new Map();
    this.loops = new Map();
    this.enabled = true;
  }
  async init() {
    if (this.ctx) return;
    const AC = globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.8;
    this.master.connect(this.ctx.destination);
    await this.ctx.resume();
    this.preload();
  }
  setEnabled(enabled) {
    this.enabled = Boolean(enabled);
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(this.enabled ? 0.8 : 0.0001, this.ctx.currentTime, 0.03);
  }
  async preload() {
    if (!this.ctx) return;
    await Promise.allSettled(Object.entries(SOUND_URLS).map(async ([name, url]) => {
      const response = await fetch(url, {mode: "cors", cache: "force-cache"});
      if (!response.ok) throw new Error(`${name}: ${response.status}`);
      const buffer = await this.ctx.decodeAudioData(await response.arrayBuffer());
      this.buffers.set(name, buffer);
    }));
  }
  play(name, options = {}) {
    if (!this.enabled || !this.ctx || !this.master) return;
    const buffer = this.buffers.get(name);
    if (!buffer) return;
    const source = this.ctx.createBufferSource();
    const gain = this.ctx.createGain();
    const panner = this.ctx.createStereoPanner();
    source.buffer = buffer;
    source.playbackRate.value = options.rate || 1;
    source.loop = Boolean(options.loop);
    gain.gain.value = options.gain ?? 0.7;
    panner.pan.value = Math.max(-1, Math.min(1, options.pan || 0));
    source.connect(panner).connect(gain).connect(this.master);
    source.start();
    if (options.loop) this.loops.set(name, {source, gain, panner});
    source.onended = () => { if (this.loops.get(name)?.source === source) this.loops.delete(name); };
    return source;
  }
  ensureLoop(name, options = {}) {
    if (!this.loops.has(name)) this.play(name, {...options, loop: true});
    const loop = this.loops.get(name);
    if (loop && this.ctx) {
      loop.gain.gain.setTargetAtTime(options.gain ?? 0.35, this.ctx.currentTime, 0.12);
      loop.panner.pan.setTargetAtTime(options.pan || 0, this.ctx.currentTime, 0.12);
      loop.source.playbackRate.setTargetAtTime(options.rate || 1, this.ctx.currentTime, 0.12);
    }
  }
  stopLoop(name) {
    const loop = this.loops.get(name);
    if (!loop) return;
    try { loop.source.stop(); } catch (_) {}
    this.loops.delete(name);
  }
  update(view) {
    if (!this.ctx) return;
    this.ensureLoop("water", {gain: 0.24 + Math.min(0.18, Math.abs(view.boat.speed) / 70), rate: 0.9 + Math.abs(view.boat.speed) / 45});
    this.ensureLoop("rain", {gain: 0.08});
    if (!view.boat.engineStalled && view.phase === "playing") {
      this.ensureLoop("engine", {gain: 0.12 + Math.abs(view.boat.throttle) * 0.23, rate: 0.72 + Math.abs(view.boat.throttle) * 0.72});
    } else this.stopLoop("engine");
    if (view.boat.pumpActive) this.ensureLoop("pump", {gain: 0.32, rate: 1});
    else this.stopLoop("pump");
  }
  handle(events) {
    for (const event of events || []) {
      if (event.type === "sonar") {
        const name = event.distance < 28 ? "sonarNear" : "sonar";
        this.play(name, {pan: event.pan || 0, gain: 0.68, rate: Math.max(0.72, 1.45 - event.distance / 130)});
      } else if (event.type === "collision") {
        this.play("collision", {pan: event.pan || 0, gain: 0.9});
        this.play("splash", {pan: event.pan || 0, gain: 0.68});
      } else if (event.type === "rope") this.play("rope", {gain: 0.7});
      else if (event.type === "rescue-complete") this.play("rescue", {gain: 0.75});
      else if (event.type === "repair" || event.type === "repair-complete") this.play("repair", {gain: 0.65});
      else if (event.type === "win") this.play("win", {gain: 0.9});
      else if (event.type === "ui-deny") this.play("deny", {gain: 0.5});
    }
  }
}
