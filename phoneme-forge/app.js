const form = document.querySelector('#align-form');
const audioInput = document.querySelector('#audio');
const transcriptInput = document.querySelector('#transcript');
const statusNode = document.querySelector('#status');
const results = document.querySelector('#results');
const rows = document.querySelector('#rows');
const player = document.querySelector('#player');
const submit = document.querySelector('#submit');
const engineNode = document.querySelector('#engine');
const warningNode = document.querySelector('#warning');

const MAUS_ENDPOINT = 'https://clarin.phonetik.uni-muenchen.de/BASWebServices/services/runMAUSBasic';
const LOAD_ENDPOINT = 'https://clarin.phonetik.uni-muenchen.de/BASWebServices/services/getLoadIndicator';

let currentIntervals = [];
let currentFilter = 'all';
let stopTimer = null;
let objectUrl = null;
let originalAudioFile = null;
let lastTextGrid = '';

function setStatus(message) {
  statusNode.textContent = message;
}

function xmlText(xml, name) {
  return xml.querySelector(name)?.textContent?.trim() || '';
}

function escapeCsv(value) {
  return `"${String(value).replaceAll('"', '""')}"`;
}

async function checkServerLoad() {
  try {
    const response = await fetch(LOAD_ENDPOINT, { cache: 'no-store' });
    if (!response.ok) return;
    const level = (await response.text()).trim();
    if (level === '2') {
      throw new Error('Сервер WebMAUS сейчас перегружен. Попробуйте ещё раз немного позже.');
    }
    if (level === '1') setStatus('Сервер WebMAUS загружен умеренно. Обработка может идти дольше обычного.');
  } catch (error) {
    if (error.message.includes('перегружен')) throw error;
  }
}

async function decodeAudio(file) {
  const arrayBuffer = await file.arrayBuffer();
  const AudioContextClass = window.AudioContext || window.webkitAudioContext;
  if (!AudioContextClass) throw new Error('Safari не поддерживает Web Audio API.');
  const context = new AudioContextClass();
  try {
    return await context.decodeAudioData(arrayBuffer.slice(0));
  } catch {
    throw new Error('Safari не смог декодировать этот аудиофайл. Попробуйте MP3, M4A или WAV.');
  } finally {
    await context.close().catch(() => {});
  }
}

function mixToMono(audioBuffer) {
  const mono = new Float32Array(audioBuffer.length);
  for (let channel = 0; channel < audioBuffer.numberOfChannels; channel += 1) {
    const source = audioBuffer.getChannelData(channel);
    for (let index = 0; index < source.length; index += 1) mono[index] += source[index];
  }
  const divisor = Math.max(1, audioBuffer.numberOfChannels);
  for (let index = 0; index < mono.length; index += 1) mono[index] /= divisor;
  return mono;
}

function resampleLinear(input, sourceRate, targetRate = 16000) {
  if (sourceRate === targetRate) return input;
  const ratio = sourceRate / targetRate;
  const outputLength = Math.max(1, Math.round(input.length / ratio));
  const output = new Float32Array(outputLength);
  for (let index = 0; index < outputLength; index += 1) {
    const position = index * ratio;
    const left = Math.floor(position);
    const right = Math.min(left + 1, input.length - 1);
    const fraction = position - left;
    output[index] = input[left] * (1 - fraction) + input[right] * fraction;
  }
  return output;
}

function writeAscii(view, offset, text) {
  for (let index = 0; index < text.length; index += 1) view.setUint8(offset + index, text.charCodeAt(index));
}

