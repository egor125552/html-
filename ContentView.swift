 import SwiftUI
import CoreHaptics
import AVFoundation
import Accelerate
import Combine // Добавил для надежности

struct ContentView: View {
    @StateObject private var engine = MidiTrackerEngine()

    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            VStack(spacing: 40) {
                Text("V9: MIDI TRACKER FINAL")
                    .font(.system(size: 26, weight: .black, design: .monospaced))
                    .foregroundColor(.purple)
                    .multilineTextAlignment(.center)

                if engine.isAnalyzing {
                    VStack(spacing: 20) {
                        ProgressView(value: engine.progress, total: 1.0)
                            .progressViewStyle(LinearProgressViewStyle(tint: .purple))
                            .padding(.horizontal, 40)

                        Text("ANALYZING WAVEFORMS...")
                            .font(.caption).foregroundColor(.gray)
                            .monospacedDigit()
                    }
                } else {
                    Button(action: { engine.togglePlayback() }) {
                        ZStack {
                            Circle()
                                .fill(LinearGradient(colors: [.purple, .indigo], startPoint: .top, endPoint: .bottom))
                                .frame(width: 120, height: 120)
                                .shadow(color: .purple.opacity(0.6), radius: 20, x: 0, y: 0)

                            Image(systemName: engine.isPlaying ? "stop.fill" : "play.fill")
                                .font(.system(size: 50))
                                .foregroundColor(.white)
                        }
                    }

                    VStack(spacing: 8) {
                        Text("DETECTED NOTES: \(engine.totalNotes)")
                            .font(.headline)
                            .foregroundColor(.white)

                        Text(engine.status)
                            .font(.caption)
                            .foregroundColor(.gray)
                    }
                }
            }
        }
        .onAppear { engine.startProcessing() }
    }
}

// MARK: - DATA STRUCTURES
struct HapticNote {
    let startTime: Double
    let duration: Double
    let intensity: Float
    let sharpness: Float
    let type: Int // 0:Kick, 1:Bass, etc.
}

// MARK: - CUSTOM ERRORS
enum AudioProcessingError: LocalizedError {
    case fileNotFound(String)
    case fileReadError(String)
    case hapticsNotSupported
    case hapticEngineSetupError(Error)
    case patternGenerationError(Error)
    case playerCreationError(Error)
    case audioSystemError(Error)

    var errorDescription: String? {
        switch self {
        case .fileNotFound(let name): return "ERROR: File '\(name)' not found."
        case .fileReadError(let name): return "ERROR: Could not read data from '\(name)'."
        case .hapticsNotSupported: return "ERROR: Haptics not supported on this device."
        case .hapticEngineSetupError: return "ERROR: Failed to set up haptic engine."
        case .patternGenerationError: return "ERROR: Failed to generate haptic pattern."
        case .playerCreationError: return "ERROR: Failed to create haptic player."
        case .audioSystemError: return "ERROR: Audio system failed."
        }
    }
}


// MARK: - ENGINE CLASS
class MidiTrackerEngine: ObservableObject {
    // Audio
    private var audioEngine = AVAudioEngine()
    private var players: [AVAudioPlayerNode] = []
    private var audioFiles: [AVAudioFile] = []
    private let fileNames = ["drums", "bass", "guitar", "piano", "other"]

    // Haptic
    private var hapticEngine: CHHapticEngine?
    private var hapticPlayer: CHHapticAdvancedPatternPlayer?

    // State
    @Published var isAnalyzing = true
    @Published var progress: Double = 0.0
    @Published var isPlaying = false
    @Published var totalNotes = 0
    @Published var status = "INITIALIZING..."

    private var finalPattern: CHHapticPattern?
    private let analysisRate = 100.0 // Анализируем каждые 10мс
    private let latencyFix = -0.03   // Сдвигаем вибрацию чуть раньше

    init() {
        // Инициализация теперь происходит в startProcessing, чтобы ловить ошибки
    }

