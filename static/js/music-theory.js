// Music Theory and Learning Features
class MusicTheoryEngine {
    constructor() {
        this.currentInstrument = 'guitar';
        this.currentSkillLevel = 1;
        this.chordSubstitutions = {};
        this.chordDatabase = this.initializeChordDatabase();
        this.init();
    }

    initializeChordDatabase() {
        return {
            guitar: {
                'C': { frets: [null, 3, 2, 0, 1, 0], difficulty: 1 },
                'G': { frets: [3, 2, 0, 0, 3, 3], difficulty: 2 },
                'Am': { frets: [null, 0, 2, 2, 1, 0], difficulty: 1 },
                'F': { frets: [1, 3, 3, 2, 1, 1], difficulty: 3 },
                'D': { frets: [null, null, 0, 2, 3, 2], difficulty: 2 },
                'Em': { frets: [0, 2, 2, 0, 0, 0], difficulty: 1 },
                'A': { frets: [null, 0, 2, 2, 2, 0], difficulty: 2 },
                'E': { frets: [0, 2, 2, 1, 0, 0], difficulty: 2 },
                'Dm': { frets: [null, null, 0, 2, 3, 1], difficulty: 2 },
                'B7': { frets: [null, 2, 1, 2, 0, 2], difficulty: 3 },
                'Cadd9': { frets: [null, 3, 2, 0, 3, 0], difficulty: 2 },
                'Gsus4': { frets: [3, 3, 0, 0, 3, 3], difficulty: 2 }
            },
            piano: {
                'C': { keys: ['C', 'E', 'G'], difficulty: 1 },
                'G': { keys: ['G', 'B', 'D'], difficulty: 1 },
                'Am': { keys: ['A', 'C', 'E'], difficulty: 1 },
                'F': { keys: ['F', 'A', 'C'], difficulty: 2 },
                'D': { keys: ['D', 'F#', 'A'], difficulty: 2 },
                'Em': { keys: ['E', 'G', 'B'], difficulty: 1 },
                'A': { keys: ['A', 'C#', 'E'], difficulty: 2 },
                'E': { keys: ['E', 'G#', 'B'], difficulty: 2 },
                'Dm': { keys: ['D', 'F', 'A'], difficulty: 1 },
                'B7': { keys: ['B', 'D#', 'F#', 'A'], difficulty: 3 }
            },
            ukulele: {
                'C': { frets: [0, 0, 0, 3], difficulty: 1 },
                'G': { frets: [0, 2, 3, 2], difficulty: 2 },
                'Am': { frets: [2, 0, 0, 0], difficulty: 1 },
                'F': { frets: [2, 0, 1, 0], difficulty: 1 },
                'D': { frets: [2, 2, 2, 0], difficulty: 2 },
                'Em': { frets: [0, 4, 3, 2], difficulty: 3 },
                'A': { frets: [2, 1, 0, 0], difficulty: 2 },
                'E': { frets: [1, 4, 0, 2], difficulty: 3 }
            }
        };
    }

    init() {
        this.setupEventListeners();
        this.loadChordLibrary();
    }

