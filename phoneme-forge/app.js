const form = document.querySelector('#align-form');
const audioInput = document.querySelector('#audio');
const transcriptInput = document.querySelector('#transcript');
const statusNode = document.querySelector('#status');
const results = document.querySelector('#results');
const rows = document.querySelector('#rows');
const player = document.querySelector('#player');
const submit = document.querySelector('#submit');
let currentIntervals = [];
let currentFilter = 'all';
let stopTimer = null;
let objectUrl = null;

const PHONE_MAP = {
  а:['a'], б:['b'], в:['v'], г:['ɡ'], д:['d'], е:['j','e'], ё:['j','o'], ж:['ʐ'], з:['z'],
  и:['i'], й:['j'], к:['k'], л:['l'], м:['m'], н:['n'], о:['o'], п:['p'], р:['r'], с:['s'],
  т:['t'], у:['u'], ф:['f'], х:['x'], ц:['t͡s'], ч:['t͡ɕ'], ш:['ʂ'], щ:['ɕː'], ы:['ɨ'],
  э:['e'], ю:['j','u'], я:['j','a'], ь:[], ъ:[]
};

function setStatus(message) { statusNode.textContent = message; }
function wordsFrom(text) { return text.match(/[А-Яа-яЁёA-Za-z0-9-]+/g) || []; }
function phonesFrom(word) {
  const phones = [];
  for (const char of word.toLowerCase()) phones.push(...(PHONE_MAP[char] || [char]));
  return phones.length ? phones : [word.toLowerCase()];
}

function allocateIntervals(words, durationMs) {
  const weights = words.map(word => Math.max(2, phonesFrom(word).length));
  const total = weights.reduce((sum, value) => sum + value, 0);
  const intervals = [];
  let cursor = 0;
  words.forEach((word, index) => {
    const end = index === words.length - 1 ? durationMs : cursor + Math.round(durationMs * weights[index] / total);
    intervals.push({tier:'word', label:word, start_ms:cursor, end_ms:end, duration_ms:end-cursor});
    const phones = phonesFrom(word);
    let phoneCursor = cursor;
    phones.forEach((phone, phoneIndex) => {
      const phoneEnd = phoneIndex === phones.length - 1
        ? end
        : cursor + Math.round((end - cursor) * (phoneIndex + 1) / phones.length);
      intervals.push({tier:'phone', label:phone, start_ms:phoneCursor, end_ms:phoneEnd, duration_ms:phoneEnd-phoneCursor});
      phoneCursor = phoneEnd;
    });
    cursor = end;
  });
  return intervals.sort((a,b) => a.start_ms-b.start_ms || (a.tier === 'word' ? -1 : 1));
}

function readDuration(file) {
  return new Promise((resolve, reject) => {
    const probe = document.createElement('audio');
    const url = URL.createObjectURL(file);
    probe.preload = 'metadata';
    probe.onloadedmetadata = () => {
      const duration = probe.duration;
      URL.revokeObjectURL(url);
      Number.isFinite(duration) && duration > 0 ? resolve(duration) : reject(new Error('Не удалось определить длительность'));
    };
    probe.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Safari не смог открыть этот аудиоформат')); };
    probe.src = url;
  });
}

function renderRows() {
  rows.replaceChildren();
  const filtered = currentIntervals.filter(item => currentFilter === 'all' || item.tier === currentFilter);
  document.querySelector('#caption').textContent = `Границы сегментов: ${filtered.length}`;
  for (const item of filtered) {
    const row = document.createElement('tr');
    const type = item.tier === 'word' ? 'Слово' : 'Фонема';
    for (const value of [type, item.label, item.start_ms, item.end_ms, item.duration_ms]) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.append(cell);
    }
    const action = document.createElement('td');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = `Прослушать ${type.toLowerCase()} ${item.label}`;
    button.addEventListener('click', () => preview(item));
    action.append(button);
    row.append(action);
    rows.append(row);
  }
}

async function preview(item) {
  if (stopTimer) clearTimeout(stopTimer);
  player.currentTime = item.start_ms / 1000;
  try { await player.play(); } catch (_) { setStatus('Нажмите кнопку воспроизведения ещё раз: Safari заблокировал автозапуск.'); }
  stopTimer = setTimeout(() => player.pause(), Math.max(50, item.duration_ms));
}

function download(name, type, contents) {
  const blob = new Blob([contents], {type});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function asCsv() {
  const escape = value => `"${String(value).replaceAll('"','""')}"`;
  return ['tier,label,start_ms,end_ms,duration_ms', ...currentIntervals.map(i => [i.tier,i.label,i.start_ms,i.end_ms,i.duration_ms].map(escape).join(','))].join('\n');
}

function textGridTier(name, items, xmax) {
  return `        item [${name === 'words' ? 1 : 2}]:\n            class = "IntervalTier"\n            name = "${name}"\n            xmin = 0\n            xmax = ${xmax}\n            intervals: size = ${items.length}\n` + items.map((item,index) => `            intervals [${index+1}]:\n                xmin = ${(item.start_ms/1000).toFixed(6)}\n                xmax = ${(item.end_ms/1000).toFixed(6)}\n                text = "${item.label.replaceAll('"','""')}"\n`).join('');
}

function asTextGrid() {
  const xmax = Math.max(...currentIntervals.map(i => i.end_ms), 0) / 1000;
  const words = currentIntervals.filter(i => i.tier === 'word');
  const phones = currentIntervals.filter(i => i.tier === 'phone');
  return `File type = "ooTextFile"\nObject class = "TextGrid"\n\nxmin = 0\nxmax = ${xmax}\ntiers? <exists>\nsize = 2\nitem []:\n${textGridTier('words', words, xmax)}${textGridTier('phones', phones, xmax)}`;
}

for (const button of document.querySelectorAll('[data-filter]')) {
  button.addEventListener('click', () => {
    currentFilter = button.dataset.filter;
    for (const other of document.querySelectorAll('[data-filter]')) other.setAttribute('aria-pressed', String(other === button));
    renderRows();
  });
}

document.querySelector('#download-json').addEventListener('click', () => download('alignment.json','application/json',JSON.stringify({engine:'browser-demo',intervals:currentIntervals},null,2)));
document.querySelector('#download-csv').addEventListener('click', () => download('alignment.csv','text/csv;charset=utf-8',asCsv()));
document.querySelector('#download-textgrid').addEventListener('click', () => download('alignment.TextGrid','text/plain;charset=utf-8',asTextGrid()));

form.addEventListener('submit', async event => {
  event.preventDefault();
  const file = audioInput.files?.[0];
  const words = wordsFrom(transcriptInput.value.trim());
  if (!file || !words.length) return;
  submit.disabled = true;
  results.hidden = true;
  setStatus('Читаю аудио локально на устройстве.');
  try {
    const duration = await readDuration(file);
    currentIntervals = allocateIntervals(words, Math.round(duration * 1000));
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    player.src = objectUrl;
    currentFilter = 'all';
    renderRows();
    results.hidden = false;
    setStatus(`Готово. Найдено сегментов: ${currentIntervals.length}. Это приблизительная браузерная разметка.`);
    document.querySelector('#results-heading').focus();
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`);
  } finally { submit.disabled = false; }
});
