"use strict";
(() => {
  const TARGET_RATE = 0.76;
  const STORAGE_KEY = "contour9-v5-repeat-handled";
  let installed = false;
  let voiceStatus = null;

  const normalize = value => String(value || "").toLowerCase().replace(/ё/g, "е");

  function voiceScore(voice) {
    const name = normalize(`${voice.name} ${voice.voiceURI}`);
    const lang = normalize(voice.lang);
    if (!lang.startsWith("ru")) return -10000;
    let score = 10;
    if (/milena|милена/.test(name)) score += 1000;
    if (/enhanced|premium|improved|high.?quality|natural|neural|улучш/.test(name)) score += 500;
    if (/compact|компакт/.test(name)) score -= 160;
    if (voice.localService) score += 15;
    return score;
  }

  function chooseVoice() {
    if (!("speechSynthesis" in window)) return null;
    const voices = window.speechSynthesis.getVoices();
    return [...voices].sort((a, b) => voiceScore(b) - voiceScore(a))[0] || null;
  }

  function isEnhancedMilena(voice) {
    if (!voice) return false;
    const name = normalize(`${voice.name} ${voice.voiceURI}`);
    return /milena|милена/.test(name) && /enhanced|premium|improved|high.?quality|natural|neural|улучш/.test(name) && !/compact|компакт/.test(name);
  }

  function updateVoiceStatus() {
    const voice = chooseVoice();
    if (voiceStatus) {
      const quality = isEnhancedMilena(voice)
        ? "улучшенная версия"
        : /milena|милена/.test(normalize(voice?.name))
          ? "обычная версия; улучшенная не найдена в системе"
          : "резервный русский голос";
      voiceStatus.textContent = `Голос игры: ${voice?.name || "русский системный"}. ${quality}. Скорость: 76 процентов.`;
    }
    try {
      if (typeof selectedVoice !== "undefined") selectedVoice = voice;
    } catch (_) {}
    return voice;
  }

  function installVoicePolicy() {
    if (!("speechSynthesis" in window)) return;
    const synth = window.speechSynthesis;
    if (!synth.__contour9NativeSpeak) {
      const nativeSpeak = synth.speak.bind(synth);
      Object.defineProperty(synth, "__contour9NativeSpeak", {value: nativeSpeak, configurable: true});
      const forcedSpeak = utterance => {
        if (utterance) {
          utterance.lang = "ru-RU";
          utterance.rate = TARGET_RATE;
          const voice = chooseVoice();
          if (voice) utterance.voice = voice;
        }
        return nativeSpeak(utterance);
      };
      try {
        synth.speak = forcedSpeak;
      } catch (_) {
        try { Object.defineProperty(synth, "speak", {value: forcedSpeak, configurable: true}); } catch (_) {}
      }
    }
    const previous = synth.onvoiceschanged;
    synth.onvoiceschanged = event => {
      if (typeof previous === "function") {
        try { previous.call(synth, event); } catch (_) {}
      }
      updateVoiceStatus();
    };
    updateVoiceStatus();
  }

  function addVoiceControls() {
    const speechButton = document.getElementById("speechButton");
    if (!speechButton || document.getElementById("voiceStatus")) return;
    const section = speechButton.closest("details") || speechButton.parentElement;
    const row = speechButton.parentElement;
    voiceStatus = document.createElement("p");
    voiceStatus.id = "voiceStatus";
    voiceStatus.className = "section-help";
    voiceStatus.setAttribute("role", "status");
    voiceStatus.setAttribute("aria-live", "polite");
    row.parentElement.insertBefore(voiceStatus, row);

    const test = document.createElement("button");
    test.id = "voiceTestButton";
    test.type = "button";
    test.textContent = "Проверить Милену и скорость 76 процентов";
    test.addEventListener("click", () => {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance("Проверка голоса. Я Милена. Скорость речи установлена на семьдесят шесть процентов.");
      utterance.lang = "ru-RU";
      utterance.rate = TARGET_RATE;
      const voice = updateVoiceStatus();
      if (voice) utterance.voice = voice;
      window.speechSynthesis.speak(utterance);
    });
    row.appendChild(test);
    speechButton.textContent = "Синтез речи: включён, скорость 76 процентов";
    updateVoiceStatus();
  }

  function readHandled() {
    try { return new Set(JSON.parse(sessionStorage.getItem(STORAGE_KEY) || "[]")); }
    catch (_) { return new Set(); }
  }

  function saveHandled(set) {
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...set].slice(-300))); } catch (_) {}
  }

  function findRepeatCountInState(root) {
    const numbers = [];
    const seen = new WeakSet();
    function walk(value, path, depth) {
      if (depth > 5 || value == null) return;
      if (typeof value === "number" && /repeat|повтор|interaction.?count|action.?count/i.test(path)) {
        numbers.push(value);
        return;
      }
      if (typeof value !== "object" || seen.has(value)) return;
      seen.add(value);
      for (const [key, child] of Object.entries(value)) walk(child, `${path}.${key}`, depth + 1);
    }
    walk(root, "state", 0);
    return numbers.length ? Math.max(...numbers) : null;
  }

  function numberFromButton(button) {
    const matches = [...String(button?.textContent || "").matchAll(/(\d+)/g)];
    return matches.length ? Number(matches[matches.length - 1][1]) : null;
  }

  function bump(container, key, delta, min = -Infinity, max = Infinity) {
    if (!container || typeof container !== "object" || typeof container[key] !== "number") return false;
    container[key] = Math.max(min, Math.min(max, container[key] + delta));
    return true;
  }

  function bumpAnywhere(state, keys, delta, min, max) {
    let changed = false;
    for (const key of keys) {
      changed = bump(state, key, delta, min, max) || changed;
      changed = bump(state.stats, key, delta, min, max) || changed;
      changed = bump(state.metrics, key, delta, min, max) || changed;
    }
    return changed;
  }

  function classifyAction(button) {
    const text = normalize(`${button.dataset.action || ""} ${button.textContent || ""}`);
    if (/удар|пнут|kick|hit|break|лом|толк/.test(text)) return "destructive";
    if (/говор|спрос|успоко|стуч|knock|talk|шеп/.test(text)) return "social";
    if (/осмотр|слуш|трог|inspect|listen|touch/.test(text)) return "observe";
    return "neutral";
  }

  function consequenceText(kind, count, objectName) {
    const object = objectName || "объект";
    const major = count % 5 === 0;
    if (kind === "destructive") {
      return major
        ? `Это уже ${count}-е силовое воздействие на ${object}. Материал окончательно меняет состояние: растут повреждения и шум, а дальнейшие события учитывают разрушение.`
        : `${count}-е силовое воздействие на ${object} оставляет новый след. Шум и износ продолжают накапливаться.`;
    }
    if (kind === "social") {
      return major
        ? `Ты повторяешь обращение ${count}-й раз. Люди больше не считают это случайностью и меняют отношение к тебе.`
        : `Это ${count}-е обращение. Собеседники запоминают настойчивость, и доверие понемногу меняется.`;
    }
    if (kind === "observe") {
      return major
        ? `После ${count} повторов ты замечаешь деталь, которую раньше пропускал. Наблюдательность открывает дополнительную информацию.`
        : `Повторный осмотр номер ${count} даёт ещё одну небольшую деталь.`;
    }
    return major
      ? `${count} повторов заставляют систему отреагировать заметно иначе.`
      : `Повтор номер ${count} немного меняет состояние окружения.`;
  }

  function applyExtendedRepeat(button) {
    let state = null;
    try { if (typeof currentState !== "undefined") state = currentState; } catch (_) {}
    const selected = document.getElementById("objectSelect");
    const objectName = selected?.selectedOptions?.[0]?.textContent || selected?.value || "объект";
    let count = state ? findRepeatCountInState(state) : null;
    if (count == null || count < 11) count = numberFromButton(document.querySelector(`[data-action="${CSS.escape(button.dataset.action || "")}"]`)) || numberFromButton(button);
    if (!Number.isFinite(count) || count <= 10) return;

    const key = `${selected?.value || "room"}:${button.dataset.action || normalize(button.textContent)}:${count}`;
    const handled = readHandled();
    if (handled.has(key)) return;
    handled.add(key);
    saveHandled(handled);

    const kind = classifyAction(button);
    const text = consequenceText(kind, count, objectName);
    if (state) {
      if (kind === "destructive") {
        bumpAnywhere(state, ["noise", "шум"], 1, 0, 100);
        if (count % 3 === 0) bumpAnywhere(state, ["damage", "destruction", "повреждения"], 1, 0, 100);
        if (count % 10 === 0) bumpAnywhere(state, ["health", "здоровье"], -1, 1, 100);
      } else if (kind === "social") {
        bumpAnywhere(state, ["trust", "доверие"], count % 5 === 0 ? 2 : 1, -100, 100);
      } else if (kind === "observe") {
        bumpAnywhere(state, ["insight", "awareness", "observation", "наблюдательность"], 1, 0, 100);
      }
      if (!state.flags || typeof state.flags !== "object") state.flags = {};
      state.flags[`extended_repeat_${kind}_${count}`] = true;
      state.message = text;
      if (Array.isArray(state.log)) {
        state.log.push(text);
        state.log = state.log.slice(-30);
      }
      try { if (typeof saveState === "function") saveState(); } catch (_) {}
      try { if (typeof render === "function" && typeof view === "function") render(view(state)); } catch (_) {}
    } else {
      const message = document.getElementById("message");
      if (message) message.textContent = text;
    }
    try {
      if (typeof speak === "function") speak(text);
      else {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = TARGET_RATE;
        window.speechSynthesis.speak(utterance);
      }
    } catch (_) {}
  }

  function installRepeatPolicy() {
    const list = document.getElementById("environmentActions");
    if (!list || list.dataset.v5RepeatPolicy) return;
    list.dataset.v5RepeatPolicy = "true";
    list.addEventListener("click", event => {
      const button = event.target.closest("button");
      if (!button) return;
      setTimeout(() => applyExtendedRepeat(button), 260);
    });
  }

  function addRouteGuide() {
    if (document.getElementById("routeGuide")) return;
    const inventory = document.getElementById("inventory")?.closest("section");
    if (!inventory) return;
    const details = document.createElement("details");
    details.id = "routeGuide";
    details.className = "panel compact";
    details.innerHTML = `
      <summary>Какими способами можно пройти игру</summary>
      <p>Без полного спойлера: выход открывается не одним-единственным маршрутом.</p>
      <ul>
        <li><strong>Технический путь:</strong> инструменты, питание, карта и код.</li>
        <li><strong>Социальный путь:</strong> наладить контакт с людьми и получить помощь.</li>
        <li><strong>Силовой путь:</strong> ломать препятствия, принимая шум, травмы и другие последствия.</li>
        <li><strong>Смешанный путь:</strong> часть систем починить, часть обойти, а часть задач решить через людей.</li>
      </ul>`;
    inventory.insertAdjacentElement("afterend", details);
  }

  function boot(attempt = 0) {
    installVoicePolicy();
    addVoiceControls();
    installRepeatPolicy();
    addRouteGuide();
    if (!installed && document.getElementById("voiceStatus") && document.getElementById("environmentActions")) installed = true;
    if (!installed && attempt < 120) setTimeout(() => boot(attempt + 1), 100);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => boot());
  else boot();
})();