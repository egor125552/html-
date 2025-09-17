document.addEventListener('DOMContentLoaded', () => {
    const textInput = document.getElementById('text-input');
    const speakButton = document.getElementById('speak-button');
    const networkTestButton = document.getElementById('network-test-button');
    const audioPlayback = document.getElementById('audio-playback');
    const networkSpeedSpan = document.getElementById('network-speed');
    const estimatedTimeSpan = document.getElementById('estimated-time');
    const loadingSpinner = document.getElementById('loading-spinner');

    // ВНИМАНИЕ: API-ключ хранится в клиентском коде.
    // Это небезопасно для публичных веб-приложений.
    // Для этого локального приложения, которое запускается только на вашем компьютере, это приемлемо.
    const API_KEY = 'AIzaSyAe97uFKZFmSaRpr6Kg72M7m789XqRMzaA';
    const API_URL = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-tts:generateContent?key=${API_KEY}`;

    speakButton.addEventListener('click', handleSpeak);
    networkTestButton.addEventListener('click', testNetworkSpeed);
    textInput.addEventListener('input', updateEstimation);

    function showLoading(show) {
        loadingSpinner.style.display = show ? 'block' : 'none';
        speakButton.disabled = show;
        speakButton.textContent = show ? 'Генерация...' : 'Озвучить';
    }

    async function handleSpeak() {
        const text = textInput.value.trim();
        if (!text) {
            alert('Пожалуйста, введите текст для озвучки.');
            return;
        }

        showLoading(true);
        audioPlayback.style.display = 'none';

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: "gemini-2.5-pro-preview-tts",
                    contents: [{
                        parts: [{ text: text }]
                    }],
                    generationConfig: {
                        responseModalities: ["AUDIO"],
                        speechConfig: {
                            voiceConfig: {
                                // Для Gemini TTS API можно использовать разные голоса, 'Kore' - один из стандартных.
                                // Также можно управлять речью с помощью промптов, например: "Say cheerfully: Hello world"
                                prebuiltVoiceConfig: {
                                    voiceName: "Kore"
                                }
                            }
                        }
                    }
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`Ошибка API: ${errorData.error.message}`);
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
            showLoading(false);
        }
    }

    async function testNetworkSpeed() {
        networkSpeedSpan.textContent = 'тестирование...';
        const testFileUrl = 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Snake_River_%285mb%29.jpg'; // Примерно 5MB файл

        const startTime = performance.now();
        try {
            const response = await fetch(testFileUrl, { cache: 'no-store', mode: 'cors' });
            const blob = await response.blob();
            const endTime = performance.now();

            const durationInSeconds = (endTime - startTime) / 1000;
            const speedBps = (blob.size * 8) / durationInSeconds;
            const speedMbps = (speedBps / 1000 / 1000).toFixed(2);

            networkSpeedSpan.textContent = `${speedMbps} Мбит/с`;
        } catch (error) {
            networkSpeedSpan.textContent = 'ошибка теста';
            console.error('Ошибка при тесте скорости:', error);
        }
    }

    function updateEstimation() {
        const textLength = textInput.value.length;
        // Примерный расчет: 15 символов в секунду + 2с на обработку
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
        const sampleRate = 24000; // Частота дискретизации для Gemini TTS
        const numChannels = 1;
        const bytesPerSample = 2; // 16-bit PCM

        const headerLength = 44;
        const dataLength = pcmData.length;
        const buffer = new ArrayBuffer(headerLength + dataLength);
        const view = new DataView(buffer);

        // RIFF header
        view.setUint32(0, 0x52494646, false); // "RIFF"
        view.setUint32(4, 36 + dataLength, true);
        view.setUint32(8, 0x57415645, false); // "WAVE"

        // "fmt " sub-chunk
        view.setUint32(12, 0x666d7420, false); // "fmt "
        view.setUint32(16, 16, true);
        view.setUint16(20, 1, true); // PCM
        view.setUint16(22, numChannels, true);
        view.setUint32(24, sampleRate, true);
        view.setUint32(28, sampleRate * numChannels * bytesPerSample, true); // Byte rate
        view.setUint16(32, numChannels * bytesPerSample, true); // Block align
        view.setUint16(34, bytesPerSample * 8, true); // Bits per sample

        // "data" sub-chunk
        view.setUint32(36, 0x64617461, false); // "data"
        view.setUint32(40, dataLength, true);

        // PCM data
        new Uint8Array(buffer, headerLength).set(pcmData);

        const blob = new Blob([view], { type: 'audio/wav' });
        return URL.createObjectURL(blob);
    }

    updateEstimation();
});
