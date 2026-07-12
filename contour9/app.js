const $ = (id) => document.getElementById(id);
let currentState = null;
let audioEnabled = true;
let speechEnabled = true;
const SPEECH_RATE = 0.55;
let audio = null;
let lastMessage = "";
let lastNarration = "";
let selectedVoice = null;

class AudioEngine {
  constructor() {
    this.ctx = null;
    this.master = null;
    this.ambient = null;
    this.loaded = new Map();
    const remote = "https://raw.githubusercontent.com/lavenderdotpet/CC0-Public-Domain-Sounds/main/100-cc0-sfx-2/";
    this.urls = {
      footstep: [remote + "sfx100v2_footstep_01.ogg"],
      door: [remote + "sfx100v2_door_02.ogg"],
      lock: [remote + "sfx100v2_lock_open_01.ogg"],
      pickup: [remote + "sfx100v2_items_02.ogg"],
      metal: [remote + "sfx100v2_metal_04.ogg"],
      switch: [remote + "sfx100v2_switch_02.ogg"],
      rain: [remote + "sfx100v2_loop_water_03.ogg"],
    };
  }
  async init() {
    if (this.ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    this.ctx = new AC();
    this.master = this.ctx.createGain();
    this.master.gain.value = 0.72;
    this.master.connect(this.ctx.destination);
    await this.ctx.resume();
    this.startAmbient();
    this.preload();
  }
  setEnabled(value) {
    audioEnabled = value;
    if (this.master && this.ctx) this.master.gain.setTargetAtTime(value ? 0.72 : 0.0001, this.ctx.currentTime, 0.02);
  }
  setSpeechDucking(active) {
    if (!this.master || !this.ctx || !audioEnabled) return;
    this.master.gain.setTargetAtTime(active ? 0.22 : 0.72, this.ctx.currentTime, 0.05);
  }
  async preload() {
    if (!this.ctx) return;
    for (const [name, candidates] of Object.entries(this.urls)) {
      for (const url of candidates) {
        try {
          const response = await fetch(url, {cache: "force-cache", mode: "cors"});
          if (!response.ok) continue;
          const data = await response.arrayBuffer();
          const buffer = await this.ctx.decodeAudioData(data.slice(0));
          this.loaded.set(name, buffer);
          break;
        } catch (_) {}
      }
    }
  }
  startAmbient() {
    if (!this.ctx || this.ambient) return;
    const osc = this.ctx.createOscillator();
    const filter = this.ctx.createBiquadFilter();
    const gain = this.ctx.createGain();
    osc.type = "sawtooth";
    osc.frequency.value = 47;
    filter.type = "lowpass";
    filter.frequency.value = 145;
    gain.gain.value = 0.035;
    osc.connect(filter).connect(gain).connect(this.master);
    osc.start();
    this.ambient = {osc, filter, gain};
  }
  room(name) {
    if (!this.ambient || !this.ctx) return;
    const freq = {cell:115,corridor:160,pump:210,workshop:145,storage:125,control:185,exit:100}[name] || 145;
    this.ambient.filter.frequency.setTargetAtTime(freq, this.ctx.currentTime, 0.25);
  }
  playEvents(events = []) {
    if (!audioEnabled || !this.ctx) return;
    for (const event of events) {
      const delay = Number(event.delay || 0);
      setTimeout(() => this.play(event.sound, event.pan || 0, event.gain || 0.7), delay * 1000);
    }
  }
  play(name, pan = 0, gain = 0.7) {
    if (!audioEnabled || !this.ctx) return;
    const buffer = this.loaded.get(name);
    if (buffer) {
      const source = this.ctx.createBufferSource();
      const panner = this.ctx.createStereoPanner();
      const g = this.ctx.createGain();
      panner.pan.value = Math.max(-1, Math.min(1, pan));
      g.gain.value = gain;
      source.buffer = buffer;
      source.connect(panner).connect(g).connect(this.master);
      source.start();
      return;
    }
    this.synth(name, pan, gain);
  }
  synth(name, pan = 0, gain = 0.7) {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    const panner = this.ctx.createStereoPanner();
    const g = this.ctx.createGain();
    panner.pan.value = Math.max(-1, Math.min(1, pan));
    g.gain.setValueAtTime(0.0001, now);
    g.gain.exponentialRampToValueAtTime(Math.max(0.001, gain * 0.22), now + 0.01);
    g.connect(panner).connect(this.master);
    const tone = (freq, dur, type = "sine", endFreq = null) => {
      const osc = this.ctx.createOscillator();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, now);
      if (endFreq) osc.frequency.exponentialRampToValueAtTime(endFreq, now + dur);
      osc.connect(g);
      osc.start(now);
      g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
      osc.stop(now + dur + 0.03);
    };
    if (name === "tone_low") tone(170,.42,"sine",155);
    else if (name === "tone_mid") tone(390,.38,"sine",410);
    else if (name === "tone_high") tone(820,.34,"sine",900);
    else if (name === "alarm") { tone(480,.65,"square",410); setTimeout(() => this.synth("alarm_tail",pan,gain*.7),720); }
    else if (name === "alarm_tail") tone(360,.4,"square",310);
    else if (name === "success") { tone(330,.7,"sine",660); setTimeout(() => this.synth("tone_high",.35,.7),420); }
    else if (name === "fail" || name === "locked") tone(180,.28,"square",92);
    else if (name === "shock" || name === "electric") tone(960,.24,"sawtooth",120);
    else if (name === "scan") tone(240,.45,"sine",760);
    else if (name === "footstep") tone(88,.12,"triangle",58);
    else if (name === "door" || name === "metal") tone(130,.42,"sawtooth",48);
    else if (name === "pickup" || name === "switch" || name === "lock") tone(520,.2,"triangle",740);
    else if (name === "rain") this.noiseBurst(2.7,.12);
    else tone(260,.18,"sine",320);
  }
  noiseBurst(duration = .3, volume = .12) {
    if (!this.ctx) return;
    const length = Math.floor(this.ctx.sampleRate * duration);
    const buffer = this.ctx.createBuffer(1, length, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i=0;i<length;i++) data[i]=(Math.random()*2-1)*(1-i/length);
    const source=this.ctx.createBufferSource();
    const filter=this.ctx.createBiquadFilter();
    const gain=this.ctx.createGain();
    filter.type="bandpass"; filter.frequency.value=1300; gain.gain.value=volume;
    source.buffer=buffer; source.connect(filter).connect(gain).connect(this.master); source.start();
  }
}

