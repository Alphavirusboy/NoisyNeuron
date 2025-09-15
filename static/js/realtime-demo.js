/**
 * Real-time Audio Processing and Music Theory Demo Interface
 * Demonstrates WebSocket integration and enhanced features
 */

class RealTimeDemo {
    constructor() {
        this.wsManager = window.wsManager;
        this.currentProcessing = null;
        this.progressBar = null;
        this.statusDisplay = null;
        
        this.init();
    }
    
    init() {
        this.createDemoInterface();
        this.setupEventListeners();
        this.setupWebSocketHandlers();
        
        console.log('🎵 Real-time demo interface initialized');
    }
    
    createDemoInterface() {
        // Create main demo container
        const demoContainer = document.createElement('div');
        demoContainer.id = 'realtime-demo';
        demoContainer.className = 'demo-container';
        demoContainer.innerHTML = `
            <div class="demo-section">
                <h2>🎵 NoisyNeuron Real-Time Demo</h2>
                
                <!-- Connection Status -->
                <div class="connection-status">
                    <div class="status-indicator">
                        <span class="status-dot" id="audio-status"></span>
                        <span>Audio Processing</span>
                    </div>
                    <div class="status-indicator">
                        <span class="status-dot" id="theory-status"></span>
                        <span>Music Theory</span>
                    </div>
                </div>
                
                <!-- Audio Processing Demo -->
                <div class="demo-panel" id="audio-demo">
                    <h3>🎧 Audio Processing</h3>
                    <div class="control-group">
                        <input type="file" id="audio-file" accept="audio/*" />
                        <select id="processing-type">
                            <option value="source_separation">Source Separation</option>
                            <option value="harmony_analysis">Harmony Analysis</option>
                            <option value="noise_reduction">Noise Reduction</option>
                        </select>
                        <button id="start-processing" class="btn-primary">Start Processing</button>
                        <button id="cancel-processing" class="btn-secondary" disabled>Cancel</button>
                    </div>
                    
                    <!-- Progress Display -->
                    <div class="progress-container" id="progress-container" style="display: none;">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                        <div class="progress-text" id="progress-text">Initializing...</div>
                        <div class="progress-percentage" id="progress-percentage">0%</div>
                    </div>
                    
                    <!-- Results Display -->
                    <div class="results-container" id="audio-results" style="display: none;">
                        <h4>Processing Results</h4>
                        <pre id="audio-results-json"></pre>
                    </div>
                </div>
                
                <!-- Music Theory Demo -->
                <div class="demo-panel" id="theory-demo">
                    <h3>🎼 Music Theory Tools</h3>
                    
                    <!-- Chord Analysis -->
                    <div class="theory-section">
                        <h4>Chord Analysis</h4>
                        <div class="control-group">
                            <input type="text" id="chord-notes" placeholder="Enter notes (e.g., C,E,G)" />
                            <button id="analyze-chord" class="btn-primary">Analyze Chord</button>
                        </div>
                        <div id="chord-result" class="result-display"></div>
                    </div>
                    
                    <!-- Scale Generation -->
                    <div class="theory-section">
                        <h4>Scale Generation</h4>
                        <div class="control-group">
                            <select id="scale-root">
                                <option value="C">C</option>
                                <option value="D">D</option>
                                <option value="E">E</option>
                                <option value="F">F</option>
                                <option value="G">G</option>
                                <option value="A">A</option>
                                <option value="B">B</option>
                            </select>
                            <select id="scale-type">
                                <option value="major">Major</option>
                                <option value="minor">Natural Minor</option>
                                <option value="dorian">Dorian</option>
                                <option value="phrygian">Phrygian</option>
                                <option value="lydian">Lydian</option>
                                <option value="mixolydian">Mixolydian</option>
                                <option value="locrian">Locrian</option>
                            </select>
                            <button id="generate-scale" class="btn-primary">Generate Scale</button>
                        </div>
                        <div id="scale-result" class="result-display"></div>
                    </div>
                    
                    <!-- Chord Substitutions -->
                    <div class="theory-section">
                        <h4>Chord Substitutions</h4>
                        <div class="control-group">
                            <input type="text" id="sub-chord" placeholder="Enter chord (e.g., Cmaj7)" />
                            <select id="instrument">
                                <option value="guitar">Guitar</option>
                                <option value="piano">Piano</option>
                                <option value="ukulele">Ukulele</option>
                            </select>
                            <button id="get-substitutions" class="btn-primary">Get Substitutions</button>
                        </div>
                        <div id="substitutions-result" class="result-display"></div>
                    </div>
                    
                    <!-- Practice Exercise -->
                    <div class="theory-section">
                        <h4>Practice Exercise</h4>
                        <div class="control-group">
                            <select id="exercise-type">
                                <option value="chord_recognition">Chord Recognition</option>
                                <option value="scale_practice">Scale Practice</option>
                            </select>
                            <button id="generate-exercise" class="btn-primary">Generate Exercise</button>
                        </div>
                        <div id="exercise-result" class="result-display"></div>
                    </div>
                    
                    <!-- Chord Progression -->
                    <div class="theory-section">
                        <h4>Chord Progression Generator</h4>
                        <div class="control-group">
                            <select id="prog-key">
                                <option value="C">C</option>
                                <option value="G">G</option>
                                <option value="D">D</option>
                                <option value="A">A</option>
                                <option value="E">E</option>
                                <option value="F">F</option>
                            </select>
                            <select id="prog-mode">
                                <option value="major">Major</option>
                                <option value="minor">Minor</option>
                            </select>
                            <button id="generate-progression" class="btn-primary">Generate Progression</button>
                        </div>
                        <div id="progression-result" class="result-display"></div>
                    </div>
                </div>
                
                <!-- Status Log -->
                <div class="demo-panel" id="status-log">
                    <h3>📝 Status Log</h3>
                    <div class="log-container" id="log-container">
                        <div class="log-entry">Demo interface ready</div>
                    </div>
                    <button id="clear-log" class="btn-secondary">Clear Log</button>
                </div>
            </div>
        `;
        
        // Add CSS styles
        const style = document.createElement('style');
        style.textContent = `
            .demo-container {
                max-width: 1200px;
                margin: 20px auto;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            }
            
            .connection-status {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            
            .status-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .status-dot {
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #dc3545;
                transition: background-color 0.3s;
            }
            
            .status-dot.connected {
                background: #28a745;
            }
            
            .demo-panel {
                margin-bottom: 30px;
                padding: 20px;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background: white;
            }
            
            .theory-section {
                margin-bottom: 20px;
                padding: 15px;
                border-left: 4px solid #667eea;
                background: #f8f9ff;
            }
            
            .control-group {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
                flex-wrap: wrap;
                align-items: center;
            }
            
            .control-group input,
            .control-group select {
                padding: 8px 12px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 120px;
            }
            
            .btn-primary {
                background: #667eea;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            
            .btn-primary:hover:not(:disabled) {
                background: #5a67d8;
            }
            
            .btn-primary:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            
            .btn-secondary {
                background: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
            }
            
            .btn-secondary:hover:not(:disabled) {
                background: #5a6268;
            }
            
            .progress-container {
                margin: 20px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            
            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e9ecef;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 10px;
            }
            
            .progress-fill {
                height: 100%;
                background: #667eea;
                transition: width 0.3s ease;
                width: 0%;
            }
            
            .progress-text {
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;
            }
            
            .progress-percentage {
                font-weight: bold;
                color: #333;
            }
            
            .result-display {
                margin-top: 10px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
                min-height: 50px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                white-space: pre-wrap;
            }
            
            .results-container {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 6px;
            }
            
            .results-container pre {
                background: white;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                font-size: 12px;
            }
            
            .log-container {
                max-height: 300px;
                overflow-y: auto;
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 10px;
                margin-bottom: 10px;
            }
            
            .log-entry {
                padding: 5px 0;
                border-bottom: 1px solid #eee;
                font-size: 14px;
                font-family: 'Courier New', monospace;
            }
            
            .log-entry:last-child {
                border-bottom: none;
            }
            
            .log-entry.success {
                color: #28a745;
            }
            
            .log-entry.error {
                color: #dc3545;
            }
            
            .log-entry.info {
                color: #17a2b8;
            }
        `;
        
        document.head.appendChild(style);
        
        // Insert demo interface after any existing content
        document.body.appendChild(demoContainer);
        
        // Store references
        this.progressBar = document.getElementById('progress-fill');
        this.statusDisplay = document.getElementById('progress-text');
    }
    
