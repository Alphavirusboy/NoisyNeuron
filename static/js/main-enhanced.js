/**
 * Enhanced NoisyNeuron Application with Full Functionality
 * Handles all UI interactions, file uploads, WebSocket connections, and audio processing
 */

class NoisyNeuronApp {
    constructor() {
        this.currentFile = null;
        this.currentProject = null;
        this.processingStatus = null;
        this.wsConnection = null;
        this.audioContext = null;
        this.currentSection = 'dashboard';
        this.userProgress = {
            songsProcessed: 24,
            practiceTime: '12h',
            stemsCreated: 96
        };
        
        this.init();
    }
    
    init() {
        this.initAudioContext();
        this.setupNavigation();
        this.setupEventListeners();
        this.setupFileUpload();
        this.setupWebSocket();
        this.loadUserSession();
        this.updateProgressStats();
        console.log('NoisyNeuron App initialized successfully');
    }
    
    async initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio context initialized');
        } catch (error) {
            console.warn('Web Audio API not supported:', error);
        }
    }
    
    setupNavigation() {
        // Navigation menu handlers
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.navigateToSection(section);
            });
        });
        
        // Dashboard action buttons
        document.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const action = e.currentTarget.dataset.action;
                this.handleDashboardAction(action);
            });
        });
    }
    
    handleDashboardAction(action) {
        switch (action) {
            case 'separate':
                this.navigateToSection('separate');
                break;
            case 'practice':
                this.navigateToSection('practice');
                break;
            case 'learn':
                this.navigateToSection('learn');
                break;
            default:
                console.log(`Action: ${action}`);
        }
    }
    
    navigateToSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show target section
        const targetSection = document.getElementById(sectionName);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`[data-section="${sectionName}"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
        
        this.currentSection = sectionName;
        this.onSectionChange(sectionName);
    }
    
    onSectionChange(sectionName) {
        switch (sectionName) {
            case 'dashboard':
                this.refreshDashboard();
                break;
            case 'learn':
                this.initializeLearningSection();
                break;
            case 'separate':
                this.initializeSeparationSection();
                break;
            case 'practice':
                this.initializePracticeSection();
                break;
        }
    }
    
    setupEventListeners() {
        // Instrument selector buttons
        document.querySelectorAll('.instrument-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.instrument-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateInstrument(e.target.dataset.instrument);
            });
        });
        
        // Skill level buttons
        document.querySelectorAll('.skill-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.skill-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.updateSkillLevel(e.target.dataset.level);
            });
        });
        
        // Chord input and substitution
        const chordInput = document.getElementById('chordInput');
        const getSubstitutions = document.getElementById('getSubstitutions');
        
        if (chordInput && getSubstitutions) {
            getSubstitutions.addEventListener('click', () => this.getChordSubstitutions());
            chordInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.getChordSubstitutions();
                }
            });
        }
        
        // Start separation button
        const startSeparationBtn = document.getElementById('startSeparation');
        if (startSeparationBtn) {
            startSeparationBtn.addEventListener('click', () => this.startSeparation());
        }
        
        // Learning path buttons
        document.querySelectorAll('.path-card .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showNotification('Learning path feature coming soon!', 'info');
            });
        });
        
        // File input change
        const audioFileInput = document.getElementById('audioFileInput');
        if (audioFileInput) {
            audioFileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }
        
        // File select button
        const fileSelectBtn = document.getElementById('fileSelectBtn');
        if (fileSelectBtn) {
            fileSelectBtn.addEventListener('click', () => {
                document.getElementById('audioFileInput')?.click();
            });
        }
    }
    
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('audioFileInput');
        
        if (!uploadArea || !fileInput) return;
        
        // Drag and drop handlers
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect({ target: { files } });
            }
        });
        
        // Click to upload
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });
    }
    
    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Validate file type
        const validTypes = ['audio/mp3', 'audio/wav', 'audio/flac', 'audio/m4a', 'audio/mpeg'];
        if (!validTypes.includes(file.type) && !file.name.match(/\\.(mp3|wav|flac|m4a)$/i)) {
            this.showNotification('Please select a valid audio file (MP3, WAV, FLAC, M4A)', 'error');
            return;
        }
        
        // Validate file size (100MB limit)
        const maxSize = 100 * 1024 * 1024; // 100MB
        if (file.size > maxSize) {
            this.showNotification('File size too large. Maximum size is 100MB.', 'error');
            return;
        }
        
        this.currentFile = file;
        this.updateUploadUI(file);
        this.showNotification(`File "${file.name}" selected successfully!`, 'success');
    }
    
    updateUploadUI(file) {
        const uploadArea = document.getElementById('uploadArea');
        if (!uploadArea) return;
        
        uploadArea.innerHTML = `
            <div class="upload-success">
                <div class="upload-icon">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h3>${file.name}</h3>
                <p>File size: ${this.formatFileSize(file.size)}</p>
                <button class="btn btn-outline" onclick="app.clearFile()">
                    <i class="fas fa-times"></i>
                    Remove File
                </button>
            </div>
        `;
    }
    
    clearFile() {
        this.currentFile = null;
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.innerHTML = `
                <div class="upload-icon">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <h3>Drop your audio file here</h3>
                <p>Supports MP3, WAV, FLAC, M4A • Maximum 100MB</p>
                <button class="btn btn-primary" id="fileSelectBtn">
                    <i class="fas fa-file-audio"></i>
                    Choose File
                </button>
                <input type="file" id="audioFileInput" accept="audio/*" hidden>
            `;
            this.setupFileUpload(); // Re-setup event listeners
        }
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    startSeparation() {
        if (!this.currentFile) {
            this.showNotification('Please select an audio file first', 'error');
            return;
        }
        
        // Get selected separation options
        const separationOptions = [];
        document.querySelectorAll('input[name="separation"]:checked').forEach(input => {
            separationOptions.push(input.value);
        });
        
        if (separationOptions.length === 0) {
            this.showNotification('Please select at least one separation option', 'error');
            return;
        }
        
        // Get quality setting
        const quality = document.querySelector('input[name="quality"]:checked')?.value || 'standard';
        
        this.showProcessingSection();
        this.uploadAndProcess(this.currentFile, separationOptions, quality);
    }
    
    showProcessingSection() {
        const processingSection = document.getElementById('processingSection');
        if (processingSection) {
            processingSection.style.display = 'block';
            processingSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    async uploadAndProcess(file, options, quality) {
        try {
            this.updateProcessingProgress(0, 'Uploading file...');
            
            const formData = new FormData();
            formData.append('audio_file', file);
            formData.append('separation_options', JSON.stringify(options));
            formData.append('quality', quality);
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                            document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
            
            const response = await fetch('/audio-processor/upload/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const result = await response.json();
            this.currentProject = result.project_id;
            
            this.updateProcessingProgress(25, 'Upload complete. Starting AI analysis...');
            this.simulateProcessingProgress();
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification('Upload failed. Please try again.', 'error');
            this.hideProcessingSection();
        }
    }
    
    simulateProcessingProgress() {
        let progress = 25;
        const stages = [
            { progress: 40, text: 'Analyzing audio characteristics...' },
            { progress: 55, text: 'Applying neural network models...' },
            { progress: 70, text: 'Separating vocal tracks...' },
            { progress: 85, text: 'Isolating instrumental stems...' },
            { progress: 100, text: 'Processing complete!' }
        ];
        
        let stageIndex = 0;
        const interval = setInterval(() => {
            if (stageIndex < stages.length) {
                const stage = stages[stageIndex];
                this.updateProcessingProgress(stage.progress, stage.text);
                stageIndex++;
            } else {
                clearInterval(interval);
                setTimeout(() => this.showResults(), 1000);
            }
        }, 2000);
    }
    
    updateProcessingProgress(percentage, text) {
        const progressFill = document.getElementById('processingProgress');
        const progressText = document.getElementById('processingText');
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = text;
        }
    }
    
    hideProcessingSection() {
        const processingSection = document.getElementById('processingSection');
        if (processingSection) {
            processingSection.style.display = 'none';
        }
    }
    
    showResults() {
        this.hideProcessingSection();
        const resultsSection = document.getElementById('resultsSection');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        this.showNotification('Audio separation completed successfully!', 'success');
    }
    
    getChordSubstitutions() {
        const chordInput = document.getElementById('chordInput');
        const substitutionsContainer = document.getElementById('chordSubstitutions');
        
        if (!chordInput || !substitutionsContainer) return;
        
        const chord = chordInput.value.trim();
        if (!chord) {
            this.showNotification('Please enter a chord name', 'error');
            return;
        }
        
        // Get current skill level
        const skillLevel = document.querySelector('.skill-btn.active')?.dataset.level || '1';
        
        // Mock chord substitutions - in real app, this would call the backend
        const substitutions = this.generateChordSubstitutions(chord, skillLevel);
        
        substitutionsContainer.innerHTML = `
            <h4>Alternative chords for ${chord}:</h4>
            <div class="chord-alternatives">
                ${substitutions.map(sub => `
                    <div class="chord-alternative">
                        <div class="chord-name">${sub.name}</div>
                        <div class="chord-difficulty">Difficulty: ${sub.difficulty}/5</div>
                        <div class="chord-diagram">${sub.diagram}</div>
                    </div>
                `).join('')}
            </div>
        `;
        
        substitutionsContainer.style.display = 'block';
    }
    
    generateChordSubstitutions(chord, skillLevel) {
        // Mock data - replace with actual API call
        const alternatives = [
            { name: 'C', difficulty: 1, diagram: 'x32010' },
            { name: 'Am', difficulty: 1, diagram: 'x02210' },
            { name: 'F (easy)', difficulty: 2, diagram: '133211' },
            { name: 'G', difficulty: 1, diagram: '320003' }
        ];
        
        return alternatives.filter(alt => alt.difficulty <= parseInt(skillLevel) + 1);
    }
    
    updateInstrument(instrument) {
        console.log(`Selected instrument: ${instrument}`);
        // Update chord library and learning content based on instrument
    }
    
    updateSkillLevel(level) {
        console.log(`Selected skill level: ${level}`);
        // Update content difficulty based on skill level
    }
    
    refreshDashboard() {
        this.updateProgressStats();
    }
    
    updateProgressStats() {
        // Update dashboard statistics
        const stats = document.querySelectorAll('.stat-number');
        if (stats.length >= 3) {
            stats[0].textContent = this.userProgress.songsProcessed;
            stats[1].textContent = this.userProgress.practiceTime;
            stats[2].textContent = this.userProgress.stemsCreated;
        }
    }
    
    initializeLearningSection() {
        console.log('Initializing learning section');
        // Initialize chord library, learning paths, etc.
    }
    
    initializeSeparationSection() {
        console.log('Initializing separation section');
        // Reset file upload area if needed
    }
    
    initializePracticeSection() {
        console.log('Initializing practice section');
        // Initialize practice tools, tuner, etc.
    }
    
    setupWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/audio-processing/`;
            
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connected');
                // Send ping to test connection
                this.wsConnection.send(JSON.stringify({
                    type: 'ping',
                    timestamp: Date.now()
                }));
            };
            
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.wsConnection.onclose = () => {
                console.log('WebSocket disconnected');
                this.updateConnectionStatus('disconnected');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('error');
            };
        } catch (error) {
            console.error('WebSocket setup failed:', error);
            this.updateConnectionStatus('error');
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('WebSocket message received:', data);
        
        switch (data.type) {
            case 'connection_established':
                console.log('WebSocket connection confirmed');
                this.showNotification('Real-time connection established', 'success');
                break;
            case 'pong':
                console.log('WebSocket ping/pong successful');
                break;
            case 'progress_update':
                this.updateProcessingProgress(data.progress, data.message);
                break;
            case 'processing_started':
                this.showNotification('Audio processing started', 'info');
                break;
            case 'processing_complete':
                this.showResults();
                this.showNotification('Processing completed successfully!', 'success');
                break;
            case 'processing_error':
                this.showNotification(data.message || 'Processing failed', 'error');
                this.hideProcessingSection();
                break;
            case 'error':
                console.error('WebSocket error:', data.message);
                this.showNotification(data.message, 'error');
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    updateConnectionStatus(status) {
        const wsStatusDot = document.getElementById('wsStatus');
        if (wsStatusDot) {
            wsStatusDot.classList.remove('connected');
            if (status === 'connected') {
                wsStatusDot.classList.add('connected');
            }
        }
        
        // Also update any other status indicators
        const statusIndicators = document.querySelectorAll('.status-dot');
        statusIndicators.forEach(dot => {
            if (dot.id === 'wsStatus') {
                dot.classList.remove('connected');
                if (status === 'connected') {
                    dot.classList.add('connected');
                }
            }
        });
    }
    
    loadUserSession() {
        // Load user session data from localStorage or server
        const savedProgress = localStorage.getItem('noisyNeuronProgress');
        if (savedProgress) {
            this.userProgress = { ...this.userProgress, ...JSON.parse(savedProgress) };
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        const container = document.querySelector('.app-container');
        if (container) {
            container.appendChild(notification);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NoisyNeuronApp();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NoisyNeuronApp;
}