function refreshVoice() {
  if (!("speechSynthesis" in window)) return;
  const voices = window.speechSynthesis.getVoices();
  selectedVoice = voices.find(v => /^ru([-_]|$)/i.test(v.lang) && /milena|yuri|katya|russian/i.test(v.name))
    || voices.find(v => /^ru([-_]|$)/i.test(v.lang))
    || null;
}

function speak(text, interrupt = true) {
  if (!speechEnabled || !("speechSynthesis" in window) || !text) return;
  if (interrupt) window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = "ru-RU";
  utterance.rate = SPEECH_RATE;
  utterance.pitch = 1;
  utterance.volume = 1;
  if (selectedVoice) utterance.voice = selectedVoice;
  utterance.onstart = () => audio?.setSpeechDucking(true);
  utterance.onend = utterance.onerror = () => audio?.setSpeechDucking(false);
  window.speechSynthesis.speak(utterance);
}

function narrationFor(state, full = false) {
  const parts = [];
  if (full) parts.push(`Помещение: ${state.room_name}. ${state.description}`);
  parts.push(state.message);
  parts.push(`Текущая цель: ${state.objective}`);
  if (state.known_code) parts.push("Известный код выхода: 2, 8, 5.");
  if (state.countdown != null) parts.push(`До блокировки осталось ходов: ${state.countdown}.`);
  if (full) {
    const actionLabels = state.actions.filter(a => a.id !== "new_game").map(a => a.label);
    const moveLabels = state.exits.filter(e => !e.locked).map(e => `перейти в ${e.target}`);
    if (actionLabels.length) parts.push(`Доступные действия: ${actionLabels.join("; ")}.`);
    if (moveLabels.length) parts.push(`Доступные переходы: ${moveLabels.join("; ")}.`);
  }
  if (state.won && state.score != null) parts.push(`Счёт: ${state.score}.`);
  return parts.join(" ");
}

function announceState(full = false) {
  if (!currentState) return;
  const state = view(currentState);
  lastNarration = narrationFor(state, full);
  speak(lastNarration);
}

