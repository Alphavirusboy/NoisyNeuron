// Practice Tools: Tuner, Metronome, and Practice Sessions
class PracticeToolkit {
    constructor() {
        this.tuner = new InstrumentTuner();
        this.metronome = new SmartMetronome();
        this.practiceSession = new PracticeSession();
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Quick action buttons
        document.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                this.handleQuickAction(action);
            });
        });
    }

    handleQuickAction(action) {
        switch (action) {
            case 'tune':
                this.tuner.toggle();
                break;
            case 'metronome':
                this.metronome.toggle();
                break;
            case 'practice':
                this.practiceSession.start();
                break;
            case 'upload':
                // Trigger file upload
                document.getElementById('audioFileInput')?.click();
                break;
        }
    }
}

// Instrument Tuner with Real-time Pitch Detection
class InstrumentTuner {
    constructor() {
        this.isActive = false;
        this.audioContext = null;
        this.analyzer = null;
        this.microphone = null;
        this.dataArray = null;
        this.rafId = null;
        
        // Note frequencies (A4 = 440Hz)
        this.noteFrequencies = {
            'C': 261.63, 'C#': 277.18, 'D': 293.66, 'D#': 311.13,
            'E': 329.63, 'F': 349.23, 'F#': 369.99, 'G': 392.00,
            'G#': 415.30, 'A': 440.00, 'A#': 466.16, 'B': 493.88
        };
        
        this.noteNames = Object.keys(this.noteFrequencies);
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const startTunerBtn = document.getElementById('startTuner');
        if (startTunerBtn) {
            startTunerBtn.addEventListener('click', () => this.toggle());
        }
    }

    async toggle() {
        if (this.isActive) {
            this.stop();
        } else {
            await this.start();
        }
    }

