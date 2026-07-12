"use strict";

const ROOMS = {
  cell: {
    name: "Шлюзовая камера",
    description: "Тесная металлическая камера. Рядом гудит распределительный щит, а выход закрывает гермодверь.",
    exits: {east: "corridor"},
  },
  corridor: {
    name: "Технический коридор",
    description: "Длинный технический коридор соединяет шлюзовую камеру, насосную, мастерскую и склад предохранителей.",
    exits: {west: "cell", north: "pump", east: "workshop", south: "storage"},
  },
  pump: {
    name: "Насосная",
    description: "Под ногами вибрируют трубы. В полу решетка, из-под нее идет слабый электрический писк.",
    exits: {south: "corridor"},
  },
  workshop: {
    name: "Мастерская",
    description: "Верстак, инструменты и мертвый аварийный радиоприёмник. На стене три резонатора: низкий, средний и высокий.",
    exits: {west: "corridor"},
  },
  storage: {
    name: "Склад предохранителей",
    description: "Небольшой склад. За заклинившей створкой виден аварийный блок питания.",
    exits: {north: "corridor", east: "control"},
  },
  control: {
    name: "Пультовая",
    description: "Центральный пульт обесточен. Рядом находится выходной шлюз.",
    exits: {west: "storage", south: "exit"},
  },
  exit: {
    name: "Выходной шлюз",
    description: "Здесь установлены кодовая панель и считыватель карты. За дверью слышен дождь и открытое пространство.",
    exits: {north: "control"},
  },
};

const DIRECTION_NAMES = {north: "север", south: "юг", east: "восток", west: "запад"};
const DIRECTION_PAN = {west: -0.8, east: 0.8, north: 0.0, south: 0.0};

function makeState(overrides = {}) {
  const state = {
    room: "cell",
    inventory: [],
    flags: {
      inspected_cell: false,
      locker_open: false,
      panel_open: false,
      door_unlocked: false,
      workshop_searched: false,
      grate_open: false,
      radio_fixed: false,
      storage_pried: false,
      fuse_installed: false,
      power_on: false,
      card_taken: false,
      code_known: false,
      checkpoint: false,
    },
    turns: 0,
    mistakes: 0,
    countdown: null,
    won: false,
    message: "Ты приходишь в себя в аварийной камере сектора Контур-9. Главная сеть мертва. Нужно выбраться наружу.",
    log: [],
  };
  if (overrides.flags) Object.assign(state.flags, overrides.flags);
  for (const [key, value] of Object.entries(overrides)) {
    if (key !== "flags") state[key] = structuredClone(value);
  }
  return state;
}

function cloneState(state) {
  return JSON.parse(JSON.stringify(state));
}

function itemName(item) {
  return ({
    glove: "изолирующая перчатка",
    maintenance_key: "ключ техобслуживания",
    wrench: "разводной ключ",
    battery: "аккумулятор",
    fuse: "силовой предохранитель",
    card: "карта доступа",
  })[item] ?? item;
}

function movementBlockReason(state, direction, target) {
  if (state.room === "cell" && direction === "east" && !state.flags.door_unlocked) return "Гермодверь заперта.";
  if (state.room === "storage" && direction === "east" && !state.flags.storage_pried) return "Проход в пультовую перекрыт заклинившей створкой.";
  if (state.room === "control" && direction === "south" && !state.flags.power_on) return "Выходной шлюз обесточен.";
  return null;
}

function objective(state) {
  const f = state.flags;
  if (state.won) return "Побег завершен.";
  if (!f.door_unlocked) return "Найти способ открыть гермодверь камеры.";
  if (!state.inventory.includes("wrench")) return "Обыскать мастерскую.";
  if (!state.inventory.includes("battery") && !f.radio_fixed) return "Достать аккумулятор из решетки насосной.";
  if (!f.radio_fixed) return "Запитать аварийный радиоприёмник.";
  if (!state.inventory.includes("fuse") && !f.fuse_installed) return "Добраться до силового предохранителя на складе.";
  if (!f.fuse_installed) return "Установить предохранитель в центральный пульт.";
  if (!f.power_on) return "Запустить аварийное питание.";
  if (!f.card_taken) return "Забрать карту доступа из открывшегося отсека пульта.";
  return "Добраться до выходного шлюза и ввести услышанный код.";
}

