/**
 * NoisyNeuron - Audio Separation Module
 * Handles audio file processing and stem separation
 */

class AudioSeparationManager {
    constructor() {
        this.currentProject = null;
        this.processingQueue = [];
        this.audioContext = null;
        this.visualizer = null;
        this.separatedStems = new Map();
        
        this.init();
    }
    
    init() {
        this.setupAudioContext();
        this.setupEventListeners();
        this.setupVisualizer();
        
        console.log('🎵 Audio Separation Manager initialized');
    }
    
    setupAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🔊 Audio context created');
        } catch (error) {
            console.warn('🔊 Web Audio API not supported:', error);
        }
    }
    
    setupEventListeners() {
        // File upload handlers
        const fileInput = document.getElementById('audio-upload');
        const dropZone = document.querySelector('.border-dashed');
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelection(e.target.files[0]);
            });
        }
        
        // Separation options
        const qualitySelect = document.querySelector('[name="quality"]');
        if (qualitySelect) {
            qualitySelect.addEventListener('change', (e) => {
                this.updateSeparationOptions({ quality: e.target.value });
            });
        }
        
        // Stem selection checkboxes
        const stemCheckboxes = document.querySelectorAll('input[type=\"checkbox\"]');
        stemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectedStems();
            });
        });
    }
    
    setupVisualizer() {
        const visualizerContainer = document.getElementById('audio-visualizer');
        if (visualizerContainer) {
            this.visualizer = new AudioVisualizer(visualizerContainer, this.audioContext);
        }
    }
    
    async handleFileSelection(file) {
        if (!file) return;
        
        console.log(`📁 File selected: ${file.name}`);
        
        // Validate file
        const validation = this.validateAudioFile(file);
        if (!validation.valid) {
            this.showError(validation.error);
            return;
        }
        
        // Show file info
        this.displayFileInfo(file);
        
        // Create audio preview
        await this.createAudioPreview(file);
        
        // Enable separation options
        this.enableSeparationOptions();
    }
    
    validateAudioFile(file) {
        const validTypes = [
            'audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/wave',
            'audio/flac', 'audio/m4a', 'audio/mp4', 'audio/aac', 'audio/ogg'
        ];
        
        const validExtensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'];
        const maxSize = 100 * 1024 * 1024; // 100MB
        const maxDuration = 600; // 10 minutes
        
        // Check file type
        const hasValidType = validTypes.includes(file.type) || 
                            validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
        
        if (!hasValidType) {
            return { valid: false, error: 'Invalid file type. Please select an audio file.' };
        }
        
        // Check file size
        if (file.size > maxSize) {
            return { valid: false, error: 'File too large. Maximum size is 100MB.' };
        }
        
        // Additional checks would go here (duration, etc.)
        
        return { valid: true };
    }
    
    displayFileInfo(file) {
        const fileInfoContainer = this.createFileInfoContainer();
        
        fileInfoContainer.innerHTML = `
            <div class="bg-surface border border-light rounded-lg p-4 mb-6">
                <div class="flex items-center gap-4">
                    <div class="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-music text-primary-500"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-semibold text-primary">${file.name}</h4>
                        <div class="flex gap-4 text-sm text-secondary mt-1">
                            <span><i class="fas fa-hdd mr-1"></i>${this.formatFileSize(file.size)}</span>
                            <span><i class="fas fa-file-audio mr-1"></i>${this.getFileExtension(file.name).toUpperCase()}</span>
                            <span id="duration-info"><i class="fas fa-clock mr-1"></i>Calculating...</span>
                        </div>
                    </div>
                    <button class="btn btn-ghost btn-sm" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;
        
        return fileInfoContainer;
    }
    
    createFileInfoContainer() {
        let container = document.getElementById('file-info-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'file-info-container';
            
            const uploadArea = document.querySelector('.border-dashed').closest('.card');
            uploadArea.parentNode.insertBefore(container, uploadArea.nextSibling);
        }
        return container;
    }
    
    async createAudioPreview(file) {
        try {
            const audioUrl = URL.createObjectURL(file);
            const audio = new Audio(audioUrl);
            
            // Wait for metadata to load
            await new Promise((resolve, reject) => {
                audio.addEventListener('loadedmetadata', resolve);
                audio.addEventListener('error', reject);
                audio.load();
            });
            
            // Update duration info
            const durationElement = document.getElementById('duration-info');
            if (durationElement) {
                durationElement.innerHTML = `<i class="fas fa-clock mr-1"></i>${this.formatDuration(audio.duration)}`;
            }
            
            // Create audio player
            this.createAudioPlayer(audioUrl, audio.duration);
            
            // Create waveform visualization
            if (this.visualizer) {
                await this.visualizer.loadAudio(audioUrl);
            }
            
        } catch (error) {
            console.error('❌ Failed to create audio preview:', error);
            this.showError('Failed to load audio file preview');
        }
    }
    
    createAudioPlayer(audioUrl, duration) {
        const playerContainer = this.createPlayerContainer();
        
        playerContainer.innerHTML = `
            <div class="audio-player">
                <div class="audio-controls">
                    <button class="play-button" id="play-btn">
                        <i class="fas fa-play"></i>
                    </button>
                    <div class="progress-bar" id="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                    <div class="time-display">
                        <span id="current-time">0:00</span>
                        <span>/</span>
                        <span id="total-time">${this.formatDuration(duration)}</span>
                    </div>
                    <div class="volume-control">
                        <i class="fas fa-volume-up"></i>
                        <input type="range" id="volume-slider" min="0" max="100" value="100" class="ml-2">
                    </div>
                </div>
                <div class="visualizer" id="audio-visualizer"></div>
            </div>
        `;
        
        // Setup player functionality
        this.setupAudioPlayer(audioUrl);
    }
    
    createPlayerContainer() {
        let container = document.getElementById('audio-player-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'audio-player-container';
            
            const fileInfo = document.getElementById('file-info-container');
            if (fileInfo) {
                fileInfo.appendChild(container);
            }
        }
        return container;
    }
    
    setupAudioPlayer(audioUrl) {
        const audio = new Audio(audioUrl);
        const playBtn = document.getElementById('play-btn');
        const progressBar = document.getElementById('progress-bar');
        const progressFill = document.getElementById('progress-fill');
        const currentTimeEl = document.getElementById('current-time');
        const volumeSlider = document.getElementById('volume-slider');
        
        let isPlaying = false;
        
        // Play/pause functionality
        playBtn.addEventListener('click', () => {
            if (isPlaying) {
                audio.pause();
                playBtn.innerHTML = '<i class=\"fas fa-play\"></i>';
                isPlaying = false;
            } else {
                audio.play();
                playBtn.innerHTML = '<i class=\"fas fa-pause\"></i>';
                isPlaying = true;
            }
        });
        
        // Progress bar
        audio.addEventListener('timeupdate', () => {
            const progress = (audio.currentTime / audio.duration) * 100;
            progressFill.style.width = `${progress}%`;
            currentTimeEl.textContent = this.formatDuration(audio.currentTime);
        });
        
        // Seek functionality
        progressBar.addEventListener('click', (e) => {
            const rect = progressBar.getBoundingClientRect();
            const clickX = e.clientX - rect.left;
            const progress = clickX / rect.width;
            audio.currentTime = progress * audio.duration;
        });
        
        // Volume control
        volumeSlider.addEventListener('input', (e) => {
            audio.volume = e.target.value / 100;
        });
        
        // Audio ended
        audio.addEventListener('ended', () => {
            playBtn.innerHTML = '<i class=\"fas fa-play\"></i>';
            isPlaying = false;
            progressFill.style.width = '0%';
            currentTimeEl.textContent = '0:00';
        });
    }
    
    enableSeparationOptions() {
        // Show separation options
        const optionsCard = document.querySelector('.card:last-child');
        if (optionsCard) {
            optionsCard.style.display = 'block';
        }
        
        // Add separation button
        this.createSeparationButton();
    }
    
    createSeparationButton() {
        let buttonContainer = document.getElementById('separation-button-container');
        if (!buttonContainer) {
            buttonContainer = document.createElement('div');
            buttonContainer.id = 'separation-button-container';
            buttonContainer.className = 'mt-6 text-center';
            
            const playerContainer = document.getElementById('audio-player-container');
            if (playerContainer) {
                playerContainer.appendChild(buttonContainer);
            }
        }
        
        buttonContainer.innerHTML = `
            <button class="btn btn-primary btn-lg" id="start-separation-btn">
                <i class="fas fa-magic mr-2"></i>
                Start Audio Separation
            </button>
        `;
        
        const startBtn = document.getElementById('start-separation-btn');
        startBtn.addEventListener('click', () => {
            this.startSeparation();
        });
    }
    
    async startSeparation() {
        const fileInput = document.getElementById('audio-upload');
        const file = fileInput.files[0];
        
        if (!file) {
            this.showError('Please select an audio file first');
            return;
        }
        
        console.log('🎵 Starting audio separation...');
        
        // Get separation options
        const options = this.getSeparationOptions();
        
        // Show processing UI
        this.showProcessingUI();
        
        try {
            // Upload and start processing
            const result = await this.uploadAndProcess(file, options);
            
            console.log('✅ Separation started:', result);
            
            // Monitor progress via WebSocket
            if (window.wsManager) {
                window.wsManager.startProcessing(result.project_id, options);
            }
            
        } catch (error) {
            console.error('❌ Separation failed:', error);
            this.showError(`Separation failed: ${error.message}`);
            this.hideProcessingUI();
        }
    }
    
    getSeparationOptions() {
        const qualitySelect = document.querySelector('select');
        const stemCheckboxes = document.querySelectorAll('input[type=\"checkbox\"]:checked');
        
        const quality = qualitySelect ? qualitySelect.value : 'balanced';
        const stems = Array.from(stemCheckboxes).map(cb => cb.nextSibling.textContent.trim().toLowerCase());
        
        return { quality, stems };
    }
    
    async uploadAndProcess(file, options) {
        const formData = new FormData();
        formData.append('audio_file', file);
        formData.append('quality', options.quality);
        formData.append('stems', JSON.stringify(options.stems));
        
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const response = await fetch('/api/audio/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}`);
        }
        
        return await response.json();
    }
    
    showProcessingUI() {
        // Create processing overlay
        const overlay = document.createElement('div');
        overlay.id = 'processing-overlay';
        overlay.className = 'fixed inset-0 bg-overlay z-modal flex items-center justify-center';
        
        overlay.innerHTML = `
            <div class="bg-surface p-8 rounded-2xl shadow-2xl max-w-md w-full mx-4">
                <div class="text-center">
                    <div class="loading-spinner mx-auto mb-4 w-12 h-12"></div>
                    <h3 class="text-xl font-semibold mb-2">Processing Audio</h3>
                    <p class="text-secondary mb-4">Separating stems using AI models...</p>
                    
                    <div class="bg-tertiary rounded-full h-3 mb-4">
                        <div class="bg-primary-500 h-3 rounded-full transition-all duration-300" 
                             id="processing-progress" style="width: 0%"></div>
                    </div>
                    
                    <div class="text-sm">
                        <div id="processing-stage" class="font-medium">Initializing...</div>
                        <div id="processing-percentage" class="text-secondary">0%</div>
                    </div>
                    
                    <button class="btn btn-secondary btn-sm mt-4" onclick="this.cancelProcessing()">
                        Cancel
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }
    
    hideProcessingUI() {
        const overlay = document.getElementById('processing-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
    
    updateProcessingProgress(progress, stage) {
        const progressBar = document.getElementById('processing-progress');
        const stageElement = document.getElementById('processing-stage');
        const percentageElement = document.getElementById('processing-percentage');
        
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
        
        if (stageElement) {
            stageElement.textContent = stage;
        }
        
        if (percentageElement) {
            percentageElement.textContent = `${Math.round(progress)}%`;
        }
    }
    
    handleSeparationComplete(result) {
        console.log('✅ Separation complete:', result);
        
        this.hideProcessingUI();
        this.displaySeparationResults(result);
        
        if (window.app) {
            window.app.showNotification('Audio separation completed successfully!', 'success');
        }
    }
    
    displaySeparationResults(result) {
        // Create results container
        const resultsContainer = document.createElement('div');
        resultsContainer.className = 'mt-8';
        resultsContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">
                        <i class="fas fa-check-circle text-success mr-2"></i>
                        Separation Complete
                    </h3>
                </div>
                <div class="card-body">
                    <div class="grid gap-4" id="stems-container">
                        <!-- Stems will be populated here -->
                    </div>
                    
                    <div class="mt-6 flex gap-3">
                        <button class="btn btn-primary">
                            <i class="fas fa-download mr-2"></i>
                            Download All Stems
                        </button>
                        <button class="btn btn-secondary">
                            <i class="fas fa-play mr-2"></i>
                            Open in Practice Mode
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Add to page
        const separateSection = document.getElementById('separate-section');
        separateSection.appendChild(resultsContainer);
        
        // Populate stems
        this.populateStems(result.stems);
    }
    
    populateStems(stems) {
        const stemsContainer = document.getElementById('stems-container');
        
        stems.forEach(stem => {
            const stemElement = document.createElement('div');
            stemElement.className = 'flex items-center justify-between p-4 bg-tertiary rounded-lg';
            
            stemElement.innerHTML = `
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                        <i class="fas fa-${this.getStemIcon(stem.type)} text-primary-500"></i>
                    </div>
                    <div>
                        <h4 class="font-medium">${this.capitalize(stem.type)}</h4>
                        <p class="text-sm text-secondary">${this.formatFileSize(stem.size)}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <button class="btn btn-ghost btn-sm" onclick="this.playStem('${stem.id}')">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="btn btn-ghost btn-sm" onclick="this.downloadStem('${stem.id}')">
                        <i class="fas fa-download"></i>
                    </button>
                </div>
            `;
            
            stemsContainer.appendChild(stemElement);
        });
    }
    
    getStemIcon(stemType) {
        const icons = {
            vocals: 'microphone',
            drums: 'drum',
            bass: 'guitar',
            other: 'music',
            piano: 'piano-keyboard',
            guitar: 'guitar'
        };
        
        return icons[stemType] || 'music';
    }
    
    // Utility methods
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
    
    getFileExtension(filename) {
        return filename.split('.').pop();
    }
    
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
    
    showError(message) {
        if (window.app) {
            window.app.showNotification(message, 'error');
        } else {
            console.error('❌', message);
        }
    }
    
    updateSeparationOptions(options) {
        console.log('🔧 Updated separation options:', options);
    }
    
    updateSelectedStems() {
        const selectedStems = Array.from(
            document.querySelectorAll('input[type=\"checkbox\"]:checked')
        ).map(cb => cb.nextSibling.textContent.trim());
        
        console.log('🎵 Selected stems:', selectedStems);
    }
}

// Audio Visualizer Class
class AudioVisualizer {
    constructor(container, audioContext) {
        this.container = container;
        this.audioContext = audioContext;
        this.analyser = null;
        this.dataArray = null;
        this.canvas = null;
        this.canvasContext = null;
        this.animationId = null;
        
        this.init();
    }
    
    init() {
        this.createCanvas();
        this.setupAnalyser();
    }
    
    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.offsetWidth;
        this.canvas.height = 200;
        this.canvas.className = 'w-full h-full';
        
        this.canvasContext = this.canvas.getContext('2d');
        this.container.appendChild(this.canvas);
    }
    
    setupAnalyser() {
        if (this.audioContext) {
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        }
    }
    
    async loadAudio(audioUrl) {
        try {
            const response = await fetch(audioUrl);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            this.drawWaveform(audioBuffer);
            
        } catch (error) {
            console.error('❌ Failed to load audio for visualization:', error);
        }
    }
    
    drawWaveform(audioBuffer) {
        const canvas = this.canvas;
        const ctx = this.canvasContext;
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Get audio data
        const channelData = audioBuffer.getChannelData(0);
        const samplesPerPixel = Math.floor(channelData.length / width);
        
        // Set style
        ctx.strokeStyle = '#0ea5e9';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        // Draw waveform
        for (let x = 0; x < width; x++) {
            const startSample = x * samplesPerPixel;
            const endSample = startSample + samplesPerPixel;
            
            let min = 1;
            let max = -1;
            
            for (let i = startSample; i < endSample; i++) {
                if (channelData[i] < min) min = channelData[i];
                if (channelData[i] > max) max = channelData[i];
            }
            
            const y1 = ((min + 1) / 2) * height;
            const y2 = ((max + 1) / 2) * height;
            
            if (x === 0) {
                ctx.moveTo(x, y1);
            } else {
                ctx.lineTo(x, y1);
                ctx.lineTo(x, y2);
            }
        }
        
        ctx.stroke();
    }
    
    startRealtimeVisualization(audioSource) {
        if (this.analyser) {
            audioSource.connect(this.analyser);
            this.animate();
        }
    }
    
    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        this.analyser.getByteFrequencyData(this.dataArray);
        
        const canvas = this.canvas;
        const ctx = this.canvasContext;
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        
        const barWidth = width / this.dataArray.length;
        
        for (let i = 0; i < this.dataArray.length; i++) {
            const barHeight = (this.dataArray[i] / 255) * height;
            
            ctx.fillStyle = `hsl(${200 + (i / this.dataArray.length) * 60}, 70%, 60%)`;
            ctx.fillRect(i * barWidth, height - barHeight, barWidth, barHeight);
        }
    }
    
    stop() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }
}

// Initialize audio separation manager
document.addEventListener('DOMContentLoaded', () => {
    window.audioSeparation = new AudioSeparationManager();
});

// Export for external use
window.AudioSeparationManager = AudioSeparationManager;
window.AudioVisualizer = AudioVisualizer;