    setupEventListeners() {
        // Audio processing controls
        document.getElementById('start-processing').addEventListener('click', () => {
            this.startAudioProcessing();
        });
        
        document.getElementById('cancel-processing').addEventListener('click', () => {
            this.cancelAudioProcessing();
        });
        
        // Music theory controls
        document.getElementById('analyze-chord').addEventListener('click', () => {
            this.analyzeChord();
        });
        
        document.getElementById('generate-scale').addEventListener('click', () => {
            this.generateScale();
        });
        
        document.getElementById('get-substitutions').addEventListener('click', () => {
            this.getSubstitutions();
        });
        
        document.getElementById('generate-exercise').addEventListener('click', () => {
            this.generateExercise();
        });
        
        document.getElementById('generate-progression').addEventListener('click', () => {
            this.generateProgression();
        });
        
        // Clear log
        document.getElementById('clear-log').addEventListener('click', () => {
            document.getElementById('log-container').innerHTML = '';
        });
    }
    
    setupWebSocketHandlers() {
        // Audio processing handlers
        this.wsManager.on('audio', 'connected', (data) => {
            this.updateConnectionStatus('audio', true);
            this.addLogEntry('✅ Audio processing connected', 'success');
        });
        
        this.wsManager.on('audio', 'disconnected', (data) => {
            this.updateConnectionStatus('audio', false);
            this.addLogEntry('❌ Audio processing disconnected', 'error');
        });
        
        this.wsManager.on('audio', 'processing_started', (data) => {
            this.addLogEntry(`🎵 Started ${data.processing_type} processing`, 'info');
            this.showProgress();
            this.setProcessingState(true);
        });
        
        this.wsManager.on('audio', 'progress', (data) => {
            this.updateProgress(data.percentage, data.message);
        });
        
        this.wsManager.on('audio', 'complete', (data) => {
            this.addLogEntry('✅ Audio processing completed', 'success');
            this.hideProgress();
            this.setProcessingState(false);
            this.showResults(data);
        });
        
        this.wsManager.on('audio', 'error', (data) => {
            this.addLogEntry(`🚨 Audio processing error: ${data.message}`, 'error');
            this.hideProgress();
            this.setProcessingState(false);
        });
        
        // Music theory handlers
        this.wsManager.on('theory', 'connected', (data) => {
            this.updateConnectionStatus('theory', true);
            this.addLogEntry('✅ Music theory connected', 'success');
        });
        
        this.wsManager.on('theory', 'disconnected', (data) => {
            this.updateConnectionStatus('theory', false);
            this.addLogEntry('❌ Music theory disconnected', 'error');
        });
        
        this.wsManager.on('theory', 'chord_analysis', (data) => {
            this.displayChordResult(data);
        });
        
        this.wsManager.on('theory', 'scale_generated', (data) => {
            this.displayScaleResult(data);
        });
        
        this.wsManager.on('theory', 'substitutions', (data) => {
            this.displaySubstitutionsResult(data);
        });
        
        this.wsManager.on('theory', 'exercise', (data) => {
            this.displayExerciseResult(data);
        });
        
        this.wsManager.on('theory', 'progression', (data) => {
            this.displayProgressionResult(data);
        });
        
        this.wsManager.on('theory', 'error', (data) => {
            this.addLogEntry(`🚨 Music theory error: ${data.message}`, 'error');
        });
    }
    