    setupEventListeners() {
        // Instrument selector
        document.querySelectorAll('.instrument-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectInstrument(e.currentTarget.dataset.instrument);
            });
        });

        // Skill level selector
        document.querySelectorAll('.skill-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectSkillLevel(parseInt(e.currentTarget.dataset.level));
            });
        });

        // Chord input and substitution
        const chordInput = document.getElementById('chordInput');
        const getSubstitutionsBtn = document.getElementById('getSubstitutions');
        
        if (chordInput && getSubstitutionsBtn) {
            getSubstitutionsBtn.addEventListener('click', () => {
                this.getChordSubstitutions(chordInput.value);
            });

            chordInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.getChordSubstitutions(chordInput.value);
                }
            });
        }
    }

    selectInstrument(instrument) {
        this.currentInstrument = instrument;
        
        // Update UI
        document.querySelectorAll('.instrument-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-instrument="${instrument}"]`).classList.add('active');
        
        // Reload chord library for new instrument
        this.loadChordLibrary();
    }

    selectSkillLevel(level) {
        this.currentSkillLevel = level;
        
        // Update UI
        document.querySelectorAll('.skill-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-level="${level}"]`).classList.add('active');
    }

    async getChordSubstitutions(chord) {
        if (!chord || chord.trim() === '') {
            this.showError('Please enter a chord name (e.g., F, Bm, C#7)');
            return;
        }

        const cleanChord = chord.trim();
        
        try {
            // Show loading
            this.showLoadingSubstitutions();
            
            // Make API call to get chord substitutions
            const response = await fetch('/music-theory/chord-recommendations/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    chord: cleanChord,
                    instrument: this.currentInstrument,
                    skill_level: this.currentSkillLevel
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.displayChordSubstitutions(cleanChord, data.recommendations);
            } else {
                this.showError(data.error || 'Failed to get chord substitutions');
            }
        } catch (error) {
            console.error('Error getting chord substitutions:', error);
            this.showError('Network error. Please try again.');
        }
    }

    showLoadingSubstitutions() {
        const container = document.getElementById('chordSubstitutions');
        container.innerHTML = `
            <div class="loading-substitutions">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Finding easier alternatives...</p>
            </div>
        `;
    }

    displayChordSubstitutions(originalChord, substitutions) {
        const container = document.getElementById('chordSubstitutions');
        
        if (!substitutions || substitutions.length === 0) {
            container.innerHTML = `
                <div class="no-substitutions">
                    <h4>Good news!</h4>
                    <p>The chord <strong>${originalChord}</strong> is already suitable for your skill level on ${this.currentInstrument}.</p>
                </div>
            `;
            return;
        }

        let html = `
            <div class="substitutions-header">
                <h4>Easier alternatives for <span class="original-chord">${originalChord}</span>:</h4>
                <p>Here are some chords that are easier to play and will sound great in your song:</p>
            </div>
            <div class="chord-alternatives">
        `;

        substitutions.forEach(sub => {
            const difficultyDots = this.createDifficultyIndicator(sub.difficulty);
            html += `
                <div class="alternative-card" data-chord="${sub.chord}">
                    <div class="alternative-chord">${sub.chord}</div>
                    <div class="alternative-reason">${sub.reason}</div>
                    <div class="difficulty-info">
                        <span>Difficulty: </span>
                        <div class="difficulty-indicator">${difficultyDots}</div>
                    </div>
                    <div class="confidence-score">
                        <span>Match: ${Math.round(sub.confidence * 100)}%</span>
                    </div>
                    <button class="btn btn-outline btn-small learn-chord-btn" data-chord="${sub.chord}">
                        <i class="fas fa-graduation-cap"></i>
                        Learn This Chord
                    </button>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

        // Add event listeners to learn chord buttons
        container.querySelectorAll('.learn-chord-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chord = e.currentTarget.dataset.chord;
                this.showChordLearning(chord);
            });
        });
    }

    createDifficultyIndicator(difficulty) {
        let dots = '';
        for (let i = 1; i <= 5; i++) {
            const filled = i <= difficulty ? 'filled' : '';
            dots += `<div class="difficulty-dot ${filled}"></div>`;
        }
        return dots;
    }

    showChordLearning(chord) {
        // This would open a chord learning interface
        // For now, we'll show a simple modal
        this.showChordModal(chord);
    }

    showChordModal(chord) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Learn ${chord} on ${this.currentInstrument}</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="chord-learning-content">
                        <div class="chord-diagram">
                            <p>Chord diagram for ${chord} would appear here</p>
                            <div class="placeholder-diagram">
                                <i class="fas fa-guitar" style="font-size: 4rem; color: #667eea;"></i>
                            </div>
                        </div>
                        <div class="chord-instructions">
                            <h4>How to play ${chord}:</h4>
                            <ol>
                                <li>Place your fingers according to the diagram above</li>
                                <li>Press down firmly but don't over-squeeze</li>
                                <li>Strum all strings and adjust finger pressure as needed</li>
                                <li>Practice transitioning from other chords you know</li>
                            </ol>
                        </div>
                        <div class="chord-tips">
                            <h4>Practice Tips:</h4>
                            <ul>
                                <li>Start slowly and focus on clean notes</li>
                                <li>Use a metronome once you can play the chord cleanly</li>
                                <li>Practice chord changes with songs you know</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        modal.style.display = 'block';

        // Close modal events
        const closeBtn = modal.querySelector('.modal-close');
        closeBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    async loadChordLibrary() {
        const chordGrid = document.getElementById('chordGrid');
        if (!chordGrid) return;

        const chords = Object.keys(this.chordDatabase[this.currentInstrument]);
        chordGrid.innerHTML = '';

        chords.forEach(chord => {
            const chordElement = this.createChordDiagram(chord);
            chordGrid.appendChild(chordElement);
        });
    }

    createChordDiagram(chordName) {
        const chordData = this.chordDatabase[this.currentInstrument][chordName];
        const container = document.createElement('div');
        container.className = 'chord-diagram';
        container.addEventListener('click', () => {
            this.playChordPreview(chordName);
        });

        const nameDisplay = document.createElement('div');
        nameDisplay.className = 'chord-name-display';
        nameDisplay.textContent = chordName;

        let diagramHTML;
        if (this.currentInstrument === 'guitar' || this.currentInstrument === 'ukulele') {
            diagramHTML = this.createGuitarDiagram(chordData, this.currentInstrument);
        } else if (this.currentInstrument === 'piano') {
            diagramHTML = this.createPianoDiagram(chordData);
        }

        const difficultyBadge = document.createElement('div');
        difficultyBadge.className = `difficulty-badge difficulty-${this.getDifficultyLabel(chordData.difficulty)}`;
        difficultyBadge.textContent = this.getDifficultyLabel(chordData.difficulty);

        container.appendChild(nameDisplay);
        container.appendChild(diagramHTML);
        container.appendChild(difficultyBadge);

        return container;
    }

    createGuitarDiagram(chordData, instrument) {
        const diagram = document.createElement('div');
        diagram.className = `${instrument}-diagram`;

        const fretboard = document.createElement('div');
        fretboard.className = 'fretboard';

        // Add frets
        for (let i = 1; i <= 4; i++) {
            const fret = document.createElement('div');
            fret.className = 'fret';
            fretboard.appendChild(fret);
        }

        // Add strings
        const numStrings = instrument === 'guitar' ? 6 : 4;
        for (let i = 1; i <= numStrings; i++) {
            const string = document.createElement('div');
            string.className = 'string';
            fretboard.appendChild(string);
        }

        // Add finger positions
        chordData.frets.forEach((fret, index) => {
            const stringPosition = (index + 1) * (100 / (numStrings + 1));
            
            if (fret === null) {
                // Muted string
                const muted = document.createElement('div');
                muted.className = 'muted-string';
                muted.textContent = '×';
                muted.style.left = stringPosition + '%';
                fretboard.appendChild(muted);
            } else if (fret === 0) {
                // Open string
                const open = document.createElement('div');
                open.className = 'open-string';
                open.textContent = '○';
                open.style.left = stringPosition + '%';
                fretboard.appendChild(open);
            } else {
                // Finger position
                const finger = document.createElement('div');
                finger.className = 'finger-position';
                finger.style.left = stringPosition + '%';
                finger.style.top = (fret * 20 - 10) + '%';
                fretboard.appendChild(finger);
            }
        });

        diagram.appendChild(fretboard);
        return diagram;
    }

    createPianoDiagram(chordData) {
        const diagram = document.createElement('div');
        diagram.className = 'piano-diagram';

        const keys = document.createElement('div');
        keys.className = 'piano-keys';

        const whiteKeys = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
        const blackKeys = ['C#', 'D#', '', 'F#', 'G#', 'A#', ''];

        whiteKeys.forEach((keyName, index) => {
            const key = document.createElement('div');
            key.className = 'white-key';
            if (chordData.keys.includes(keyName)) {
                key.classList.add('active');
            }
            keys.appendChild(key);

            // Add black key after this white key if it exists
            if (blackKeys[index]) {
                const blackKey = document.createElement('div');
                blackKey.className = 'black-key';
                blackKey.style.left = `${(index + 0.7) * (100 / 7)}%`;
                if (chordData.keys.includes(blackKeys[index])) {
                    blackKey.classList.add('active');
                }
                keys.appendChild(blackKey);
            }
        });

        diagram.appendChild(keys);
        return diagram;
    }

    getDifficultyLabel(difficulty) {
        switch (difficulty) {
            case 1: return 'easy';
            case 2: return 'medium';
            case 3: return 'hard';
            default: return 'medium';
        }
    }

    playChordPreview(chordName) {
        // Add visual feedback
        const allDiagrams = document.querySelectorAll('.chord-diagram');
        allDiagrams.forEach(d => d.classList.remove('selected'));
        
        event.currentTarget.classList.add('selected');
        
        // Here you could add Web Audio API chord synthesis
        console.log(`Playing chord preview for ${chordName} on ${this.currentInstrument}`);
        
        // Add chord to input if chord helper is visible
        const chordInput = document.getElementById('chordInput');
        if (chordInput) {
            chordInput.value = chordName;
        }
    }

    populateSampleChordLibrary() {
        const chordGrid = document.getElementById('chordGrid');
        if (!chordGrid) return;

        const sampleChords = {
            guitar: [
                { name: 'C', difficulty: 1 },
                { name: 'G', difficulty: 1 },
                { name: 'Am', difficulty: 1 },
                { name: 'Em', difficulty: 1 },
                { name: 'D', difficulty: 2 },
                { name: 'A', difficulty: 2 },
                { name: 'Dm', difficulty: 2 },
                { name: 'E', difficulty: 2 },
                { name: 'F', difficulty: 4 },
                { name: 'Bm', difficulty: 4 }
            ],
            piano: [
                { name: 'C', difficulty: 1 },
                { name: 'F', difficulty: 1 },
                { name: 'G', difficulty: 1 },
                { name: 'Am', difficulty: 1 },
                { name: 'Dm', difficulty: 1 },
                { name: 'Em', difficulty: 2 },
                { name: 'A', difficulty: 2 },
                { name: 'D', difficulty: 2 },
                { name: 'E', difficulty: 2 },
                { name: 'Bb', difficulty: 3 }
            ],
            ukulele: [
                { name: 'C', difficulty: 1 },
                { name: 'F', difficulty: 1 },
                { name: 'G', difficulty: 1 },
                { name: 'Am', difficulty: 1 },
                { name: 'Dm', difficulty: 2 },
                { name: 'Em', difficulty: 2 },
                { name: 'A', difficulty: 2 },
                { name: 'D', difficulty: 2 },
                { name: 'E', difficulty: 3 },
                { name: 'Bm', difficulty: 4 }
            ]
        };

        const chords = sampleChords[this.currentInstrument] || sampleChords.guitar;
        
        let html = '';
        chords.forEach(chord => {
            const difficultyDots = this.createDifficultyIndicator(chord.difficulty);
            html += `
                <div class="chord-card" data-chord="${chord.name}">
                    <div class="chord-name">${chord.name}</div>
                    <div class="chord-diagram-mini">
                        <i class="fas fa-${this.currentInstrument === 'piano' ? 'piano' : 'guitar'}"></i>
                    </div>
                    <div class="chord-difficulty">
                        <div class="difficulty-indicator">${difficultyDots}</div>
                    </div>
                    <button class="btn btn-outline btn-small">Learn</button>
                </div>
            `;
        });

        chordGrid.innerHTML = html;

        // Add click listeners to chord cards
        chordGrid.querySelectorAll('.chord-card button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const chord = e.currentTarget.closest('.chord-card').dataset.chord;
                this.showChordLearning(chord);
            });
        });
    }

    showError(message) {
        const container = document.getElementById('chordSubstitutions');
        container.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            </div>
        `;
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

// Song Analysis and Key Detection
class SongAnalyzer {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // File upload for analysis
        const fileInput = document.getElementById('audioFileInput');
        const uploadArea = document.getElementById('uploadArea');
        
        if (fileInput && uploadArea) {
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            uploadArea.addEventListener('drop', this.handleDrop.bind(this));
            fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        }
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('drag-over');
    }

    handleDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.analyzeAudioFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (file) {
            this.analyzeAudioFile(file);
        }
    }

    async analyzeAudioFile(file) {
        // Validate file
        if (!this.validateAudioFile(file)) {
            return;
        }

        try {
            this.showAnalysisProgress();
            
            const formData = new FormData();
            formData.append('audio_file', file);

            const response = await fetch('/music-theory/api/songs/analyze_harmony/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });

            const data = await response.json();
            
            if (response.ok) {
                this.displayAnalysisResults(data);
            } else {
                this.showAnalysisError(data.error || 'Analysis failed');
            }
        } catch (error) {
            console.error('Error analyzing audio:', error);
            this.showAnalysisError('Network error during analysis');
        }
    }

    validateAudioFile(file) {
        const maxSize = 100 * 1024 * 1024; // 100MB
        const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/mp4'];
        
        if (file.size > maxSize) {
            this.showError('File too large. Maximum size is 100MB.');
            return false;
        }
        
        if (!allowedTypes.includes(file.type)) {
            this.showError('Unsupported file type. Please use MP3, WAV, FLAC, or M4A.');
            return false;
        }
        
        return true;
    }

    showAnalysisProgress() {
        const processingSection = document.getElementById('processingSection');
        if (processingSection) {
            processingSection.style.display = 'block';
            this.updateProgress(0, 'Uploading file...');
            
            // Simulate progress updates
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 20;
                if (progress >= 90) {
                    clearInterval(interval);
                    this.updateProgress(90, 'Finalizing analysis...');
                } else {
                    this.updateProgress(progress, 'Analyzing audio patterns...');
                }
            }, 1000);
        }
    }

    updateProgress(percentage, text) {
        const progressBar = document.getElementById('processingProgress');
        const progressText = document.getElementById('processingText');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
    }

    displayAnalysisResults(data) {
        this.updateProgress(100, 'Analysis complete!');
        
        setTimeout(() => {
            const processingSection = document.getElementById('processingSection');
            const resultsSection = document.getElementById('resultsSection');
            
            if (processingSection) processingSection.style.display = 'none';
            if (resultsSection) {
                resultsSection.style.display = 'block';
                resultsSection.innerHTML = this.createResultsHTML(data);
            }
        }, 1000);
    }

    createResultsHTML(data) {
        return `
            <div class="analysis-results">
                <div class="results-header">
                    <h3>Audio Analysis Results</h3>
                    <p>Here's what our AI discovered about your song:</p>
                </div>
                
                <div class="results-grid">
                    <div class="result-card">
                        <div class="result-icon">
                            <i class="fas fa-key"></i>
                        </div>
                        <div class="result-content">
                            <h4>Key Signature</h4>
                            <div class="result-value">${data.key || 'Unknown'}</div>
                        </div>
                    </div>
                    
                    <div class="result-card">
                        <div class="result-icon">
                            <i class="fas fa-stopwatch"></i>
                        </div>
                        <div class="result-content">
                            <h4>Tempo</h4>
                            <div class="result-value">${Math.round(data.tempo || 0)} BPM</div>
                        </div>
                    </div>
                    
                    <div class="result-card">
                        <div class="result-icon">
                            <i class="fas fa-clock"></i>
                        </div>
                        <div class="result-content">
                            <h4>Duration</h4>
                            <div class="result-value">${this.formatDuration(data.duration || 0)}</div>
                        </div>
                    </div>
                </div>
                
                ${data.chord_progression ? this.createChordProgressionHTML(data.chord_progression) : ''}
                
                <div class="results-actions">
                    <button class="btn btn-primary" onclick="musicTheory.getBeginnerVersion()">
                        <i class="fas fa-magic"></i>
                        Get Beginner-Friendly Version
                    </button>
                    <button class="btn btn-outline" onclick="this.startPracticeMode()">
                        <i class="fas fa-play"></i>
                        Practice This Song
                    </button>
                </div>
            </div>
        `;
    }

    createChordProgressionHTML(progression) {
        if (!progression || progression.length === 0) {
            return '';
        }

        let html = `
            <div class="chord-progression-section">
                <h4>Detected Chord Progression</h4>
                <div class="chord-timeline">
        `;

        progression.forEach((item, index) => {
            const timestamp = this.formatTime(item.timestamp || 0);
            const confidence = Math.round((item.confidence || 0) * 100);
            
            html += `
                <div class="chord-item" data-timestamp="${item.timestamp}">
                    <div class="chord-time">${timestamp}</div>
                    <div class="chord-name">${item.chord}</div>
                    <div class="chord-confidence">${confidence}%</div>
                </div>
            `;
        });

        html += `
                </div>
                <p class="progression-note">
                    <i class="fas fa-lightbulb"></i>
                    Click "Get Beginner-Friendly Version" to see easier chord alternatives!
                </p>
            </div>
        `;

        return html;
    }

    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    showAnalysisError(message) {
        const processingSection = document.getElementById('processingSection');
        if (processingSection) {
            processingSection.style.display = 'none';
        }
        
        this.showError(message);
    }

    showError(message) {
        // Show error in a user-friendly way
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button class="error-close">&times;</button>
            </div>
        `;

        document.body.appendChild(errorDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);

        // Manual close
        errorDiv.querySelector('.error-close').addEventListener('click', () => {
            errorDiv.parentNode.removeChild(errorDiv);
        });
    }

    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.musicTheory = new MusicTheoryEngine();
    window.songAnalyzer = new SongAnalyzer();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MusicTheoryEngine, SongAnalyzer };
}
