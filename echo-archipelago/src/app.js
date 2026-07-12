"use strict";

import {createGame, startGame, setControl, command, step, getView, serialize, deserialize} from "./game-core.js";
import {AudioEngine} from "./audio-engine.js";
import {LocalRoomTransport, PeerRoomTransport} from "./network.js";

const $ = id => document.getElementById(id);
const stateBox = {state: null};
let audio = new AudioEngine();
let raf = 0;
let previousTime = 0;
let transport = null;
let accessibilityMode = "touch";
let role = "captain";
let roomCode = "";
let lastAnnouncement = 0;

function vibrate(pattern) { try { navigator.vibrate?.(pattern); } catch (_) {} }
function randomRoom() { return Math.random().toString(36).slice(2, 6).toUpperCase(); }

function setMode(mode) {
  accessibilityMode = mode;
  document.body.dataset.accessibility = mode;
  $("modeTouch").setAttribute("aria-pressed", String(mode === "touch"));
  $("modeReader").setAttribute("aria-pressed", String(mode === "reader"));
  $("modeHint").textContent = mode === "reader"
    ? "Режим экранного диктора: все команды — обычные кнопки, действия выполняются одним нажатием."
    : "Режим без VoiceOver: рулевые зоны и газ можно удерживать пальцем; расположение кнопок постоянно.";
}

function newSession(mode, selectedRole = "captain") {
  role = selectedRole;
  stateBox.state = createGame({mode, role});
  render();
}

async function beginSolo() {
  await audio.init();
  transport?.close(); transport = null;
  newSession("solo", "captain");
  startGame(stateBox.state);
  showGame();
  startLoop();
}

async function hostCoop(kind) {
  await audio.init();
  roomCode = ($("roomInput").value.trim() || randomRoom()).toUpperCase();
  $("roomInput").value = roomCode;
  newSession("coop", "captain");
  transport = kind === "peer" ? new PeerRoomTransport(roomCode, "captain") : new LocalRoomTransport(roomCode, "captain");
  setNetworkStatus(`Комната ${roomCode}: ждём второго игрока…`);
  transport.onMessage(handleNetworkMessage);
  try {
    await transport.connect();
    startGame(stateBox.state);
    transport.send({type: "snapshot", state: serialize(stateBox.state)});
    setNetworkStatus(`Комната ${roomCode}: капитан подключён.`);
    showGame(); startLoop();
  } catch (error) {
    setNetworkStatus(`Не удалось открыть комнату: ${error.message}`);
  }
}

async function joinCoop(kind) {
  await audio.init();
  roomCode = $("roomInput").value.trim().toUpperCase();
  if (!roomCode) { setNetworkStatus("Введи четырёхзначный код комнаты."); return; }
  newSession("coop", "crew");
  transport = kind === "peer" ? new PeerRoomTransport(roomCode, "crew") : new LocalRoomTransport(roomCode, "crew");
  transport.onMessage(handleNetworkMessage);
  try {
    await transport.connect();
    transport.send({type: "hello", role: "crew"});
    setNetworkStatus(`Комната ${roomCode}: второй игрок подключён.`);
    showGame(); startLoop();
  } catch (error) {
    setNetworkStatus(`Не удалось войти: ${error.message}`);
  }
}

function handleNetworkMessage(message) {
  if (!message || !stateBox.state) return;
  if (role === "captain") {
    if (message.type === "control") setControl(stateBox.state, message.control, message.active, "crew");
    if (message.type === "command") {
      const result = command(stateBox.state, message.action, "crew");
      audio.handle(result.events);
    }
    if (message.type === "hello") {
      setNetworkStatus(`Комната ${roomCode}: экипаж в сборе.`);
      transport.send({type: "snapshot", state: serialize(stateBox.state)});
    }
  } else if (message.type === "snapshot") {
    stateBox.state = deserialize(message.state);
    stateBox.state.role = "crew";
    render();
  }
}

function showGame() {
  $("startScreen").hidden = true;
  $("gameScreen").hidden = false;
  $("roleLabel").textContent = role === "captain" ? "Капитан" : "Системный оператор";
  document.body.dataset.role = role;
  $("gameTitle").focus();
  render();
}

function startLoop() {
  cancelAnimationFrame(raf);
  previousTime = performance.now();
  const frame = now => {
    const dt = Math.min(0.1, (now - previousTime) / 1000);
    previousTime = now;
    if (stateBox.state?.phase === "playing" && role === "captain") {
      const events = step(stateBox.state, dt);
      audio.handle(events);
      if (transport && Math.floor(now / 100) !== Math.floor((now - dt * 1000) / 100)) {
        transport.send({type: "snapshot", state: serialize(stateBox.state)});
      }
    }
    render();
    raf = requestAnimationFrame(frame);
  };
  raf = requestAnimationFrame(frame);
}