    private func setupAudioSession() throws {
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            throw AudioProcessingError.audioSystemError(error)
        }
    }

    private func setupHaptics() throws {
        guard CHHapticEngine.capabilitiesForHardware().supportsHaptics else {
            throw AudioProcessingError.hapticsNotSupported
        }
        do {
            hapticEngine = try CHHapticEngine()
            // Обработчик перезапуска, если система остановила движок
            hapticEngine?.stoppedHandler = { reason in
                print("Haptic engine stopped: \(reason)")
            }
            hapticEngine?.resetHandler = { [weak self] in
                print("Haptic engine reset. Restarting...")
                do {
                    try self?.hapticEngine?.start()
                } catch {
                    DispatchQueue.main.async {
                        self?.status = AudioProcessingError.hapticEngineSetupError(error).localizedDescription
                    }
                }
            }
        } catch {
            throw AudioProcessingError.hapticEngineSetupError(error)
        }
    }

    func startProcessing() {
        DispatchQueue.global(qos: .userInteractive).async {
            do {
                // Выполняем всю настройку здесь, чтобы передать ошибки на UI
                try self.setupAudioSession()
                try self.setupHaptics()
                try self.preparePlayers()

                let detectedNotes = try self.detectNotes()
                self.finalPattern = try self.generateHapticPattern(from: detectedNotes)

                DispatchQueue.main.async {
                    self.totalNotes = detectedNotes.count
                    self.progress = 1.0
                    self.isAnalyzing = false
                    self.status = "READY"
                }
            } catch {
                // Если любая стадия провалилась, показываем ошибку
                DispatchQueue.main.async {
                    self.status = (error as? LocalizedError)?.errorDescription ?? "Unknown error"
                    self.isAnalyzing = false
                }
            }
        }
    }

    private func detectNotes() throws -> [HapticNote] {
        var detectedNotes: [HapticNote] = []
        var sampleRate: Double = 44100.0
        var totalFrames: Int = 0

        // 1. ЗАГРУЗКА И НОРМАЛИЗАЦИЯ ДАННЫХ
        var stemsData: [[Float]] = []
        for (index, file) in audioFiles.enumerated() {
            guard let buffer = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: UInt32(file.length)) else {
                throw AudioProcessingError.fileReadError(fileNames[index])
            }
            try file.read(into: buffer)

            guard let channelData = buffer.floatChannelData?[0] else {
                throw AudioProcessingError.fileReadError(fileNames[index])
            }

            var rawData = Array(UnsafeBufferPointer(start: channelData, count: Int(buffer.frameLength)))

            // НОРМАЛИЗАЦИЯ: Приводим пиковую громкость к 1.0
            var maxVal: Float = 0.0
            vDSP_maxv(rawData, 1, &maxVal, vDSP_Length(rawData.count))
            if maxVal > 0.0 {
                vDSP_vsmul(rawData, 1, [1.0 / maxVal], &rawData, 1, vDSP_Length(rawData.count))
            }

            stemsData.append(rawData)
            sampleRate = file.processingFormat.sampleRate
            totalFrames = max(totalFrames, Int(buffer.frameLength))

            // Обновляем прогресс-бар после загрузки каждого файла
            let loadProgress = Double(index + 1) / Double(audioFiles.count) * 0.5
            DispatchQueue.main.async { self.progress = loadProgress }
        }

        // 2. АНАЛИЗ НОТ (SEGMENTATION)
        let step = Int(sampleRate / analysisRate)
        var isNoteOn = [false, false, false, false, false]
        var noteStart = [0.0, 0.0, 0.0, 0.0, 0.0]
        var notePeakVol = [0.0, 0.0, 0.0, 0.0, 0.0]
        let thresholds: [Float] = [0.15, 0.08, 0.08, 0.08, 0.08] // Пороги для нормализованных данных

        var lastUIUpdateTime = Date()

        for cursor in stride(from: 0, to: totalFrames - step, by: step) {
            let time = Double(cursor) / sampleRate

            for (i, stem) in stemsData.enumerated() {
                if cursor + step >= stem.count { continue }

                var rms: Float = 0
                stem.withUnsafeBufferPointer { ptr in
                    guard let base = ptr.baseAddress else { return }
                    vDSP_measqv(base + cursor, 1, &rms, UInt(step))
                }
                let vol = sqrt(rms)

                if vol > thresholds[i] {
                    if !isNoteOn[i] {
                        isNoteOn[i] = true
                        noteStart[i] = time
                        notePeakVol[i] = Double(vol)
                    } else {
                        if Double(vol) > notePeakVol[i] { notePeakVol[i] = Double(vol) }
                    }
                } else {
                    if isNoteOn[i] {
                        saveNote(index: i, start: noteStart[i], end: time, peak: notePeakVol[i], into: &detectedNotes)
                        isNoteOn[i] = false
                    }
                }
            }

            // ОПТИМИЗАЦИЯ: Обновляем UI не чаще 10 раз в секунду
            if lastUIUpdateTime.timeIntervalSinceNow < -0.1 {
                let analysisProgress = 0.5 + (Double(cursor) / Double(totalFrames) * 0.5)
                DispatchQueue.main.async { self.progress = analysisProgress }
                lastUIUpdateTime = Date()
            }
        }

        let finalTime = Double(totalFrames) / sampleRate
        for i in 0..<5 where isNoteOn[i] {
            saveNote(index: i, start: noteStart[i], end: finalTime, peak: notePeakVol[i], into: &detectedNotes)
        }

        return detectedNotes
    }

    private func generateHapticPattern(from notes: [HapticNote]) throws -> CHHapticPattern {
        var events: [CHHapticEvent] = []
        let sortedNotes = notes.sorted { $0.startTime < $1.startTime }

        for note in sortedNotes {
            let hapticTime = max(0, note.startTime + latencyFix)

            let event: CHHapticEvent
            if note.type == 0 { // DRUMS (Transient)
                event = CHHapticEvent(
                    eventType: .hapticTransient,
                    parameters: [
                        CHHapticEventParameter(parameterID: .hapticIntensity, value: note.intensity),
                        CHHapticEventParameter(parameterID: .hapticSharpness, value: 1.0)
                    ],
                    relativeTime: hapticTime
                )
            } else { // MELODY / BASS (Continuous)
                let safeDuration = min(note.duration, 2.0) // Ограничиваем длину вибрации
                let dynamicAttack = min(0.05, Float(safeDuration) * 0.2)
                let dynamicDecay = min(0.1, Float(safeDuration) * 0.2)

                event = CHHapticEvent(
                    eventType: .hapticContinuous,
                    parameters: [
                        CHHapticEventParameter(parameterID: .hapticIntensity, value: note.intensity),
                        CHHapticEventParameter(parameterID: .hapticSharpness, value: note.sharpness),
                        CHHapticEventParameter(parameterID: .attackTime, value: dynamicAttack),
                        CHHapticEventParameter(parameterID: .decayTime, value: dynamicDecay)
                    ],
                    relativeTime: hapticTime,
                    duration: safeDuration
                )
            }
            events.append(event)
        }

        do {
            return try CHHapticPattern(events: events, parameters: [])
        } catch {
            throw AudioProcessingError.patternGenerationError(error)
        }
    }

    private func saveNote(index: Int, start: Double, end: Double, peak: Double, into notes: inout [HapticNote]) {
        let duration = end - start
        if duration <= 0.03 && index != 0 { return } // Фильтр шумов

        let sharpness: Float
        switch index {
        case 0: sharpness = 1.0 // Drums
        case 1: sharpness = 0.0 // Bass (Глухой)
        case 2: sharpness = 0.4 // Guitar (Шершавый)
        case 3: sharpness = 0.8 // Piano (Звонкий)
        default: sharpness = 0.5
        }

        let note = HapticNote(
            startTime: start,
            duration: duration,
            intensity: Float(min(peak, 1.0)),
            sharpness: sharpness,
            type: index
        )
        notes.append(note)
    }

    private func preparePlayers() throws {
        // Очищаем предыдущие данные
        audioEngine.stop()
        audioEngine.reset()
        players.removeAll()
        audioFiles.removeAll()

        let mixer = audioEngine.mainMixerNode

        for name in fileNames {
            guard let url = Bundle.main.url(forResource: name, withExtension: "mp3") ?? Bundle.main.url(forResource: name, withExtension: "wav") else {
                throw AudioProcessingError.fileNotFound(name)
            }
            do {
                let file = try AVAudioFile(forReading: url)
                audioFiles.append(file)
                let player = AVAudioPlayerNode()
                audioEngine.attach(player)
                audioEngine.connect(player, to: mixer, format: file.processingFormat)
                players.append(player)
            } catch {
                throw AudioProcessingError.fileReadError(name)
            }
        }

        // Заранее готовим движок, чтобы избежать задержек при старте
        audioEngine.prepare()
    }

    func togglePlayback() {
        // Убеждаемся, что аудио движок запущен
        if !audioEngine.isRunning {
            do {
                try audioEngine.start()
            } catch {
                status = AudioProcessingError.audioSystemError(error).localizedDescription
                return
            }
        }

        if isPlaying {
            // Остановка
            players.forEach { $0.stop() }
            hapticPlayer?.stop(atTime: 0, completionHandler: { _ in })
            isPlaying = false
            status = "STOPPED"
        } else {
            // Воспроизведение
            guard let pattern = finalPattern, let engine = hapticEngine else { return }
            do {
                try engine.start()
                hapticPlayer = try engine.makeAdvancedPlayer(with: pattern)

                // Перезапускаем плееры с начала
                for (i, player) in players.enumerated() {
                    player.scheduleFile(audioFiles[i], at: nil)
                }

                // Синхронный старт
                let audioStartTime = players.first?.lastRenderTime?.hostTime ?? mach_absolute_time()
                players.forEach { $0.play(at: AVAudioTime(hostTime: audioStartTime)) }
                try hapticPlayer?.start(atTime: 0)

                isPlaying = true
                status = "PLAYING TRACK"
            } catch {
                status = AudioProcessingError.playerCreationError(error).localizedDescription
            }
        }
    }
}