    // Audio Processing Methods
    startAudioProcessing() {
        const fileInput = document.getElementById('audio-file');
        const processingType = document.getElementById('processing-type').value;
        
        if (!fileInput.files.length) {
            alert('Please select an audio file');
            return;
        }
        
        // For demo purposes, we'll use a mock file path
        const mockFilePath = '/path/to/uploaded/' + fileInput.files[0].name;
        
        const success = this.wsManager.startAudioProcessing(processingType, mockFilePath, {
            method: processingType === 'source_separation' ? 'demucs' : 'default'
        });
        
        if (!success) {
            alert('WebSocket not connected. Please refresh the page.');
        }
    }
    
    cancelAudioProcessing() {
        this.wsManager.cancelAudioProcessing();
        this.hideProgress();
        this.setProcessingState(false);
        this.addLogEntry('⏹️ Processing cancelled', 'info');
    }
    
    // Music Theory Methods
    analyzeChord() {
        const notesInput = document.getElementById('chord-notes').value;
        if (!notesInput.trim()) {
            alert('Please enter chord notes (e.g., C,E,G)');
            return;
        }
        
        const notes = notesInput.split(',').map(note => note.trim());
        this.wsManager.analyzeChord(notes);
    }
    
    generateScale() {
        const root = document.getElementById('scale-root').value;
        const scaleType = document.getElementById('scale-type').value;
        this.wsManager.generateScale(root, scaleType);
    }
    