function render() {
  if (!stateBox.state) return;
  const view = getView(stateBox.state);
  $("missionMessage").textContent = view.message;
  $("speed").textContent = `${view.boat.speed.toFixed(1)} узла`;
  $("heading").textContent = `${Math.round((view.boat.heading + 360) % 360)}°`;
  $("hull").textContent = `${Math.round(view.boat.hull)}%`;
  $("water").textContent = `${Math.round(view.boat.water)}%`;
  $("fuel").textContent = `${Math.round(view.boat.fuel)}%`;
  $("temperature").textContent = `${Math.round(view.boat.engineTemp)}°`;
  $("rescued").textContent = `${view.rescued}/2`;
  $("time").textContent = `${Math.ceil(view.remaining)} с`;
  $("quickAction").textContent = view.quickLabel;
  const captainLocked = view.mode === "coop" && role === "crew";
  const crewLocked = view.mode === "coop" && role === "captain";
  for (const id of ["leftButton", "rightButton", "throttleButton", "reverseButton", "anchorButton"]) $(id).disabled = captainLocked;
  for (const id of ["sonarButton", "pumpButton", "rescueButton"]) $(id).disabled = crewLocked;
  $("repairButton").hidden = !view.canRepair;
  $("repairButton").disabled = crewLocked;
  $("pumpButton").classList.toggle("active", view.boat.pumpActive);
  $("engineWarning").hidden = !view.boat.engineStalled && view.boat.engineTemp < 88;
  $("engineWarning").textContent = view.boat.engineStalled ? "Двигатель заглох" : "Двигатель перегревается";
  $("resultPanel").hidden = !(view.won || view.lost);
  if (view.won || view.lost) $("resultText").textContent = `${view.message} Счёт: ${view.score}.`;
  audio.update(view);
  announce(view);
}

function announce(view) {
  const now = performance.now();
  if (now - lastAnnouncement < 1200) return;
  lastAnnouncement = now;
  $("liveStatus").textContent = `${view.message} Скорость ${view.boat.speed.toFixed(1)}. Корпус ${Math.round(view.boat.hull)}. Вода ${Math.round(view.boat.water)}. Спасено ${view.rescued} из двух.`;
}

function sendControl(control, active) {
  if (!stateBox.state) return;
  if (role === "captain") setControl(stateBox.state, control, active, "captain");
  else transport?.send({type: "control", control, active});
}

function sendCommand(action) {
  if (!stateBox.state) return;
  if (role === "captain") {
    const result = command(stateBox.state, action, "captain");
    audio.handle(result.events);
    if (action === "quick" && result.ok) vibrate(18);
  } else transport?.send({type: "command", action});
}

function bindHold(id, control) {
  const button = $(id);
  let active = false;
  const down = event => {
    event.preventDefault();
    active = true;
    sendControl(control, true);
    button.classList.add("held");
    vibrate(8);
  };
  const up = event => {
    if (!active) return;
    event?.preventDefault();
    active = false;
    sendControl(control, false);
    button.classList.remove("held");
  };
  button.addEventListener("pointerdown", down);
  button.addEventListener("pointerup", up);
  button.addEventListener("pointercancel", up);
  button.addEventListener("pointerleave", up);
  button.addEventListener("click", event => {
    if (accessibilityMode !== "reader") return;
    event.preventDefault();
    sendControl(control, true);
    setTimeout(() => sendControl(control, false), 480);
  });
}

function setNetworkStatus(text) { $("networkStatus").textContent = text; }

$("modeTouch").addEventListener("click", () => setMode("touch"));
$("modeReader").addEventListener("click", () => setMode("reader"));
$("soloButton").addEventListener("click", beginSolo);
$("hostLocal").addEventListener("click", () => hostCoop("local"));
$("joinLocal").addEventListener("click", () => joinCoop("local"));
$("hostPeer").addEventListener("click", () => hostCoop("peer"));
$("joinPeer").addEventListener("click", () => joinCoop("peer"));
$("sonarButton").addEventListener("click", () => sendCommand("sonar"));
$("quickAction").addEventListener("click", () => sendCommand("quick"));
$("repairButton").addEventListener("click", () => sendCommand("repair"));
$("anchorButton").addEventListener("click", () => sendCommand("anchor"));
$("soundButton").addEventListener("click", () => {
  audio.setEnabled(!audio.enabled);
  $("soundButton").textContent = `Звук: ${audio.enabled ? "включён" : "выключен"}`;
});
$("restartButton").addEventListener("click", () => location.reload());

bindHold("leftButton", "left");
bindHold("rightButton", "right");
bindHold("throttleButton", "forward");
bindHold("reverseButton", "reverse");
bindHold("pumpButton", "pump");
bindHold("rescueButton", "rescue");

window.addEventListener("keydown", event => {
  if (!stateBox.state) return;
  if (event.key === "ArrowLeft") sendControl("left", true);
  if (event.key === "ArrowRight") sendControl("right", true);
  if (event.key === "ArrowUp") sendControl("forward", true);
  if (event.key === "ArrowDown") sendControl("reverse", true);
  if (event.key.toLowerCase() === "s") sendCommand("sonar");
  if (event.key === " ") { event.preventDefault(); sendCommand("quick"); }
  if (event.key.toLowerCase() === "p") sendControl("pump", true);
  if (event.key.toLowerCase() === "r") sendControl("rescue", true);
});
window.addEventListener("keyup", event => {
  if (event.key === "ArrowLeft") sendControl("left", false);
  if (event.key === "ArrowRight") sendControl("right", false);
  if (event.key === "ArrowUp") sendControl("forward", false);
  if (event.key === "ArrowDown") sendControl("reverse", false);
  if (event.key.toLowerCase() === "p") sendControl("pump", false);
  if (event.key.toLowerCase() === "r") sendControl("rescue", false);
});

setMode("touch");
window.__echoArchipelago = {
  getState: () => stateBox.state,
  setState: value => { stateBox.state = value; render(); },
  command: sendCommand,
  control: sendControl,
  step: seconds => { const events = step(stateBox.state, seconds); audio.handle(events); render(); return events; },
  startSolo: beginSolo,
  getView: () => stateBox.state && getView(stateBox.state),
  setMode,
};
