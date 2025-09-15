/**
 * NoisyNeuron - Modern Application Core
 * Professional music learning platform JavaScript
 */

class NoisyNeuronApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.isProcessing = false;
        this.websocket = null;
        this.audioContext = null;
        this.theme = localStorage.getItem('theme') || 'light';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.initializeWebSocket();
        this.setupTheme();
        this.setupAudioContext();
        this.startStatusUpdates();
        
        console.log('🎵 NoisyNeuron App Initialized');
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const section = e.currentTarget.dataset.section;
                this.navigateToSection(section);
            });
        });
        
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }
        
        // Action buttons
        document.addEventListener('click', (e) => {
            const actionBtn = e.target.closest('[data-action]');
            if (actionBtn) {
                const action = actionBtn.dataset.action;
                this.handleAction(action, actionBtn);
            }
        });
        
        // File upload
        const fileInput = document.getElementById('audio-upload');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileUpload(e.target.files[0]);
            });
        }
        
        // Drag and drop
        this.setupDragAndDrop();
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }
    
    navigateToSection(sectionName) {
        // Update nav links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');
        
        // Show/hide sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('hidden');
        });
        
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            targetSection.classList.add('animate-fade-in');
            
            // Remove animation class after completion
            setTimeout(() => {
                targetSection.classList.remove('animate-fade-in');
            }, 500);
        }
        
        this.currentSection = sectionName;
        
        // Analytics
        this.trackEvent('navigation', { section: sectionName });
    }
    
    handleAction(action, button) {
        console.log(`🎯 Action triggered: ${action}`);
        
        switch (action) {
            case 'separate':
                this.navigateToSection('separate');
                break;
            case 'practice':
                this.navigateToSection('practice');
                break;
            case 'theory':
                this.navigateToSection('theory');
                break;
            case 'library':
                this.navigateToSection('library');
                break;
            case 'chord-practice':
                this.startChordPractice();
                break;
            case 'rhythm-training':
                this.startRhythmTraining();
                break;
            case 'ear-training':
                this.startEarTraining();
                break;
            case 'learn-fundamentals':
                this.showFundamentals();
                break;
            case 'study-harmony':
                this.showHarmony();
                break;
            case 'analyze-music':
                this.showMusicAnalysis();
                break;
            default:
                console.warn(`Unknown action: ${action}`);
        }
        
        // Add click animation
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = '';
        }, 150);
    }
    
    setupTheme() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this.updateThemeIcon();
    }
    
    toggleTheme() {
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', this.theme);
        document.documentElement.setAttribute('data-theme', this.theme);
        this.updateThemeIcon();
        
        // Animate theme transition
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
    
    updateThemeIcon() {
        const themeIcon = document.querySelector('#theme-toggle i');
        if (themeIcon) {
            themeIcon.className = this.theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
        }
    }
    
    setupDragAndDrop() {
        const dropZone = document.querySelector('.border-dashed');
        if (!dropZone) return;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-primary-500', 'bg-primary-50');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-primary-500', 'bg-primary-50');
            }, false);
        });
        
        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        }, false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    async handleFileUpload(file) {
        if (!file) return;
        
        // Validate file
        if (!this.validateAudioFile(file)) {
            this.showNotification('Please select a valid audio file (MP3, WAV, FLAC, M4A)', 'error');
            return;
        }
        
        if (file.size > 100 * 1024 * 1024) { // 100MB
            this.showNotification('File size must be less than 100MB', 'error');
            return;
        }
        
        console.log(`📁 File selected: ${file.name} (${this.formatFileSize(file.size)})`);
        
        // Show loading
        this.showLoading('Processing audio file...');
        
        try {
            // Create FormData
            const formData = new FormData();
            formData.append('audio_file', file);
            formData.append('quality', 'balanced');
            formData.append('stems', JSON.stringify(['vocals', 'drums', 'bass', 'other']));
            
            // Get CSRF token
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            // Upload and process
            const response = await fetch('/api/audio/upload/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('✅ Upload successful:', result);
            
            this.showNotification('Audio file uploaded successfully! Processing will begin shortly.', 'success');
            
            // Start monitoring processing
            this.monitorProcessing(result.project_id);
            
        } catch (error) {
            console.error('❌ Upload failed:', error);
            this.showNotification('Failed to upload file. Please try again.', 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    validateAudioFile(file) {
        const validTypes = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave',
            'audio/flac', 'audio/m4a', 'audio/mp4', 'audio/aac'
        ];
        
        const validExtensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac'];
        
        return validTypes.includes(file.type) || 
               validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/audio-processing/`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.updateConnectionStatus('wsStatus', 'connected');
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.updateConnectionStatus('wsStatus', 'disconnected');
                
                // Reconnect after 3 seconds
                setTimeout(() => {
                    this.initializeWebSocket();
                }, 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('🔌 WebSocket error:', error);
                this.updateConnectionStatus('wsStatus', 'disconnected');
            };
            
        } catch (error) {
            console.error('🔌 Failed to initialize WebSocket:', error);
            this.updateConnectionStatus('wsStatus', 'disconnected');
        }
    }
    
    handleWebSocketMessage(data) {
        console.log('📨 WebSocket message:', data);
        
        switch (data.type) {
            case 'processing_progress':
                this.updateProcessingProgress(data.progress, data.stage);
                break;
            case 'processing_complete':
                this.handleProcessingComplete(data);
                break;
            case 'processing_error':
                this.handleProcessingError(data);
                break;
            case 'notification':
                this.showNotification(data.message, data.level || 'info');
                break;
        }
    }
    
    updateConnectionStatus(elementId, status) {
        const statusDot = document.getElementById(elementId);
        if (statusDot) {
            statusDot.className = `status-dot ${status}`;
        }
    }
    
    startStatusUpdates() {
        // Update server status
        this.updateConnectionStatus('serverStatus', 'connected');
        
        // Check server health periodically
        setInterval(async () => {
            try {
                const response = await fetch('/api/health/', { method: 'GET' });
                this.updateConnectionStatus('serverStatus', response.ok ? 'connected' : 'disconnected');
            } catch {
                this.updateConnectionStatus('serverStatus', 'disconnected');
            }
        }, 30000); // Check every 30 seconds
    }
    
    setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🔊 Audio context initialized');
        } catch (error) {
            console.warn('🔊 Audio context not available:', error);
        }
    }
    
    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + 1-5 for navigation
        if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '5') {
            e.preventDefault();
            const sections = ['dashboard', 'separate', 'practice', 'theory', 'library'];
            const index = parseInt(e.key) - 1;
            if (sections[index]) {
                this.navigateToSection(sections[index]);
            }
        }
        
        // Space bar for play/pause (when in practice mode)
        if (e.code === 'Space' && this.currentSection === 'practice') {
            e.preventDefault();
            // TODO: Implement play/pause functionality
        }
        
        // Escape to close modals
        if (e.key === 'Escape') {
            this.hideLoading();
            // TODO: Close any open modals
        }
    }
    
    showLoading(message = 'Loading...') {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.querySelector('h3').textContent = message;
            overlay.classList.remove('hidden');
            overlay.classList.add('flex');
        }
    }
    
    hideLoading() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.classList.add('hidden');
            overlay.classList.remove('flex');
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-toast p-4 rounded-lg shadow-lg max-w-sm transition-all duration-300 transform translate-x-full`;
        
        // Set type-specific styles
        const typeStyles = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        
        notification.className += ` ${typeStyles[type] || typeStyles.info}`;
        
        // Set content
        notification.innerHTML = `
            <div class="flex items-center gap-3">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
                <button class="ml-auto" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    }
    
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || icons.info;
    }
    
    monitorProcessing(projectId) {
        // This would be implemented to track processing progress
        console.log(`📊 Monitoring processing for project: ${projectId}`);
        
        // Send WebSocket message to start monitoring
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            this.websocket.send(JSON.stringify({
                type: 'monitor_processing',
                project_id: projectId
            }));
        }
    }
    
    updateProcessingProgress(progress, stage) {
        console.log(`📊 Processing progress: ${progress}% - ${stage}`);
        // TODO: Update UI with progress
    }
    
    handleProcessingComplete(data) {
        console.log('✅ Processing complete:', data);
        this.showNotification('Audio separation completed successfully!', 'success');
        // TODO: Update UI with results
    }
    
    handleProcessingError(data) {
        console.error('❌ Processing error:', data);
        this.showNotification(`Processing failed: ${data.error}`, 'error');
    }
    
    // Practice Tool Methods
    startChordPractice() {
        console.log('🎸 Starting Chord Practice');
        this.navigateToSection('practice');
        this.showModal('Chord Practice', this.getChordPracticeContent());
        this.trackEvent('practice_tool', { type: 'chord-practice' });
    }
    
    startRhythmTraining() {
        console.log('🥁 Starting Rhythm Training');
        this.navigateToSection('practice');
        this.showModal('Rhythm Training', this.getRhythmTrainingContent());
        this.trackEvent('practice_tool', { type: 'rhythm-training' });
    }
    
    startEarTraining() {
        console.log('👂 Starting Ear Training');
        this.navigateToSection('practice');
        this.showModal('Ear Training', this.getEarTrainingContent());
        this.trackEvent('practice_tool', { type: 'ear-training' });
    }
    
    showFundamentals() {
        console.log('📚 Showing Music Fundamentals');
        this.navigateToSection('theory');
        this.showModal('Music Fundamentals', this.getFundamentalsContent());
        this.trackEvent('theory_tool', { type: 'fundamentals' });
    }
    
    showHarmony() {
        console.log('🎼 Showing Harmony Studies');
        this.navigateToSection('theory');
        this.showModal('Harmony Studies', this.getHarmonyContent());
        this.trackEvent('theory_tool', { type: 'harmony' });
    }
    
    showMusicAnalysis() {
        console.log('🔍 Starting Music Analysis');
        this.navigateToSection('theory');
        this.showModal('Music Analysis', this.getMusicAnalysisContent());
        this.trackEvent('theory_tool', { type: 'analysis' });
    }
    
    // Modal functionality
    showModal(title, content) {
        // Remove existing modal if any
        const existingModal = document.querySelector('.practice-modal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Create modal
        const modal = document.createElement('div');
        modal.className = 'practice-modal fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl max-h-96 overflow-y-auto m-4">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-xl font-bold">${title}</h2>
                    <button class="close-modal text-gray-500 hover:text-gray-700 text-xl">×</button>
                </div>
                <div class="modal-content">
                    ${content}
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add close functionality
        modal.querySelector('.close-modal').addEventListener('click', () => {
            modal.remove();
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    // Content generators for each practice tool
    getChordPracticeContent() {
        return `
            <div class="space-y-4">
                <p>Practice chord progressions and improve your chord recognition skills.</p>
                <div class="chord-practice-controls space-y-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">Key:</label>
                        <select class="w-full p-2 border rounded">
                            <option value="C">C Major</option>
                            <option value="G">G Major</option>
                            <option value="D">D Major</option>
                            <option value="A">A Major</option>
                            <option value="Am">A Minor</option>
                            <option value="Em">E Minor</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Progression:</label>
                        <select class="w-full p-2 border rounded">
                            <option value="I-V-vi-IV">I-V-vi-IV (Pop Progression)</option>
                            <option value="ii-V-I">ii-V-I (Jazz Standard)</option>
                            <option value="I-vi-ii-V">I-vi-ii-V (Circle Progression)</option>
                            <option value="vi-IV-I-V">vi-IV-I-V (Alternative Pop)</option>
                        </select>
                    </div>
                    <button class="btn btn-primary w-full">Start Practice Session</button>
                </div>
                <div id="chord-display" class="text-center p-4 bg-gray-100 dark:bg-gray-700 rounded">
                    <div class="text-2xl font-bold">Ready to Practice!</div>
                    <div class="text-sm text-gray-600 dark:text-gray-300">Select your settings and click start</div>
                </div>
            </div>
        `;
    }
    
    getRhythmTrainingContent() {
        return `
            <div class="space-y-4">
                <p>Improve your timing and rhythm with interactive exercises.</p>
                <div class="rhythm-controls space-y-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">Tempo (BPM):</label>
                        <input type="range" min="60" max="200" value="120" class="w-full" id="tempo-slider">
                        <div class="text-center">
                            <span id="tempo-display">120</span> BPM
                        </div>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Time Signature:</label>
                        <select class="w-full p-2 border rounded">
                            <option value="4/4">4/4</option>
                            <option value="3/4">3/4</option>
                            <option value="2/4">2/4</option>
                            <option value="6/8">6/8</option>
                        </select>
                    </div>
                    <div class="flex space-x-2">
                        <button class="btn btn-primary flex-1" id="start-metronome">Start Metronome</button>
                        <button class="btn btn-secondary flex-1" id="rhythm-exercise">Rhythm Exercise</button>
                    </div>
                </div>
                <div id="metronome-display" class="text-center p-4 bg-gray-100 dark:bg-gray-700 rounded">
                    <div class="text-6xl" id="beat-indicator">♩</div>
                    <div class="text-sm text-gray-600 dark:text-gray-300">Click start to begin</div>
                </div>
            </div>
        `;
    }
    
    getEarTrainingContent() {
        return `
            <div class="space-y-4">
                <p>Develop your musical ear with interval and chord recognition exercises.</p>
                <div class="ear-training-controls space-y-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">Exercise Type:</label>
                        <select class="w-full p-2 border rounded">
                            <option value="intervals">Interval Recognition</option>
                            <option value="chords">Chord Recognition</option>
                            <option value="scales">Scale Recognition</option>
                            <option value="progressions">Chord Progressions</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Difficulty:</label>
                        <select class="w-full p-2 border rounded">
                            <option value="beginner">Beginner</option>
                            <option value="intermediate">Intermediate</option>
                            <option value="advanced">Advanced</option>
                        </select>
                    </div>
                    <button class="btn btn-primary w-full">Start Exercise</button>
                </div>
                <div id="ear-training-exercise" class="text-center p-4 bg-gray-100 dark:bg-gray-700 rounded">
                    <div class="text-xl font-bold mb-2">Ready for Ear Training!</div>
                    <div class="text-sm text-gray-600 dark:text-gray-300">Choose your exercise type and difficulty</div>
                    <div class="mt-4 space-x-2 hidden" id="exercise-controls">
                        <button class="btn btn-outline">🔊 Play Again</button>
                        <button class="btn btn-outline">📝 Show Answer</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    getFundamentalsContent() {
        return `
            <div class="space-y-4">
                <p>Learn the basic building blocks of music theory.</p>
                <div class="fundamentals-topics grid grid-cols-2 gap-3">
                    <button class="btn btn-outline text-left p-3" data-topic="notes">
                        <div class="font-semibold">Notes & Intervals</div>
                        <div class="text-xs text-gray-600">Musical alphabet, sharps, flats</div>
                    </button>
                    <button class="btn btn-outline text-left p-3" data-topic="scales">
                        <div class="font-semibold">Scales & Modes</div>
                        <div class="text-xs text-gray-600">Major, minor, modal scales</div>
                    </button>
                    <button class="btn btn-outline text-left p-3" data-topic="keys">
                        <div class="font-semibold">Key Signatures</div>
                        <div class="text-xs text-gray-600">Sharps, flats, relative keys</div>
                    </button>
                    <button class="btn btn-outline text-left p-3" data-topic="time">
                        <div class="font-semibold">Time Signatures</div>
                        <div class="text-xs text-gray-600">4/4, 3/4, compound time</div>
                    </button>
                </div>
                <div id="topic-content" class="p-4 bg-gray-100 dark:bg-gray-700 rounded">
                    <div class="text-center text-gray-600 dark:text-gray-300">
                        Select a topic above to start learning
                    </div>
                </div>
            </div>
        `;
    }
    
    getHarmonyContent() {
        return `
            <div class="space-y-4">
                <p>Explore chord construction, progressions, and harmonic relationships.</p>
                <div class="harmony-topics grid grid-cols-2 gap-3">
                    <button class="btn btn-outline text-left p-3" data-topic="chords">
                        <div class="font-semibold">Chord Construction</div>
                        <div class="text-xs text-gray-600">Triads, 7th chords, extensions</div>
                    </button>
                    <button class="btn btn-outline text-left p-3" data-topic="progressions">
                        <div class="font-semibold">Progressions</div>
                        <div class="text-xs text-gray-600">Common patterns, functions</div>
                    </button>
                    <button class="btn btn-outline text-left p-3" data-topic="voice-leading">
                        <div class="font-semibold">Voice Leading</div>
                        <div class="text-xs text-gray-600">Smooth voice movement</div>
                    </button>
                    <button class="btn btn-outline text-left p-3" data-topic="modulation">
                        <div class="font-semibold">Modulation</div>
                        <div class="text-xs text-gray-600">Key changes, pivot chords</div>
                    </button>
                </div>
                <div id="harmony-content" class="p-4 bg-gray-100 dark:bg-gray-700 rounded">
                    <div class="text-center text-gray-600 dark:text-gray-300">
                        Select a harmony topic to explore
                    </div>
                </div>
            </div>
        `;
    }
    
    getMusicAnalysisContent() {
        return `
            <div class="space-y-4">
                <p>Analyze musical pieces and understand compositional techniques.</p>
                <div class="analysis-tools space-y-3">
                    <div>
                        <label class="block text-sm font-medium mb-1">Analysis Type:</label>
                        <select class="w-full p-2 border rounded">
                            <option value="harmonic">Harmonic Analysis</option>
                            <option value="formal">Formal Analysis</option>
                            <option value="melodic">Melodic Analysis</option>
                            <option value="rhythmic">Rhythmic Analysis</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-medium mb-1">Upload Score or Audio:</label>
                        <input type="file" accept=".mp3,.wav,.midi,.pdf" class="w-full p-2 border rounded">
                    </div>
                    <button class="btn btn-primary w-full">Start Analysis</button>
                </div>
                <div id="analysis-results" class="p-4 bg-gray-100 dark:bg-gray-700 rounded">
                    <div class="text-center">
                        <div class="text-lg font-semibold mb-2">Analysis Tools</div>
                        <div class="text-sm text-gray-600 dark:text-gray-300">
                            Upload a file and select analysis type to begin
                        </div>
                        <div class="mt-4 space-y-2">
                            <div class="text-xs text-gray-500">Supported formats:</div>
                            <div class="text-xs">Audio: MP3, WAV | Scores: PDF, MIDI</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    trackEvent(event, data = {}) {
        // Analytics tracking
        console.log(`📈 Event: ${event}`, data);
        
        // Send to analytics service (if implemented)
        if (window.gtag) {
            window.gtag('event', event, data);
        }
    }
}

// Utility functions
const utils = {
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NoisyNeuronApp();
});

// Export for external use
window.NoisyNeuronApp = NoisyNeuronApp;
window.utils = utils;