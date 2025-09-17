document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const textInput = document.getElementById('text-input');
    const speakButton = document.getElementById('speak-button');
    const audioPlayback = document.getElementById('audio-playback');
    const loadingSpinner = document.getElementById('loading-spinner');

    // Voice Selection Elements
    const combobox = document.getElementById('voice-combobox');
    const selectedVoiceDisplay = document.getElementById('selected-voice');
    const selectedVoiceNameSpan = document.getElementById('selected-voice-name');
    const voiceList = document.getElementById('voice-list');

    // Info Section Elements
    const networkTestButton = document.getElementById('network-test-button');
    const networkSpeedSpan = document.getElementById('network-speed');
    const estimatedTimeSpan = document.getElementById('estimated-time');

    // --- State and Constants ---
    const API_KEY = 'AIzaSyAe97uFKZFmSaRpr6Kg72M7m789XqRMzaA';
    const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-tts:generateContent?key=${API_KEY}`;

    let currentVoice = 'Zephyr';
    let focusedVoiceIndex = 0;
    let isListOpen = false;

    const voices = [
        { name: 'Zephyr', ru: 'Зефир', desc: 'Яркий и светлый, для энергичных сообщений.' },
        { name: 'Puck', ru: 'Пак', desc: 'Оптимистичный и веселый, для позитивных новостей.' },
        { name: 'Charon', ru: 'Харон', desc: 'Информативный и ясный, для новостей и инструкций.' },
        { name: 'Kore', ru: 'Кора', desc: 'Твердый и уверенный, для официальных заявлений.' },
        { name: 'Fenrir', ru: 'Фенрир', desc: 'Возбужденный и динамичный, для рекламы и анонсов.' },
        { name: 'Leda', ru: 'Леда', desc: 'Молодежный и свежий, для блогов и соцсетей.' },
        { name: 'Orus', ru: 'Орус', desc: 'Строгий и авторитетный, для лекций и документации.' },
        { name: 'Aoede', ru: 'Аэда', desc: 'Беззаботный и легкий, для развлекательного контента.' },
        { name: 'Callirrhoe', ru: 'Каллироя', desc: 'Непринужденный и спокойный, для медитаций и поэзии.' },
        { name: 'Autonoe', ru: 'Автоноя', desc: 'Яркий и живой, для рассказывания историй.' },
        { name: 'Enceladus', ru: 'Энцелад', desc: 'С придыханием, тихий, для интимных и личных сообщений.' },
        { name: 'Iapetus', ru: 'Япет', desc: 'Чистый и отчетливый, для образовательных материалов.' },
        { name: 'Umbriel', ru: 'Умбриэль', desc: 'Простой и дружелюбный, для повседневного общения.' },
        { name: 'Algieba', ru: 'Альгиеба', desc: 'Гладкий и плавный, для аудиокниг.' },
        { name: 'Despina', ru: 'Деспина', desc: 'Мягкий и убедительный, для презентаций.' },
        { name: 'Erinome', ru: 'Эринома', desc: 'Ясный и точный, для технических инструкций.' },
        { name: 'Algenib', ru: 'Альгениб', desc: 'С хрипотцой, зрелый, для персонажей в историях.' },
        { name: 'Rasalgethi', ru: 'Рас-Альгети', desc: 'Информативный и зрелый, для новостных сводок.' },
        { name: 'Laomedeia', ru: 'Лаомедея', desc: 'Оптимистичный и энергичный, для мотивационных речей.' },
        { name: 'Achernar', ru: 'Ахернар', desc: 'Мягкий и нежный, для колыбельных или успокаивающего контента.' },
        { name: 'Alnilam', ru: 'Альнилам', desc: 'Твердый и решительный, для важных объявлений.' },
        { name: 'Schedar', ru: 'Шедар', desc: 'Ровный и последовательный, для длинных текстов.' },
        { name: 'Gacrux', ru: 'Гакрукс', desc: 'Зрелый и глубокий, для повествования.' },
        { name: 'Pulcherrima', ru: 'Пульхеррима', desc: 'Прямой и напористый, для деловых сообщений.' },
        { name: 'Achird', ru: 'Ахирд', desc: 'Дружелюбный и теплый, для приветствий и поддержки.' },
        { name: 'Zubenelgenubi', ru: 'Зубен эль Генуби', desc: 'Повседневный и расслабленный, для подкастов.' },
        { name: 'Vindemiatrix', ru: 'Виндемиатрикс', desc: 'Мягкий и деликатный, для чувствительных тем.' },
        { name: 'Sadachbia', ru: 'Садахбия', desc: 'Живой и анимированный, для детских историй.' },
        { name: 'Sadaltager', ru: 'Садальтагер', desc: 'Осведомленный и авторитетный, для экспертных мнений.' },
        { name: 'Sulafat', ru: 'Сулафат', desc: 'Теплый и гостеприимный, для озвучки персонажей.' }
    ];

    // --- Functions ---

    function populateVoiceList() {
        voiceList.innerHTML = '';
        voices.forEach((voice, index) => {
            const li = document.createElement('li');
            li.id = `voice-option-${index}`;
            li.setAttribute('role', 'option');
            li.setAttribute('data-voice-name', voice.name);
            li.tabIndex = -1; // Make it focusable via JS

            li.innerHTML = `
                <div class="voice-info">
                    <span class="voice-name">${voice.ru} (${voice.name})</span>
                    <span class="voice-description">${voice.desc}</span>
                </div>
                <button class="button-secondary sample-button" data-voice-name="${voice.name}" aria-label="Прослушать пример голоса ${voice.ru}">▶</button>
            `;
            voiceList.appendChild(li);
        });
    }

    function toggleDropdown(show) {
        isListOpen = show;
        voiceList.classList.toggle('open', show);
        selectedVoiceDisplay.setAttribute('aria-expanded', show);
        if (show) {
            focusedVoiceIndex = voices.findIndex(v => v.name === currentVoice);
            voiceList.children[focusedVoiceIndex]?.focus();
        }
    }

    function selectVoice(voiceName) {
        currentVoice = voiceName;
        const voice = voices.find(v => v.name === voiceName);
        selectedVoiceNameSpan.textContent = `${voice.ru} (${voice.name})`;
        toggleDropdown(false);
        selectedVoiceDisplay.focus();
    }

    function handleComboboxKeyDown(e) {
        if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            if (!isListOpen) {
                toggleDropdown(true);
            }
        }
    }

    function handleListKeyDown(e) {
        e.preventDefault();
        const items = voiceList.children;
        let nextIndex = focusedVoiceIndex;

        if (e.key === 'ArrowDown') {
            nextIndex = (focusedVoiceIndex + 1) % items.length;
        } else if (e.key === 'ArrowUp') {
            nextIndex = (focusedVoiceIndex - 1 + items.length) % items.length;
        } else if (e.key === 'Home') {
            nextIndex = 0;
        } else if (e.key === 'End') {
            nextIndex = items.length - 1;
        } else if (e.key === 'Enter') {
            selectVoice(items[focusedVoiceIndex].dataset.voiceName);
            return;
        } else if (e.key === ' ') {
            const voiceName = items[focusedVoiceIndex].dataset.voiceName;
            playSample(voiceName);
            return;
        } else if (e.key === 'Escape') {
            toggleDropdown(false);
            selectedVoiceDisplay.focus();
            return;
        }

        items[focusedVoiceIndex].classList.remove('focused');
        focusedVoiceIndex = nextIndex;
        items[focusedVoiceIndex].classList.add('focused');
        items[focusedVoiceIndex].focus();
    }

    async function playSample(voiceName) {
        const sampleText = `This is a sample of the ${voiceName} voice.`;
        // Use a more descriptive prompt for better results
        const prompt = `(Speaking in a clear and neutral tone) ${sampleText}`;
        await generateAndPlayAudio(prompt, voiceName, true);
    }

    async function handleSpeak() {
        const text = textInput.value.trim();
        if (!text) {
            alert('Пожалуйста, введите текст для озвучки.');
            return;
        }
        await generateAndPlayAudio(text, currentVoice, false);
    }

    async function generateAndPlayAudio(text, voiceName, isSample) {
        showLoading(true, isSample);
        audioPlayback.style.display = 'none';

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: "gemini-2.5-pro-preview-tts",
                    contents: [{ parts: [{ text: text }] }],
                    generationConfig: {
                        responseModalities: ["AUDIO"],
                        speechConfig: {
                            voiceConfig: { prebuiltVoiceConfig: { voiceName: voiceName } }
                        }
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Ошибка API: ${errorData.error.message || 'Неизвестная ошибка'}`);
            }

            const data = await response.json();
            const audioBase64 = data.candidates[0].content.parts[0].inlineData.data;
            const audioData = base64ToUint8Array(audioBase64);
            const wavDataUri = createWavDataUri(audioData);

            audioPlayback.src = wavDataUri;
            audioPlayback.style.display = 'block';
            audioPlayback.play();

        } catch (error) {
            console.error('Ошибка при генерации речи:', error);
            alert(`Произошла ошибка: ${error.message}`);
        } finally {
            showLoading(false, isSample);
        }
    }

    function showLoading(show, isSample) {
        loadingSpinner.style.display = show ? 'block' : 'none';
        if (isSample) {
            // Optionally disable sample buttons while one is playing
        } else {
            speakButton.disabled = show;
            speakButton.textContent = show ? 'Генерация...' : 'Озвучить основной текст';
        }
    }

    // --- Other Functions (Network, Estimation, WAV creation) ---
    // (These are mostly unchanged but included for completeness)
    async function testNetworkSpeed() {
        networkSpeedSpan.textContent = 'тестирование...';
        const testFileUrl = 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Snake_River_%285mb%29.jpg';
        try {
            const startTime = performance.now();
            const response = await fetch(testFileUrl, { cache: 'no-store' });
            const blob = await response.blob();
            const endTime = performance.now();
            const durationInSeconds = (endTime - startTime) / 1000;
            const speedMbps = ((blob.size * 8) / durationInSeconds / 1000 / 1000).toFixed(2);
            networkSpeedSpan.textContent = `${speedMbps} Мбит/с`;
        } catch (error) {
            networkSpeedSpan.textContent = 'ошибка теста';
            console.error('Ошибка при тесте скорости:', error);
        }
    }

    function updateEstimation() {
        const textLength = textInput.value.length;
        const estimatedSeconds = Math.round((textLength / 15) + 2);
        estimatedTimeSpan.textContent = `${estimatedSeconds} секунд`;
    }

    function base64ToUint8Array(base64) {
        const binaryString = atob(base64);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        return bytes;
    }

    function createWavDataUri(pcmData) {
        const sampleRate = 24000;
        const numChannels = 1;
        const bytesPerSample = 2;
        const headerLength = 44;
        const dataLength = pcmData.length;
        const buffer = new ArrayBuffer(headerLength + dataLength);
        const view = new DataView(buffer);
        view.setUint32(0, 0x52494646, false); // "RIFF"
        view.setUint32(4, 36 + dataLength, true);
        view.setUint32(8, 0x57415645, false); // "WAVE"
        view.setUint32(12, 0x666d7420, false); // "fmt "
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true); // PCM
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numChannels * bytesPerSample, true);
        view.setUint16(32, numChannels * bytesPerSample, true);
        view.setUint16(34, bytesPerSample * 8, true);
        view.setUint32(36, 0x64617461, false); // "data"
        view.setUint32(40, dataLength, true);
        new Uint8Array(buffer, headerLength).set(pcmData);
        const blob = new Blob([view], { type: 'audio/wav' });
        return URL.createObjectURL(blob);
    }

    // --- Event Listeners ---
    speakButton.addEventListener('click', handleSpeak);
    networkTestButton.addEventListener('click', testNetworkSpeed);
    textInput.addEventListener('input', updateEstimation);

    selectedVoiceDisplay.addEventListener('click', () => toggleDropdown(!isListOpen));
    selectedVoiceDisplay.addEventListener('keydown', handleComboboxKeyDown);
    voiceList.addEventListener('keydown', handleListKeyDown);

    voiceList.addEventListener('click', (e) => {
        const target = e.target;
        const voiceItem = target.closest('li');
        if (!voiceItem) return;

        const voiceName = voiceItem.dataset.voiceName;

        if (target.classList.contains('sample-button')) {
            playSample(voiceName);
        } else {
            selectVoice(voiceName);
        }
    });

    document.addEventListener('click', (e) => {
        if (!combobox.contains(e.target)) {
            toggleDropdown(false);
        }
    });

    // --- Initialization ---
    populateVoiceList();
    updateEstimation();
    selectVoice(currentVoice); // Set initial voice display
});
