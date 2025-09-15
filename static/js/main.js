/**
 * Main JavaScript file for NoisyNeuron application
 * Handles UI interactions, file uploads, and processing workflow
 */

class NoisyNeuronApp {
    constructor() {
        this.currentFile = null;
        this.currentProject = null;
        this.processingStatus = null;
        this.wsConnection = null;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setupWebSocket();
        this.loadUserSession();
    }
    
    setupEventListeners() {
        // Navigation and modals
        document.getElementById('loginBtn')?.addEventListener('click', () => this.showModal('loginModal'));
        document.getElementById('signupBtn')?.addEventListener('click', () => this.showModal('signupModal'));
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => this.hideModal(e.target.closest('.modal')));
        });
        
        // Auth forms
        document.getElementById('loginForm')?.addEventListener('submit', (e) => this.handleLogin(e));
        document.getElementById('signupForm')?.addEventListener('submit', (e) => this.handleSignup(e));
        
        // Main workflow buttons
        document.getElementById('startSeparationBtn')?.addEventListener('click', () => this.showUploadSection());
        document.getElementById('watchDemoBtn')?.addEventListener('click', () => this.playDemo());
        
        // File upload
        this.setupFileUpload();
        
        // Processing options
        document.getElementById('toggleAdvanced')?.addEventListener('click', () => this.toggleAdvancedOptions());
        document.getElementById('startProcessingBtn')?.addEventListener('click', () => this.startProcessing());
        
        // Processing controls
        document.getElementById('cancelProcessingBtn')?.addEventListener('click', () => this.cancelProcessing());
        
        // Results actions
        document.getElementById('downloadAllBtn')?.addEventListener('click', () => this.downloadAllStems());
        document.getElementById('processNewBtn')?.addEventListener('click', () => this.processNewFile());
        
        // Smooth scrolling for navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }
    
    setupFileUpload() {
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('audioFileInput');
        
        if (!uploadArea || !fileInput) return;
        
        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
        
        // Remove file button
        document.getElementById('removeFileBtn')?.addEventListener('click', () => this.removeFile());
    }
    
    setupWebSocket() {
        // Setup WebSocket connection for real-time updates
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/processing/`;
        
        try {
            this.wsConnection = new WebSocket(wsUrl);
            
            this.wsConnection.onopen = () => {
                console.log('WebSocket connected');
            };
            
            this.wsConnection.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.wsConnection.onclose = () => {
                console.log('WebSocket disconnected');
                // Attempt to reconnect after 5 seconds
                setTimeout(() => this.setupWebSocket(), 5000);
            };
            
            this.wsConnection.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.warn('WebSocket not available, falling back to polling');
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'processing_update':
                this.updateProcessingStatus(data.payload);
                break;
            case 'processing_complete':
                this.handleProcessingComplete(data.payload);
                break;
            case 'processing_error':
                this.handleProcessingError(data.payload);
                break;
        }
    }
    
    async handleFileSelect(file) {
        // Validate file
        const validation = this.validateAudioFile(file);
        if (!validation.valid) {
            this.showError(validation.message);
            return;
        }
        
        this.currentFile = file;
        this.showFilePreview(file);
        
        // Analyze file
        try {
            this.showLoading('Analyzing audio file...');
            const analysis = await this.analyzeAudioFile(file);
            this.updateFileAnalysis(analysis);
            this.hideLoading();
            this.showProcessingOptions();
        } catch (error) {
            this.hideLoading();
            this.showError('Error analyzing audio file: ' + error.message);
        }
    }
    
    validateAudioFile(file) {
        const supportedTypes = ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/ogg', 'audio/mp4', 'audio/aac'];
        const maxSize = 100 * 1024 * 1024; // 100MB
        
        if (!supportedTypes.includes(file.type)) {
            return { valid: false, message: 'Unsupported file type. Please use MP3, WAV, FLAC, OGG, M4A, or AAC.' };
        }
        
        if (file.size > maxSize) {
            return { valid: false, message: 'File too large. Maximum size is 100MB.' };
        }
        
        return { valid: true };
    }
    
    showFilePreview(file) {
        const preview = document.getElementById('filePreview');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const audioPlayer = document.getElementById('audioPlayer');
        
        if (preview) {
            preview.classList.remove('hidden');
            
            if (fileName) fileName.textContent = file.name;
            if (fileSize) fileSize.textContent = this.formatFileSize(file.size);
            
            if (audioPlayer) {
                const url = URL.createObjectURL(file);
                audioPlayer.src = url;
                audioPlayer.addEventListener('loadedmetadata', () => {
                    const duration = document.getElementById('fileDuration');
                    if (duration) {
                        duration.textContent = this.formatDuration(audioPlayer.duration);
                    }
                    
                    // Generate waveform preview
                    this.generateWaveformPreview(audioPlayer);
                });
            }
        }
    }
    
    async analyzeAudioFile(file) {
        const formData = new FormData();
        formData.append('audio_file', file);
        
        try {
            const response = await fetch('/api/audio/analyze/', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Server error' }));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Audio analysis error:', error);
            throw error;
        }
    }
    
    updateFileAnalysis(analysis) {
        // Update UI with analysis results
        console.log('Audio analysis:', analysis);
        
        // Update duration if not already set
        const duration = document.getElementById('fileDuration');
        if (duration && analysis.duration) {
            duration.textContent = this.formatDuration(analysis.duration);
        }
    }
    
    generateWaveformPreview(audioElement) {
        const canvas = document.getElementById('waveformDisplay');
        if (!canvas) return;
        
        // This is a simplified waveform visualization
        // In a real implementation, you'd use Web Audio API
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#667eea';
        
        // Generate mock waveform data
        const bars = 100;
        const barWidth = width / bars;
        
        for (let i = 0; i < bars; i++) {
            const barHeight = Math.random() * height * 0.8;
            const x = i * barWidth;
            const y = (height - barHeight) / 2;
            
            ctx.fillRect(x, y, barWidth - 1, barHeight);
        }
    }
    
    showProcessingOptions() {
        this.hideSection('upload-section');
        this.showSection('processing-options');
    }
    
    toggleAdvancedOptions() {
        const panel = document.getElementById('advancedPanel');
        const button = document.getElementById('toggleAdvanced');
        
        if (panel && button) {
            panel.classList.toggle('hidden');
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = panel.classList.contains('hidden') 
                    ? 'fas fa-cog' 
                    : 'fas fa-times';
            }
        }
    }
    
    async startProcessing() {
        if (!this.currentFile) {
            this.showError('No file selected');
            return;
        }
        
        // Get processing options
        const options = this.getProcessingOptions();
        
        try {
            this.showSection('processing-status');
            this.hideSection('processing-options');
            
            // Start processing
            const response = await this.submitProcessingJob(this.currentFile, options);
            this.processingStatus = response;
            
            // Start status polling if WebSocket is not available
            if (!this.wsConnection || this.wsConnection.readyState !== WebSocket.OPEN) {
                this.startStatusPolling(response.job_id);
            }
            
        } catch (error) {
            this.showError('Failed to start processing: ' + error.message);
            this.showSection('processing-options');
            this.hideSection('processing-status');
        }
    }
    
    getProcessingOptions() {
        return {
            separate_vocals: document.getElementById('separateVocals')?.checked ?? true,
            separate_drums: document.getElementById('separateDrums')?.checked ?? true,
            separate_bass: document.getElementById('separateBass')?.checked ?? true,
            separate_other: document.getElementById('separateOther')?.checked ?? true,
            markov_order: parseInt(document.getElementById('markovOrder')?.value ?? '2'),
            quality_level: document.getElementById('qualityLevel')?.value ?? 'balanced',
            output_format: document.getElementById('outputFormat')?.value ?? 'wav'
        };
    }
    
    async submitProcessingJob(file, options) {
        const formData = new FormData();
        formData.append('audio_file', file);
        formData.append('options', JSON.stringify(options));
        
        try {
            const response = await fetch('/api/audio/process/', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Server error' }));
                throw new Error(errorData.error || `HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Processing submission error:', error);
            throw error;
        }
    }
    
    updateProcessingStatus(status) {
        // Update progress bar
        const progressFill = document.getElementById('progressFill');
        const progressPercent = document.getElementById('progressPercent');
        const currentStep = document.getElementById('currentStep');
        
        if (progressFill) {
            progressFill.style.width = `${status.progress}%`;
        }
        
        if (progressPercent) {
            progressPercent.textContent = `${status.progress}%`;
        }
        
        if (currentStep) {
            currentStep.textContent = status.current_step || 'Processing...';
        }
        
        // Update visualization nodes
        this.updateVisualizationNodes(status.step_number);
        
        // Update detail statuses
        this.updateDetailStatuses(status);
    }
    
    updateVisualizationNodes(currentStep) {
        const nodes = document.querySelectorAll('.node');
        nodes.forEach((node, index) => {
            const stepNumber = parseInt(node.dataset.step);
            
            if (stepNumber < currentStep) {
                node.className = 'node completed';
            } else if (stepNumber === currentStep) {
                node.className = 'node active';
            } else {
                node.className = 'node';
            }
        });
    }
    
    updateDetailStatuses(status) {
        const statusMap = {
            'markovStatus': status.markov_status || 'Pending',
            'spectralStatus': status.spectral_status || 'Pending',
            'enhancementStatus': status.enhancement_status || 'Pending'
        };
        
        Object.entries(statusMap).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }
    
    handleProcessingComplete(results) {
        this.hideSection('processing-status');
        this.showResults(results);
    }
    
    handleProcessingError(error) {
        this.hideSection('processing-status');
        this.showError('Processing failed: ' + error.message);
        this.showSection('processing-options');
    }
    
    showResults(results) {
        this.showSection('results-section');
        this.populateResultsGrid(results);
    }
    
    populateResultsGrid(results) {
        const grid = document.getElementById('resultsGrid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        results.separated_tracks.forEach(track => {
            const card = this.createResultCard(track);
            grid.appendChild(card);
        });
    }
    
    createResultCard(track) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        card.innerHTML = `
            <div class="result-header">
                <div class="result-title">
                    <i class="fas ${this.getTrackIcon(track.type)}"></i>
                    ${this.getTrackDisplayName(track.type)}
                </div>
                <div class="quality-score">${Math.round(track.quality_score * 100)}%</div>
            </div>
            <div class="result-waveform">
                <canvas width="280" height="60" data-track-id="${track.id}"></canvas>
            </div>
            <audio controls preload="metadata" src="${track.file_url}"></audio>
            <div class="result-controls">
                <button class="btn btn-primary btn-small" onclick="app.downloadTrack('${track.id}')">
                    <i class="fas fa-download"></i>
                    Download
                </button>
                <button class="btn btn-outline btn-small" onclick="app.playTrack('${track.id}')">
                    <i class="fas fa-play"></i>
                    Play
                </button>
            </div>
        `;
        
        return card;
    }
    
    getTrackIcon(type) {
        const iconMap = {
            'vocals': 'fa-microphone',
            'drums': 'fa-drum',
            'bass': 'fa-guitar',
            'other': 'fa-music'
        };
        return iconMap[type] || 'fa-music';
    }
    
    getTrackDisplayName(type) {
        const nameMap = {
            'vocals': 'Vocals',
            'drums': 'Drums',
            'bass': 'Bass',
            'other': 'Other Instruments'
        };
        return nameMap[type] || 'Unknown';
    }
    
    async downloadTrack(trackId) {
        try {
            const response = await fetch(`/api/audio/download/${trackId}/`, {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `track_${trackId}.wav`;
                a.click();
                URL.revokeObjectURL(url);
            }
        } catch (error) {
            this.showError('Failed to download track');
        }
    }
    
    async downloadAllStems() {
        try {
            const response = await fetch(`/api/audio/download-all/${this.processingStatus.job_id}/`, {
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'separated_stems.zip';
                a.click();
                URL.revokeObjectURL(url);
            }
        } catch (error) {
            this.showError('Failed to download stems');
        }
    }
    
    processNewFile() {
        // Reset state and show upload section
        this.currentFile = null;
        this.processingStatus = null;
        
        this.hideSection('results-section');
        this.hideSection('processing-options');
        this.hideSection('processing-status');
        this.showSection('upload-section');
        
        // Clear file preview
        const preview = document.getElementById('filePreview');
        if (preview) {
            preview.classList.add('hidden');
        }
        
        // Reset file input
        const fileInput = document.getElementById('audioFileInput');
        if (fileInput) {
            fileInput.value = '';
        }
    }
    
    removeFile() {
        this.currentFile = null;
        
        const preview = document.getElementById('filePreview');
        if (preview) {
            preview.classList.add('hidden');
        }
        
        const fileInput = document.getElementById('audioFileInput');
        if (fileInput) {
            fileInput.value = '';
        }
        
        this.hideSection('processing-options');
    }
    
    async cancelProcessing() {
        if (!this.processingStatus) return;
        
        try {
            await fetch(`/api/audio/cancel/${this.processingStatus.job_id}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            this.hideSection('processing-status');
            this.showSection('processing-options');
        } catch (error) {
            this.showError('Failed to cancel processing');
        }
    }
    
    startStatusPolling(jobId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/audio/status/${jobId}/`);
                const status = await response.json();
                
                this.updateProcessingStatus(status);
                
                if (status.status === 'completed') {
                    clearInterval(pollInterval);
                    this.handleProcessingComplete(status);
                } else if (status.status === 'failed') {
                    clearInterval(pollInterval);
                    this.handleProcessingError(status);
                }
            } catch (error) {
                console.error('Status polling error:', error);
            }
        }, 2000);
    }
    
    showUploadSection() {
        document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' });
        this.showSection('upload-section');
    }
    
    playDemo() {
        // Implement demo functionality
        this.showInfo('Demo feature coming soon!');
    }
    
    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail')?.value;
        const password = document.getElementById('loginPassword')?.value;
        
        try {
            const response = await fetch('/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ email, password })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleAuthSuccess(data);
                this.hideModal(document.getElementById('loginModal'));
            } else {
                this.showError('Invalid credentials');
            }
        } catch (error) {
            this.showError('Login failed');
        }
    }
    
    async handleSignup(e) {
        e.preventDefault();
        
        const username = document.getElementById('signupUsername')?.value;
        const email = document.getElementById('signupEmail')?.value;
        const password = document.getElementById('signupPassword')?.value;
        const passwordConfirm = document.getElementById('signupPasswordConfirm')?.value;
        
        if (password !== passwordConfirm) {
            this.showError('Passwords do not match');
            return;
        }
        
        try {
            const response = await fetch('/api/auth/signup/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ username, email, password })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.handleAuthSuccess(data);
                this.hideModal(document.getElementById('signupModal'));
            } else {
                const error = await response.json();
                this.showError(error.message || 'Signup failed');
            }
        } catch (error) {
            this.showError('Signup failed');
        }
    }
    
    handleAuthSuccess(data) {
        // Update UI for authenticated user
        localStorage.setItem('auth_token', data.token);
        this.updateAuthUI(data.user);
    }
    
    updateAuthUI(user) {
        const authButtons = document.querySelector('.auth-buttons');
        if (authButtons) {
            authButtons.innerHTML = `
                <span>Welcome, ${user.username}!</span>
                <button class="btn btn-outline" onclick="app.logout()">Logout</button>
            `;
        }
    }
    
    async logout() {
        try {
            await fetch('/api/auth/logout/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
        
        localStorage.removeItem('auth_token');
        location.reload();
    }
    
    loadUserSession() {
        const token = localStorage.getItem('auth_token');
        if (token) {
            // Validate token and update UI
            this.validateAuthToken(token);
        }
    }
    
    async validateAuthToken(token) {
        try {
            const response = await fetch('/api/auth/validate/', {
                headers: {
                    'Authorization': `Token ${token}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateAuthUI(data.user);
            } else {
                localStorage.removeItem('auth_token');
            }
        } catch (error) {
            localStorage.removeItem('auth_token');
        }
    }
    
    // Utility methods
    showSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.remove('hidden');
        }
    }
    
    hideSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.classList.add('hidden');
        }
    }
    
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    hideModal(modal) {
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    showLoading(message = 'Loading...') {
        // Implement loading indicator
        console.log('Loading:', message);
    }
    
    hideLoading() {
        // Hide loading indicator
    }
    
    showError(message) {
        // Create a better error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-notification';
        errorDiv.innerHTML = `
            <div class="error-content">
                <i class="fas fa-exclamation-triangle"></i>
                <span>${message}</span>
                <button class="error-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 400px;
        `;
        
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
        
        console.error('Error:', message);
    }
    
    showInfo(message) {
        // Implement info notification
        alert('Info: ' + message);
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    getCsrfToken() {
        // Try getting from meta tag first
        const metaToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (metaToken) return metaToken;
        
        // Try getting from form input
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (token) return token;
        
        // Fallback: get from cookie
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

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new NoisyNeuronApp();
});