    getSubstitutions() {
        const chord = document.getElementById('sub-chord').value;
        const instrument = document.getElementById('instrument').value;
        
        if (!chord.trim()) {
            alert('Please enter a chord (e.g., Cmaj7)');
            return;
        }
        
        this.wsManager.getChordSubstitutions(chord, instrument, 5);
    }
    
    generateExercise() {
        const exerciseType = document.getElementById('exercise-type').value;
        this.wsManager.generatePracticeExercise(exerciseType, 1);
    }
    
    generateProgression() {
        const key = document.getElementById('prog-key').value;
        const mode = document.getElementById('prog-mode').value;
        this.wsManager.generateChordProgression(key, mode, 4);
    }
    
    // UI Update Methods
    updateConnectionStatus(type, connected) {
        const statusDot = document.getElementById(`${type}-status`);
        if (connected) {
            statusDot.classList.add('connected');
        } else {
            statusDot.classList.remove('connected');
        }
    }
    
    showProgress() {
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('audio-results').style.display = 'none';
    }
    
    hideProgress() {
        document.getElementById('progress-container').style.display = 'none';
    }
    
    updateProgress(percentage, message) {
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        if (this.statusDisplay) {
            this.statusDisplay.textContent = message;
        }
        document.getElementById('progress-percentage').textContent = `${percentage}%`;
    }
    
    setProcessingState(processing) {
        document.getElementById('start-processing').disabled = processing;
        document.getElementById('cancel-processing').disabled = !processing;
    }
    
    showResults(data) {
        document.getElementById('audio-results').style.display = 'block';
        document.getElementById('audio-results-json').textContent = JSON.stringify(data, null, 2);
    }
    
    displayChordResult(data) {
        const result = document.getElementById('chord-result');
        result.textContent = `Chord: ${data.chord} (${(data.confidence * 100).toFixed(1)}% confidence)\\nQuality: ${data.quality}\\nDifficulty: ${data.difficulty}/10`;
        this.addLogEntry(`🎼 Analyzed chord: ${data.chord}`, 'success');
    }
    
    displayScaleResult(data) {
        const result = document.getElementById('scale-result');
        result.textContent = `${data.root} ${data.scale_type}: ${data.scale_info.notes.join(', ')}\\nDifficulty: ${data.scale_info.difficulty}/10`;
        this.addLogEntry(`🎵 Generated ${data.root} ${data.scale_type} scale`, 'success');
    }
    
    displaySubstitutionsResult(data) {
        const result = document.getElementById('substitutions-result');
        const subs = data.substitutions.map(sub => `${sub.chord} (${sub.type})`).join('\\n');
        result.textContent = `Substitutions for ${data.original_chord}:\\n${subs}`;
        this.addLogEntry(`🔄 Found ${data.substitutions.length} substitutions`, 'success');
    }
    
    displayExerciseResult(data) {
        const result = document.getElementById('exercise-result');
        result.textContent = `Exercise: ${data.exercise.question}\\nAnswer: ${data.exercise.answer}\\nDifficulty: ${data.exercise.difficulty}/10`;
        this.addLogEntry(`📚 Generated ${data.exercise.type} exercise`, 'success');
    }
    
    displayProgressionResult(data) {
        const result = document.getElementById('progression-result');
        result.textContent = `${data.key} ${data.mode} progression:\\nRoman: ${data.roman_numerals.join(' - ')}\\nChords: ${data.chords.join(' - ')}`;
        this.addLogEntry(`🎶 Generated progression in ${data.key} ${data.mode}`, 'success');
    }
    
    addLogEntry(message, type = 'info') {
        const logContainer = document.getElementById('log-container');
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        logContainer.appendChild(entry);
        logContainer.scrollTop = logContainer.scrollHeight;
    }
}

// Initialize demo when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for WebSocket manager to initialize
    setTimeout(() => {
        window.realTimeDemo = new RealTimeDemo();
    }, 1000);
});

console.log('🎵 Real-time demo interface loaded');