function loadState() {
  try {
    const raw = sessionStorage.getItem("contour9-preview-state");
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return makeState();
}
function saveState() {
  try { sessionStorage.setItem("contour9-preview-state", JSON.stringify(currentState)); } catch (_) {}
}
function perform(action, value = null) {
  const beforeRoom = currentState?.room;
  const result = applyAction(currentState, action, value);
  currentState = result.state;
  saveState();
  const stateView = view(currentState);
  render(stateView);
  audio?.playEvents(result.events);
  const changedRoom = beforeRoom !== currentState.room;
  lastNarration = narrationFor(stateView, changedRoom || action === "new_game");
  setTimeout(() => speak(lastNarration), changedRoom ? 260 : 120);
  return result;
}
function render(state) {
  lastMessage = state.message;
  $("roomName").textContent = state.room_name;
  $("description").textContent = state.description;
  $("message").textContent = state.message;
  $("objective").textContent = state.objective;
  $("turns").textContent = String(state.turns);
  $("mistakes").textContent = String(state.mistakes);
  $("countdown").textContent = state.countdown == null ? "неактивна" : `${state.countdown} ходов`;
  $("countdown").classList.toggle("danger", state.countdown != null && state.countdown <= 3);
  $("knownCode").textContent = state.known_code ? "285" : "ещё не найден";
  $("inventory").textContent = state.inventory.length ? state.inventory.join(", ") : "Пусто";
  $("codePanel").hidden = !(state.room === "exit" && !state.won);
  $("codeHint").textContent = state.known_code ? "Известный код выхода: 285. Введи цифры 2, 8, 5." : "Код ещё не найден. Почини аварийное радио в мастерской.";
  $("repeatCodeButton").hidden = !state.known_code;
  document.querySelector(".location").classList.toggle("win", state.won);
  const actions=$("actions"); actions.innerHTML="";
  for(const action of state.actions) {
    const button=document.createElement("button");
    button.textContent=`${action.label}${action.key ? ` — ${action.key}` : ""}`;
    button.dataset.action=action.id;
    button.addEventListener("click",()=>action.id === "new_game" ? newGame() : perform(action.id));
    actions.appendChild(button);
  }
  const moves=$("moves"); moves.innerHTML="";
  for(const exit of state.exits) {
    const button=document.createElement("button");
    button.textContent=`Перейти в ${exit.target}${exit.locked ? ` — закрыто: ${exit.reason}` : ""}`;
    button.disabled=exit.locked;
    button.dataset.direction=exit.direction;
    button.addEventListener("click",()=>perform(`move_${exit.direction}`));
    moves.appendChild(button);
  }
  const log=$("log"); log.innerHTML="";
  for(const entry of state.log) { const li=document.createElement("li"); li.textContent=entry; log.appendChild(li); }
  audio?.room(state.room);
}
function newGame() {
  currentState=makeState();
  saveState();
  $("codeInput").value="";
  render(view(currentState));
  audio?.playEvents([{sound:"success",pan:0,gain:.5}]);
  setTimeout(() => announceState(true), 120);
}
function availableAction(id) { return view(currentState).actions.some(a=>a.id===id); }
function move(direction) {
  const exit=view(currentState).exits.find(e=>e.direction===direction && !e.locked);
  if(exit) perform(`move_${direction}`);
  else audio?.play("locked",direction==="west"?-0.8:direction==="east"?0.8:0,.6);
}

$("startButton").addEventListener("click",async()=>{
  audio=new AudioEngine();
  try { await audio.init(); } catch (_) {}
  currentState=loadState();
  render(view(currentState));
  $("startPanel").hidden=true;
  $("playPanel").hidden=false;
  audio.play("success",0,.45);
  refreshVoice();
  setTimeout(() => announceState(true), 180);
  $("roomName").focus();
});
$("repeatButton").addEventListener("click",()=>{
  audio?.play("scan",0,.35);
  announceState(true);
});
$("speechButton").addEventListener("click",()=>{
  speechEnabled = !speechEnabled;
  if (!speechEnabled && "speechSynthesis" in window) window.speechSynthesis.cancel();
  $("speechButton").setAttribute("aria-pressed", String(speechEnabled));
  $("speechButton").textContent = `Синтез речи: ${speechEnabled ? "включён" : "выключен"}`;
  if (speechEnabled) speak("Синтез речи включён. Скорость 55 процентов.");
});
$("soundButton").addEventListener("click",()=>{
  audioEnabled=!audioEnabled; audio?.setEnabled(audioEnabled);
  $("soundButton").setAttribute("aria-pressed",String(audioEnabled));
  $("soundButton").textContent=`Звук: ${audioEnabled?"включен":"выключен"}`;
});
$("newButton").addEventListener("click",newGame);
$("submitCode").addEventListener("click",()=>perform("enter_code",$("codeInput").value));
$("repeatCodeButton").addEventListener("click",()=>perform("repeat_code"));
$("codeInput").addEventListener("keydown",event=>{ if(event.key==="Enter") perform("enter_code",$("codeInput").value); });
document.addEventListener("keydown",event=>{
  if(!currentState || event.target===$("codeInput")) return;
  const key=event.key.toLowerCase();
  if(key==="arrowup"){event.preventDefault();move("north");}
  else if(key==="arrowdown"){event.preventDefault();move("south");}
  else if(key==="arrowleft"){event.preventDefault();move("west");}
  else if(key==="arrowright"){event.preventDefault();move("east");}
  else if(key==="i"&&availableAction("inspect"))perform("inspect");
  else if(key==="l"&&availableAction("listen"))perform("listen");
  else if(key==="r")$("repeatButton").click();
  else if(key==="c"&&availableAction("repeat_code"))perform("repeat_code");
  else if(key==="v")$("speechButton").click();
  else if(key==="m")$("soundButton").click();
  else if(key==="n")newGame();
  else if(/^[1-9]$/.test(key)){
    const candidates=view(currentState).actions.filter(a=>a.key===key);
    if(candidates.length) candidates[0].id==="enter_code" ? $("codeInput").focus() : perform(candidates[0].id);
  }
});
if ("speechSynthesis" in window) { refreshVoice(); window.speechSynthesis.onvoiceschanged = refreshVoice; }
window.__contour9={makeState,applyAction,view,perform,newGame,narrationFor,announceState,getState:()=>cloneState(currentState),speechRate:SPEECH_RATE};
