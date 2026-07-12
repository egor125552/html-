function applyAction(inputState, action, value = null) {
  if (action === "new_game") return {state: makeState(), events: [{sound: "success", pan: 0, gain: 0.5}]};
  const state = inputState;
  if (state.won) {
    addMessage(state, "Побег уже завершен. Начни новую игру.");
    return {state, events: []};
  }
  const events = [];
  const f = state.flags;
  const inv = state.inventory;

  if (action.startsWith("move_")) {
    const direction = action.split("_", 2)[1];
    const target = ROOMS[state.room].exits[direction];
    if (!target) {
      addMessage(state, "В этом направлении прохода нет.");
      state.mistakes += 1;
      return {state, events: [{sound: "fail", pan: DIRECTION_PAN[direction] ?? 0, gain: 0.5}]};
    }
    const reason = movementBlockReason(state, direction, target);
    if (reason) {
      addMessage(state, reason);
      state.mistakes += 1;
      return {state, events: [{sound: "locked", pan: DIRECTION_PAN[direction] ?? 0, gain: 0.7}]};
    }
    state.room = target;
    addMessage(state, `Ты переходишь в помещение: ${ROOMS[target].name}. ${ROOMS[target].description}`);
    events.push(
      {sound: "footstep", pan: DIRECTION_PAN[direction] ?? 0, gain: 0.65},
      {sound: "door", pan: DIRECTION_PAN[direction] ?? 0, gain: 0.45},
      ...advance(state),
    );
    return {state, events};
  }

  if (action === "inspect") {
    let text = ROOMS[state.room].description;
    if (state.room === "cell" && !f.inspected_cell) {
      f.inspected_cell = true;
      text += " В шкафчике что-то мягкое. В щите слышно опасное потрескивание, но за проводами звякает металлический предмет.";
    } else if (state.room === "workshop") text += " На верстаке лежит тяжелый инструмент. Радиоприемнику не хватает питания.";
    else if (state.room === "pump") text += " Решетка держится на двух ржавых гайках. Под ней лежит небольшой аккумулятор.";
    else if (state.room === "storage") text += " Створку можно отжать прочным инструментом.";
    else if (state.room === "control") text += " В пульте пустое гнездо силового предохранителя.";
    else if (state.room === "exit") text += ` Панель принимает трёхзначный код. ${f.code_known ? "Известный код выхода: 2, 8, 5." : "Код передаст аварийный радиоприёмник после ремонта."}`;
    addMessage(state, text);
    events.push(...advance(state));
  } else if (action === "listen") {
    const listenText = {
      cell: "За дверью тянется длинный коридор. Справа от щита искрит проводка.",
      corridor: "Из насосной идет ровная вибрация. В мастерской звенят инструменты. На складе скрипит заклинившая створка.",
      pump: "Под решеткой слышен короткий электронный писк аккумулятора.",
      workshop: "Резонаторы дают три тона: низкий, средний и высокий. Радио молчит.",
      storage: "За заклинившей створкой гудят силовые шины пультовой.",
      control: "При запуске питание пойдет к выходному шлюзу.",
      exit: "Снаружи дождь. Электрозамок ждет код и карту.",
    }[state.room];
    addMessage(state, listenText);
    events.push({sound: "scan", pan: 0, gain: 0.55}, ...advance(state));
  } else if (action === "repeat_code" && f.code_known) {
    addMessage(state, "Известный код выхода: 2, 8, 5. Низкий тон дал 2, высокий — 8, средний — 5.");
  } else if (action === "open_locker" && state.room === "cell" && !f.locker_open) {
    f.locker_open = true;
    addMessage(state, "Шкафчик открывается. Внутри лежит толстая изолирующая перчатка.");
    events.push({sound: "door", pan: -0.7, gain: 0.55}, ...advance(state));
  } else if (action === "take_glove" && state.room === "cell" && f.locker_open && !inv.includes("glove")) {
    inv.push("glove");
    addMessage(state, "Ты берешь изолирующую перчатку.");
    events.push({sound: "pickup", pan: -0.5, gain: 0.7}, ...advance(state));
  } else if (action === "open_panel" && state.room === "cell" && !f.panel_open) {
    if (!inv.includes("glove")) {
      state.mistakes += 1;
      addMessage(state, "Ты касаешься щита голой рукой. Разряд отбрасывает тебя назад. Нужна изоляция.");
      events.push({sound: "shock", pan: -0.5, gain: 0.9}, ...advance(state));
    } else {
      f.panel_open = true;
      if (!inv.includes("maintenance_key")) inv.push("maintenance_key");
      addMessage(state, "Перчатка держит разряд. За пучком проводов находится ключ техобслуживания. Ты забираешь его.");
      events.push({sound: "electric", pan: -0.6, gain: 0.7}, {sound: "pickup", pan: -0.4, gain: 0.7}, ...advance(state));
    }
  } else if (action === "unlock_cell" && state.room === "cell" && inv.includes("maintenance_key") && !f.door_unlocked) {
    f.door_unlocked = true;
    addMessage(state, "Ключ поворачивается. Замки гермодвери отходят один за другим. Путь в технический коридор открыт.");
    events.push({sound: "lock", pan: 0.8, gain: 0.75}, {sound: "door", pan: 0.8, gain: 0.6}, ...advance(state));
  } else if (action === "search_workshop" && state.room === "workshop" && !f.workshop_searched) {
    f.workshop_searched = true;
    if (!inv.includes("wrench")) inv.push("wrench");
    addMessage(state, "Под ветошью находится исправный разводной ключ. Радиоприемник цел, но его аккумуляторный отсек пуст.");
    events.push({sound: "metal", pan: 0.5, gain: 0.6}, {sound: "pickup", pan: 0.5, gain: 0.7}, ...advance(state));
  } else if (action === "play_tones" && state.room === "workshop") {
    addMessage(state, "Ты запускаешь резонаторы. Это словарь для кода: низкий тон означает цифру 2, средний — цифру 5, высокий — цифру 8. Это еще не сам код; порядок позже передаст радио.");
    events.push(
      {sound: "tone_low", pan: -0.6, gain: 0.8, delay: 0.0},
      {sound: "tone_mid", pan: 0.0, gain: 0.8, delay: 0.55},
      {sound: "tone_high", pan: 0.6, gain: 0.8, delay: 1.1},
      ...advance(state),
    );
  } else if (action === "open_grate" && state.room === "pump" && inv.includes("wrench") && !f.grate_open) {
    f.grate_open = true;
    addMessage(state, "Гайки срываются с хрустом. Решетка открыта, аккумулятор можно достать.");
    events.push({sound: "metal", pan: 0, gain: 0.8}, ...advance(state));
  } else if (action === "take_battery" && state.room === "pump" && f.grate_open && !inv.includes("battery") && !f.radio_fixed) {
    inv.push("battery");
    addMessage(state, "Ты достаешь тяжелый аккумулятор. Заряда еще достаточно.");
    events.push({sound: "pickup", pan: 0, gain: 0.75}, ...advance(state));
  } else if (action === "repair_radio" && state.room === "workshop" && inv.includes("battery") && !f.radio_fixed) {
    inv.splice(inv.indexOf("battery"), 1);
    f.radio_fixed = true;
    f.code_known = true;
    addMessage(state, "Радио оживает и передает порядок: низкий тон, высокий тон, средний тон. Подставляем цифры из резонаторов: 2, 8, 5. Код выхода — 285. Игра запомнила его; действие «Повторить известный код» теперь доступно в любом помещении.");
    events.push(
      {sound: "switch", pan: 0, gain: 0.7},
      {sound: "tone_low", pan: -0.5, gain: 0.9, delay: 0.35},
      {sound: "tone_high", pan: 0.5, gain: 0.9, delay: 1.05},
      {sound: "tone_mid", pan: 0, gain: 0.9, delay: 1.75},
      ...advance(state),
    );
  } else if (action === "pry_storage" && state.room === "storage" && inv.includes("wrench") && !f.storage_pried) {
    f.storage_pried = true;
    addMessage(state, "Ты заводишь ключ в щель и отжимаешь створку. Открывается проход в пультовую.");
    events.push({sound: "metal", pan: 0.6, gain: 0.85}, {sound: "door", pan: 0.7, gain: 0.65}, ...advance(state));
  } else if (action === "take_fuse" && state.room === "storage" && f.storage_pried && !inv.includes("fuse") && !f.fuse_installed) {
    inv.push("fuse");
    addMessage(state, "Ты берешь массивный силовой предохранитель.");
    events.push({sound: "pickup", pan: -0.3, gain: 0.75}, ...advance(state));
  } else if (action === "install_fuse" && state.room === "control" && inv.includes("fuse") && !f.fuse_installed) {
    inv.splice(inv.indexOf("fuse"), 1);
    f.fuse_installed = true;
    addMessage(state, "Предохранитель входит в гнездо. Пульт готов к запуску.");
    events.push({sound: "lock", pan: 0, gain: 0.65}, ...advance(state));
  } else if (action === "power_on" && state.room === "control" && f.fuse_installed && !f.power_on) {
    f.power_on = true;
    f.checkpoint = true;
    state.countdown = 12;
    addMessage(state, "Аварийное питание включено. Вместе с ним просыпается защита: до полной блокировки 12 ходов. В пульте открылся отсек с картой.");
    events.push({sound: "switch", pan: 0, gain: 0.9}, {sound: "alarm", pan: 0, gain: 0.75}, ...advance(state, 0));
  } else if (action === "take_card" && state.room === "control" && f.power_on && !f.card_taken) {
    f.card_taken = true;
    if (!inv.includes("card")) inv.push("card");
    addMessage(state, "Ты забираешь карту доступа. Теперь переходи в выходной шлюз.");
    events.push({sound: "pickup", pan: 0.3, gain: 0.8}, ...advance(state));
  } else if (action === "check_exit" && state.room === "exit" && !f.power_on) {
    addMessage(state, "Панель полностью мертва. Сначала нужно запитать центральный пульт.");
    state.mistakes += 1;
    events.push({sound: "fail", pan: 0, gain: 0.6});
  } else if (action === "enter_code" && state.room === "exit" && f.power_on) {
    const code = String(value || "").replaceAll("-", "").replaceAll(" ", "");
    if (!inv.includes("card")) {
      addMessage(state, "Кодовая панель отвечает, но считыватель требует карту доступа.");
      state.mistakes += 1;
      events.push({sound: "locked", pan: 0, gain: 0.7}, ...advance(state));
    } else if (code !== "285") {
      addMessage(state, "Неверный код. Панель отнимает два деления таймера.");
      state.mistakes += 1;
      events.push({sound: "fail", pan: 0, gain: 0.8}, ...advance(state, 2));
    } else {
      state.won = true;
      state.countdown = null;
      addMessage(state, "Код принят. Карта считывается. Шлюз раскрывается, и холодный дождь ударяет в лицо. Ты выбрался из Контура-9.");
      events.push(
        {sound: "success", pan: 0, gain: 1.0},
        {sound: "door", pan: 0, gain: 0.9, delay: 0.5},
        {sound: "rain", pan: 0, gain: 0.65, delay: 1.0},
      );
    }
  } else {
    addMessage(state, "Это действие сейчас недоступно.");
    state.mistakes += 1;
    events.push({sound: "fail", pan: 0, gain: 0.5});
  }
  return {state, events};
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {ROOMS, DIRECTION_NAMES, DIRECTION_PAN, makeState, cloneState, itemName, movementBlockReason, objective, availableActions, score, view, applyAction};
}