    async start() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: false,
                    autoGainControl: false,
                    noiseSuppression: false
                } 
            });

            // Setup audio context
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyzer = this.audioContext.createAnalyser();
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            
            this.analyzer.fftSize = 8192;
            this.analyzer.smoothingTimeConstant = 0.8;
            this.dataArray = new Float32Array(this.analyzer.frequencyBinCount);
            
            this.microphone.connect(this.analyzer);
            
            this.isActive = true;
            this.updateUI();
            this.startAnalysis();
            
        } catch (error) {
            console.error('Error accessing microphone:', error);
            this.showError('Unable to access microphone. Please check permissions.');
        }
    }

    stop() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
            this.rafId = null;
        }
        
        if (this.microphone) {
            this.microphone.disconnect();
            this.microphone = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        this.isActive = false;
        this.updateUI();
    }

    startAnalysis() {
        const analyze = () => {
            if (!this.isActive) return;
            
            this.analyzer.getFloatFrequencyData(this.dataArray);
            
            // Find the fundamental frequency
            const frequency = this.findFundamentalFrequency();
            
            if (frequency > 0) {
                const noteInfo = this.frequencyToNote(frequency);
                this.updateTunerDisplay(noteInfo);
            }
            
            this.rafId = requestAnimationFrame(analyze);
        };
        
        analyze();
    }

    findFundamentalFrequency() {
        const sampleRate = this.audioContext.sampleRate;
        const nyquist = sampleRate / 2;
        const binSize = nyquist / this.dataArray.length;
        
        // Find the bin with the highest magnitude
        let maxMagnitude = -Infinity;
        let maxBin = 0;
        
        // Only look in the frequency range we care about (80Hz - 2000Hz)
        const minBin = Math.floor(80 / binSize);
        const maxBinIndex = Math.floor(2000 / binSize);
        
        for (let i = minBin; i < maxBinIndex; i++) {
            if (this.dataArray[i] > maxMagnitude) {
                maxMagnitude = this.dataArray[i];
                maxBin = i;
            }
        }
        
        // Only return frequency if the signal is strong enough
        if (maxMagnitude > -60) { // -60 dB threshold
            return maxBin * binSize;
        }
        
        return 0;
    }

    frequencyToNote(frequency) {
        if (frequency <= 0) return null;
        
        // Find the closest note
        let closestNote = 'A';
        let minDiff = Infinity;
        
        this.noteNames.forEach(note => {
            const noteFreq = this.noteFrequencies[note];
            const diff = Math.abs(frequency - noteFreq);
            
            if (diff < minDiff) {
                minDiff = diff;
                closestNote = note;
            }
        });
        
        // Calculate cents off
        const targetFreq = this.noteFrequencies[closestNote];
        const cents = Math.round(1200 * Math.log2(frequency / targetFreq));
        
        return {
            note: closestNote,
            frequency: frequency,
            targetFrequency: targetFreq,
            cents: cents,
            inTune: Math.abs(cents) <= 10 // Within 10 cents is considered in tune
        };
    }

    updateTunerDisplay(noteInfo) {
        const noteDisplay = document.getElementById('detectedNote');
        const freqDisplay = document.getElementById('detectedFreq');
        const needle = document.getElementById('tuningNeedle');
        
        if (noteInfo && noteDisplay && freqDisplay && needle) {
            noteDisplay.textContent = noteInfo.note;
            freqDisplay.textContent = `${Math.round(noteInfo.frequency)} Hz`;
            
            // Update needle position (-50 to +50 cents)
            const needlePosition = Math.max(-50, Math.min(50, noteInfo.cents));
            const needlePercent = ((needlePosition + 50) / 100) * 100;
            needle.style.left = `${needlePercent}%`;
            
            // Color coding
            if (noteInfo.inTune) {
                noteDisplay.className = 'note-display in-tune';
                needle.className = 'meter-needle in-tune';
            } else if (Math.abs(noteInfo.cents) <= 25) {
                noteDisplay.className = 'note-display close';
                needle.className = 'meter-needle close';
            } else {
                noteDisplay.className = 'note-display out-of-tune';
                needle.className = 'meter-needle out-of-tune';
            }
        }
    }

    updateUI() {
        const startBtn = document.getElementById('startTuner');
        if (startBtn) {
            startBtn.textContent = this.isActive ? 'Stop Tuner' : 'Start Tuning';
            startBtn.className = this.isActive ? 'btn btn-secondary' : 'btn btn-primary';
        }
    }

    showError(message) {
        // Show error notification
        console.error(message);
        // You could implement a toast notification here
    }
}

// Smart Metronome with Visual and Audio Cues
class SmartMetronome {
    constructor() {
        this.isPlaying = false;
        this.bpm = 120;
        this.timeSignature = [4, 4];
        this.currentBeat = 0;
        this.intervalId = null;
        this.audioContext = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateDisplay();
    }