function availableActions(state) {
  if (state.won) return [{id: "new_game", label: "Начать новую игру", key: "N"}];
  const f = state.flags;
  const inv = state.inventory;
  const actions = [
    {id: "inspect", label: "Осмотреть помещение", key: "I"},
    {id: "listen", label: "Прислушаться", key: "L"},
  ];
  if (f.code_known) actions.push({id: "repeat_code", label: "Повторить известный код", key: "C"});
  if (state.room === "cell") {
    if (!f.locker_open) actions.push({id: "open_locker", label: "Открыть аварийный шкафчик", key: "1"});
    if (f.locker_open && !inv.includes("glove") && !f.panel_open) actions.push({id: "take_glove", label: "Взять изолирующую перчатку", key: "2"});
    if (!f.panel_open) actions.push({id: "open_panel", label: "Открыть распределительный щит", key: "3"});
    if (inv.includes("maintenance_key") && !f.door_unlocked) actions.push({id: "unlock_cell", label: "Открыть гермодверь ключом", key: "4"});
  } else if (state.room === "workshop") {
    if (!f.workshop_searched) actions.push({id: "search_workshop", label: "Обыскать верстак", key: "1"});
    if (inv.includes("battery") && !f.radio_fixed) actions.push({id: "repair_radio", label: "Подключить аккумулятор к радиоприёмнику", key: "2"});
    actions.push({id: "play_tones", label: "Прослушать три резонатора", key: "3"});
  } else if (state.room === "pump") {
    if (inv.includes("wrench") && !f.grate_open) actions.push({id: "open_grate", label: "Открутить решетку разводным ключом", key: "1"});
    if (f.grate_open && !inv.includes("battery") && !f.radio_fixed) actions.push({id: "take_battery", label: "Достать аккумулятор", key: "2"});
  } else if (state.room === "storage") {
    if (inv.includes("wrench") && !f.storage_pried) actions.push({id: "pry_storage", label: "Отжать заклинившую створку", key: "1"});
    if (f.storage_pried && !inv.includes("fuse") && !f.fuse_installed) actions.push({id: "take_fuse", label: "Взять силовой предохранитель", key: "2"});
  } else if (state.room === "control") {
    if (inv.includes("fuse") && !f.fuse_installed) actions.push({id: "install_fuse", label: "Установить предохранитель", key: "1"});
    if (f.fuse_installed && !f.power_on) actions.push({id: "power_on", label: "Запустить аварийное питание", key: "2"});
    if (f.power_on && !f.card_taken) actions.push({id: "take_card", label: "Забрать карту доступа", key: "3"});
  } else if (state.room === "exit") {
    if (f.power_on) actions.push({id: "enter_code", label: "Ввести код на панели", key: "1"});
    if (!f.power_on) actions.push({id: "check_exit", label: "Проверить мертвую панель", key: "1"});
  }
  return actions;
}

function score(state) {
  return Math.max(100, 1400 - state.turns * 18 - state.mistakes * 90);
}

function view(state) {
  const room = ROOMS[state.room];
  const exits = Object.entries(room.exits).map(([direction, target]) => {
    const locked = movementBlockReason(state, direction, target);
    return {
      direction,
      label: DIRECTION_NAMES[direction],
      target: ROOMS[target].name,
      locked: Boolean(locked),
      reason: locked || "",
    };
  });
  return {
    room: state.room,
    room_name: room.name,
    description: room.description,
    message: state.message,
    inventory: state.inventory.map(itemName),
    inventory_ids: [...state.inventory],
    turns: state.turns,
    mistakes: state.mistakes,
    countdown: state.countdown,
    won: state.won,
    exits,
    actions: availableActions(state),
    objective: objective(state),
    score: state.won ? score(state) : null,
    known_code: state.flags.code_known ? "285" : null,
    log: state.log.slice(-8),
  };
}

function addMessage(state, text) {
  state.message = text;
  state.log.push(text);
  state.log = state.log.slice(-20);
}

function resetToCheckpoint(state) {
  state.room = "control";
  state.countdown = 12;
  state.mistakes += 1;
  state.flags.card_taken = true;
  if (!state.inventory.includes("card")) state.inventory.push("card");
  addMessage(state, "Система блокирует шлюз. Аварийный контур откатывает тебя к пультовой контрольной точке. Таймер перезапущен.");
  return [{sound: "fail", pan: 0, gain: 0.9}, {sound: "alarm", pan: 0, gain: 0.7}];
}

function advance(state, amount = 1) {
  state.turns += amount;
  const events = [];
  if (state.countdown !== null && !state.won) {
    state.countdown -= amount;
    if (state.countdown <= 0) events.push(...resetToCheckpoint(state));
    else if (state.countdown <= 3) events.push({sound: "alarm", pan: 0, gain: 1.0});
  }
  return events;
}