function pcm16WavBlob(samples, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  writeAscii(view, 0, 'RIFF');
  view.setUint32(4, 36 + samples.length * 2, true);
  writeAscii(view, 8, 'WAVE');
  writeAscii(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeAscii(view, 36, 'data');
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (const rawSample of samples) {
    const sample = Math.max(-1, Math.min(1, rawSample));
    view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
    offset += 2;
  }
  return new Blob([buffer], { type: 'audio/wav' });
}

async function normalizeForMaus(file) {
  setStatus('Декодирую аудио на iPhone.');
  const audioBuffer = await decodeAudio(file);
  if (audioBuffer.duration > 900) throw new Error('Для первой версии максимум 15 минут аудио за один запуск.');
  setStatus('Перевожу в mono WAV 16 кГц.');
  const mono = mixToMono(audioBuffer);
  const samples = resampleLinear(mono, audioBuffer.sampleRate, 16000);
  return pcm16WavBlob(samples, 16000);
}

async function runMaus(wavBlob, transcript) {
  await checkServerLoad();
  const formData = new FormData();
  formData.append('SIGNAL', new File([wavBlob], 'speech.wav', { type: 'audio/wav' }));
  formData.append('LANGUAGE', 'rus-RU');
  formData.append('OUTFORMAT', 'TextGrid');
  formData.append('TEXT', new File([transcript], 'transcript.txt', { type: 'text/plain;charset=utf-8' }));

  setStatus('WebMAUS строит реальные границы слов и фонем. Не закрывайте вкладку.');
  let response;
  try {
    response = await fetch(MAUS_ENDPOINT, { method: 'POST', body: formData });
  } catch (error) {
    throw new Error(`Safari не смог связаться с WebMAUS: ${error.message}. Возможна блокировка CORS или временный сбой сервиса.`);
  }
  if (!response.ok) throw new Error(`WebMAUS вернул HTTP ${response.status}.`);

  const xmlString = await response.text();
  const xml = new DOMParser().parseFromString(xmlString, 'application/xml');
  if (xml.querySelector('parsererror')) throw new Error('WebMAUS вернул повреждённый XML-ответ.');

  const success = xmlText(xml, 'success').toLowerCase();
  const warning = xmlText(xml, 'warning');
  const output = xmlText(xml, 'output');
  const downloadLink = xmlText(xml, 'downloadLink');
  if (!['true', '1', 'yes'].includes(success) || !downloadLink) {
    throw new Error(output || warning || 'WebMAUS не смог разметить эту запись. Проверьте точность расшифровки.');
  }

  const gridResponse = await fetch(downloadLink, { cache: 'no-store' });
  if (!gridResponse.ok) throw new Error(`Не удалось скачать TextGrid: HTTP ${gridResponse.status}.`);
  return { textGrid: await gridResponse.text(), warning, downloadLink };
}

function parseTextGrid(text) {
  const tiers = [];
  const itemPattern = /item\s*\[\d+\]\s*:\s*class\s*=\s*"IntervalTier"\s*name\s*=\s*"([^"]*)"[\s\S]*?(?=\n\s*item\s*\[\d+\]\s*:|$)/g;
  let tierMatch;
  while ((tierMatch = itemPattern.exec(text)) !== null) {
    const [, name] = tierMatch;
    const block = tierMatch[0];
    const intervals = [];
    const intervalPattern = /intervals\s*\[\d+\]\s*:\s*xmin\s*=\s*([\d.eE+-]+)\s*xmax\s*=\s*([\d.eE+-]+)\s*text\s*=\s*"((?:[^"]|"")*)"/g;
    let match;
    while ((match = intervalPattern.exec(block)) !== null) {
      intervals.push({
        start_ms: Math.round(Number(match[1]) * 1000),
        end_ms: Math.round(Number(match[2]) * 1000),
        label: match[3].replaceAll('""', '"').trim(),
      });
    }
    tiers.push({ name, intervals });
  }

  if (!tiers.length) throw new Error('В TextGrid не найдено слоёв IntervalTier.');
  const phoneTier = tiers.find(tier => /MAU|phone|phon/i.test(tier.name)) || tiers.at(-1);
  const wordTier = tiers.find(tier => /ORT|word|orth/i.test(tier.name)) || tiers[0];
  const intervals = [];

  for (const item of wordTier.intervals) {
    if (!item.label || item.label === '<p:>') continue;
    intervals.push({ ...item, duration_ms: item.end_ms - item.start_ms, tier: 'word' });
  }
  for (const item of phoneTier.intervals) {
    if (!item.label) continue;
    const label = item.label === '<p:>' ? 'пауза' : item.label;
    intervals.push({ ...item, label, duration_ms: item.end_ms - item.start_ms, tier: 'phone' });
  }
  if (!intervals.some(item => item.tier === 'phone')) throw new Error('WebMAUS не вернул фонемный слой.');
  return intervals.sort((a, b) => a.start_ms - b.start_ms || (a.tier === 'word' ? -1 : 1));
}

function renderRows() {
  rows.replaceChildren();
  const filtered = currentIntervals.filter(item => currentFilter === 'all' || item.tier === currentFilter);
  document.querySelector('#caption').textContent = `Реальные границы WebMAUS: ${filtered.length} сегментов`;
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
  try {
    await player.play();
  } catch {
    setStatus('Safari заблокировал автозапуск. Нажмите «Прослушать» ещё раз.');
    return;
  }
  stopTimer = setTimeout(() => player.pause(), Math.max(40, item.duration_ms));
}

function download(name, type, contents) {
  const blob = new Blob([contents], { type });
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
  return [
    'tier,label,start_ms,end_ms,duration_ms',
    ...currentIntervals.map(item => [item.tier, item.label, item.start_ms, item.end_ms, item.duration_ms].map(escapeCsv).join(',')),
  ].join('\n');
}

for (const button of document.querySelectorAll('[data-filter]')) {
  button.addEventListener('click', () => {
    currentFilter = button.dataset.filter;
    for (const other of document.querySelectorAll('[data-filter]')) {
      other.setAttribute('aria-pressed', String(other === button));
    }
    renderRows();
  });
}

document.querySelector('#download-json').addEventListener('click', () => {
  download('webmaus-alignment.json', 'application/json', JSON.stringify({ engine: 'BAS WebMAUS rus-RU', intervals: currentIntervals }, null, 2));
});
document.querySelector('#download-csv').addEventListener('click', () => download('webmaus-alignment.csv', 'text/csv;charset=utf-8', asCsv()));
document.querySelector('#download-textgrid').addEventListener('click', () => download('webmaus-alignment.TextGrid', 'text/plain;charset=utf-8', lastTextGrid));

form.addEventListener('submit', async event => {
  event.preventDefault();
  const file = audioInput.files?.[0];
  const transcript = transcriptInput.value.trim();
  if (!file || !transcript) return;

  submit.disabled = true;
  results.hidden = true;
  warningNode.hidden = true;
  try {
    const wavBlob = await normalizeForMaus(file);
    const result = await runMaus(wavBlob, transcript);
    lastTextGrid = result.textGrid;
    currentIntervals = parseTextGrid(lastTextGrid);
    originalAudioFile = file;
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(originalAudioFile);
    player.src = objectUrl;
    currentFilter = 'all';
    renderRows();
    engineNode.textContent = 'Движок: BAS WebMAUS, русская акустическая модель rus-RU. Фонемы: SAMPA.';
    if (result.warning) {
      warningNode.textContent = `Предупреждение WebMAUS: ${result.warning}`;
      warningNode.hidden = false;
    }
    results.hidden = false;
    const phoneCount = currentIntervals.filter(item => item.tier === 'phone').length;
    setStatus(`Готово. WebMAUS нашёл ${phoneCount} фонем с реальными таймкодами.`);
    document.querySelector('#results-heading').focus();
  } catch (error) {
    setStatus(`Ошибка: ${error.message}`);
  } finally {
    submit.disabled = false;
  }
});