    setupEventListeners() {
        const toggleBtn = document.getElementById('metronomeToggle');
        const tempoSlider = document.getElementById('tempoSlider');
        const timeSignatureSelect = document.getElementById('timeSignature');
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => this.toggle());
        }
        
        if (tempoSlider) {
            tempoSlider.addEventListener('input', (e) => {
                this.setBPM(parseInt(e.target.value));
            });
        }
        
        if (timeSignatureSelect) {
            timeSignatureSelect.addEventListener('change', (e) => {
                const [num, den] = e.target.value.split('/').map(Number);
                this.setTimeSignature(num, den);
            });
        }
    }

    toggle() {
        if (this.isPlaying) {
            this.stop();
        } else {
            this.start();
        }
    }

    async start() {
        if (!this.audioContext) {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        if (this.audioContext.state === 'suspended') {
            await this.audioContext.resume();
        }
        
        this.isPlaying = true;
        this.currentBeat = 0;
        this.scheduleNextBeat();
        this.updateUI();
    }

    stop() {
        this.isPlaying = false;
        if (this.intervalId) {
            clearTimeout(this.intervalId);
            this.intervalId = null;
        }
        this.resetVisualBeats();
        this.updateUI();
    }

    scheduleNextBeat() {
        if (!this.isPlaying) return;
        
        const beatInterval = (60 / this.bpm) * 1000; // Convert to milliseconds
        
        this.playBeat();
        this.updateVisualBeat();
        
        this.currentBeat = (this.currentBeat + 1) % this.timeSignature[0];
        
        this.intervalId = setTimeout(() => {
            this.scheduleNextBeat();
        }, beatInterval);
    }

    playBeat() {
        if (!this.audioContext) return;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        // Different pitch for downbeat
        oscillator.frequency.value = this.currentBeat === 0 ? 800 : 400;
        oscillator.type = 'square';
        
        gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + 0.1);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + 0.1);
    }

    updateVisualBeat() {
        const beatIndicators = document.querySelectorAll('#metronomeVisual .beat-indicator');
        
        // Reset all indicators
        beatIndicators.forEach(indicator => {
            indicator.classList.remove('active', 'downbeat');
        });
        
        // Highlight current beat
        if (beatIndicators[this.currentBeat]) {
            beatIndicators[this.currentBeat].classList.add('active');
            if (this.currentBeat === 0) {
                beatIndicators[this.currentBeat].classList.add('downbeat');
            }
        }
    }

    resetVisualBeats() {
        const beatIndicators = document.querySelectorAll('#metronomeVisual .beat-indicator');
        beatIndicators.forEach(indicator => {
            indicator.classList.remove('active', 'downbeat');
        });
    }

    setBPM(bpm) {
        this.bpm = Math.max(40, Math.min(300, bpm));
        this.updateDisplay();
    }

    setTimeSignature(numerator, denominator) {
        this.timeSignature = [numerator, denominator];
        this.updateVisualBeats();
        this.updateDisplay();
    }

    updateVisualBeats() {
        const visualContainer = document.getElementById('metronomeVisual');
        if (!visualContainer) return;
        
        // Clear existing beats
        visualContainer.innerHTML = '';
        
        // Add beat indicators based on time signature
        for (let i = 0; i < this.timeSignature[0]; i++) {
            const indicator = document.createElement('div');
            indicator.className = 'beat-indicator';
            visualContainer.appendChild(indicator);
        }
    }

    updateDisplay() {
        const tempoValue = document.getElementById('tempoValue');
        const tempoSlider = document.getElementById('tempoSlider');
        
        if (tempoValue) {
            tempoValue.textContent = this.bpm;
        }
        
        if (tempoSlider) {
            tempoSlider.value = this.bpm;
        }
    }

    updateUI() {
        const toggleBtn = document.getElementById('metronomeToggle');
        if (toggleBtn) {
            toggleBtn.textContent = this.isPlaying ? 'Stop' : 'Start';
            toggleBtn.className = this.isPlaying ? 'btn btn-secondary' : 'btn btn-primary';
        }
    }
}

// Practice Session Manager
class PracticeSession {
    constructor() {
        this.currentSong = null;
        this.isActive = false;
        this.startTime = null;
        this.pausedTime = 0;
        this.settings = {
            slowPlayback: false,
            loopSection: false,
            chordHighlight: false
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        const startBtn = document.getElementById('startPractice');
        const songSelect = document.getElementById('practiceSong');
        const settingCheckboxes = document.querySelectorAll('.practice-option input[type="checkbox"]');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.start());
        }
        
        if (songSelect) {
            songSelect.addEventListener('change', (e) => {
                this.currentSong = e.target.value;
            });
        }
        
        settingCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const setting = e.target.id;
                this.settings[setting] = e.target.checked;
            });
        });
    }

    start() {
        if (!this.currentSong) {
            this.showError('Please select a song to practice');
            return;
        }
        
        this.isActive = true;
        this.startTime = Date.now();
        this.showPracticeInterface();
        this.updateUI();
    }

    stop() {
        this.isActive = false;
        this.updateUI();
        this.savePracticeSession();
    }

    showPracticeInterface() {
        // Create practice overlay
        const overlay = document.createElement('div');
        overlay.id = 'practiceOverlay';
        overlay.className = 'practice-overlay';
        overlay.innerHTML = `
            <div class="practice-interface">
                <div class="practice-header">
                    <h3>Practicing: ${this.getSongTitle()}</h3>
                    <div class="practice-timer">
                        <i class="fas fa-clock"></i>
                        <span id="practiceTimer">00:00</span>
                    </div>
                    <button id="endPractice" class="btn btn-secondary">
                        <i class="fas fa-stop"></i>
                        End Practice
                    </button>
                </div>
                
                <div class="practice-content">
                    <div class="song-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="songProgress"></div>
                        </div>
                        <div class="time-markers">
                            <span>0:00</span>
                            <span>3:45</span>
                        </div>
                    </div>
                    
                    <div class="current-section">
                        <h4>Current Section</h4>
                        <div class="chord-display">
                            <div class="current-chord">Am</div>
                            <div class="next-chord">F</div>
                        </div>
                    </div>
                    
                    <div class="practice-controls">
                        <button class="practice-btn" id="playPause">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="practice-btn" id="rewind">
                            <i class="fas fa-backward"></i>
                        </button>
                        <button class="practice-btn" id="forward">
                            <i class="fas fa-forward"></i>
                        </button>
                        <button class="practice-btn" id="loopToggle">
                            <i class="fas fa-repeat"></i>
                        </button>
                    </div>
                    
                    <div class="practice-feedback">
                        <div class="accuracy-meter">
                            <label>Playing Accuracy</label>
                            <div class="meter">
                                <div class="meter-fill" style="width: 85%"></div>
                            </div>
                            <span>85%</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Setup practice interface event listeners
        this.setupPracticeControls();
        this.startPracticeTimer();
    }

    setupPracticeControls() {
        const endBtn = document.getElementById('endPractice');
        if (endBtn) {
            endBtn.addEventListener('click', () => {
                this.stop();
                this.hidePracticeInterface();
            });
        }
        
        // Add other control listeners here
    }

    startPracticeTimer() {
        const timer = document.getElementById('practiceTimer');
        if (!timer) return;
        
        const updateTimer = () => {
            if (!this.isActive) return;
            
            const elapsed = Date.now() - this.startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            timer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            setTimeout(updateTimer, 1000);
        };
        
        updateTimer();
    }

    hidePracticeInterface() {
        const overlay = document.getElementById('practiceOverlay');
        if (overlay) {
            overlay.remove();
        }
    }

    getSongTitle() {
        const songSelect = document.getElementById('practiceSong');
        if (songSelect) {
            const selectedOption = songSelect.options[songSelect.selectedIndex];
            return selectedOption.textContent;
        }
        return 'Unknown Song';
    }

    savePracticeSession() {
        const duration = Date.now() - this.startTime;
        const sessionData = {
            song: this.currentSong,
            duration: duration,
            settings: this.settings,
            timestamp: new Date().toISOString()
        };
        
        // Save to localStorage for now (in a real app, you'd send to server)
        const sessions = JSON.parse(localStorage.getItem('practiceSessions') || '[]');
        sessions.push(sessionData);
        localStorage.setItem('practiceSessions', JSON.stringify(sessions));
        
        console.log('Practice session saved:', sessionData);
    }

    updateUI() {
        const startBtn = document.getElementById('startPractice');
        if (startBtn) {
            startBtn.textContent = this.isActive ? 'End Practice' : 'Start Practice Session';
            startBtn.className = this.isActive ? 'btn btn-secondary' : 'btn btn-primary';
        }
    }

    showError(message) {
        console.error(message);
        // Implement toast notification
    }
}

// Initialize Practice Tools
document.addEventListener('DOMContentLoaded', function() {
    window.practiceToolkit = new PracticeToolkit();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PracticeToolkit, InstrumentTuner, SmartMetronome, PracticeSession };
}
