/**
 * WebSocket Manager for Real-time Audio Processing and Music Theory
 * Handles communication with Django Channels WebSocket consumers
 */

class WebSocketManager {
    constructor() {
        this.audioSocket = null;
        this.theorySocket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // Event handlers storage
        this.eventHandlers = {
            audio: new Map(),
            theory: new Map()
        };
        
        this.init();
    }
    
    init() {
        // Get WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        
        this.audioSocketURL = `${protocol}//${host}/ws/audio-processing/`;
        this.theorySocketURL = `${protocol}//${host}/ws/music-theory/`;
        
        console.log('🔌 WebSocket Manager initialized');
        console.log('Audio Socket URL:', this.audioSocketURL);
        console.log('Theory Socket URL:', this.theorySocketURL);
    }
    
    // Connection Management
    connectAudioSocket() {
        if (this.audioSocket && this.audioSocket.readyState === WebSocket.OPEN) {
            console.log('📡 Audio socket already connected');
            return;
        }
        
        console.log('🔌 Connecting to audio processing socket...');
        this.audioSocket = new WebSocket(this.audioSocketURL);
        
        this.audioSocket.onopen = (event) => {
            console.log('✅ Audio socket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.emit('audio', 'connected', { message: 'Audio processing connection established' });
        };
        
        this.audioSocket.onmessage = (event) => {
            this.handleAudioMessage(JSON.parse(event.data));
        };
        
        this.audioSocket.onclose = (event) => {
            console.log('❌ Audio socket disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.emit('audio', 'disconnected', { code: event.code, reason: event.reason });
            this.attemptReconnect('audio');
        };
        
        this.audioSocket.onerror = (error) => {
            console.error('🚨 Audio socket error:', error);
            this.emit('audio', 'error', { error: 'Connection error' });
        };
    }
    
    connectTheorySocket() {
        if (this.theorySocket && this.theorySocket.readyState === WebSocket.OPEN) {
            console.log('📡 Theory socket already connected');
            return;
        }
        
        console.log('🔌 Connecting to music theory socket...');
        this.theorySocket = new WebSocket(this.theorySocketURL);
        
        this.theorySocket.onopen = (event) => {
            console.log('✅ Theory socket connected');
            this.emit('theory', 'connected', { message: 'Music theory connection established' });
        };
        
        this.theorySocket.onmessage = (event) => {
            this.handleTheoryMessage(JSON.parse(event.data));
        };
        
        this.theorySocket.onclose = (event) => {
            console.log('❌ Theory socket disconnected:', event.code, event.reason);
            this.emit('theory', 'disconnected', { code: event.code, reason: event.reason });
            this.attemptReconnect('theory');
        };
        
        this.theorySocket.onerror = (error) => {
            console.error('🚨 Theory socket error:', error);
            this.emit('theory', 'error', { error: 'Connection error' });
        };
    }
    
    connectAll() {
        this.connectAudioSocket();
        this.connectTheorySocket();
    }
    
    disconnect() {
        if (this.audioSocket) {
            this.audioSocket.close();
            this.audioSocket = null;
        }
        if (this.theorySocket) {
            this.theorySocket.close();
            this.theorySocket = null;
        }
        this.isConnected = false;
        console.log('🔌 All WebSocket connections closed');
    }
    
    attemptReconnect(socketType) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ Max reconnection attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff
        
        console.log(`🔄 Attempting to reconnect ${socketType} socket in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            if (socketType === 'audio') {
                this.connectAudioSocket();
            } else if (socketType === 'theory') {
                this.connectTheorySocket();
            }
        }, delay);
    }
    
    // Message Handlers
    handleAudioMessage(data) {
        console.log('📥 Audio message:', data);
        
        switch (data.type) {
            case 'connection_established':
                this.emit('audio', 'ready', data);
                break;
            case 'processing_started':
                this.emit('audio', 'processing_started', data);
                break;
            case 'progress_update':
                this.emit('audio', 'progress', data);
                break;
            case 'processing_complete':
                this.emit('audio', 'complete', data);
                break;
            case 'processing_error':
                this.emit('audio', 'error', data);
                break;
            case 'processing_cancelled':
                this.emit('audio', 'cancelled', data);
                break;
            case 'pong':
                this.emit('audio', 'pong', data);
                break;
            default:
                console.warn('Unknown audio message type:', data.type);
        }
    }
    
    handleTheoryMessage(data) {
        console.log('📥 Theory message:', data);
        
        switch (data.type) {
            case 'connection_established':
                this.emit('theory', 'ready', data);
                break;
            case 'chord_analysis_result':
                this.emit('theory', 'chord_analysis', data);
                break;
            case 'scale_generation_result':
                this.emit('theory', 'scale_generated', data);
                break;
            case 'key_detection_result':
                this.emit('theory', 'key_detected', data);
                break;
            case 'chord_substitutions_result':
                this.emit('theory', 'substitutions', data);
                break;
            case 'practice_exercise_result':
                this.emit('theory', 'exercise', data);
                break;
            case 'chord_progression_result':
                this.emit('theory', 'progression', data);
                break;
            case 'error':
                this.emit('theory', 'error', data);
                break;
            case 'pong':
                this.emit('theory', 'pong', data);
                break;
            default:
                console.warn('Unknown theory message type:', data.type);
        }
    }
    
    // Audio Processing Methods
    startAudioProcessing(processingType, filePath, options = {}) {
        if (!this.audioSocket || this.audioSocket.readyState !== WebSocket.OPEN) {
            console.error('Audio socket not connected');
            return false;
        }
        
        const message = {
            type: 'start_processing',
            processing_type: processingType,
            file_path: filePath,
            options: options
        };
        
        this.audioSocket.send(JSON.stringify(message));
        console.log('📤 Sent audio processing request:', message);
        return true;
    }
    
    cancelAudioProcessing() {
        if (!this.audioSocket || this.audioSocket.readyState !== WebSocket.OPEN) {
            return false;
        }
        
        this.audioSocket.send(JSON.stringify({
            type: 'cancel_processing'
        }));
        return true;
    }
    
    requestProgress() {
        if (!this.audioSocket || this.audioSocket.readyState !== WebSocket.OPEN) {
            return false;
        }
        
        this.audioSocket.send(JSON.stringify({
            type: 'request_progress'
        }));
        return true;
    }
    
    // Music Theory Methods
    analyzeChord(notes) {
        if (!this.theorySocket || this.theorySocket.readyState !== WebSocket.OPEN) {
            console.error('Theory socket not connected');
            return false;
        }
        
        this.theorySocket.send(JSON.stringify({
            type: 'analyze_chord',
            notes: notes
        }));
        return true;
    }
    
    generateScale(root, scaleType) {
        if (!this.theorySocket || this.theorySocket.readyState !== WebSocket.OPEN) {
            console.error('Theory socket not connected');
            return false;
        }
        
        this.theorySocket.send(JSON.stringify({
            type: 'generate_scale',
            root: root,
            scale_type: scaleType
        }));
        return true;
    }
    
    detectKey(chromaVector) {
        if (!this.theorySocket || this.theorySocket.readyState !== WebSocket.OPEN) {
            console.error('Theory socket not connected');
            return false;
        }
        
        this.theorySocket.send(JSON.stringify({
            type: 'detect_key',
            chroma_vector: chromaVector
        }));
        return true;
    }
    
    getChordSubstitutions(chord, instrument = 'guitar', maxResults = 5) {
        if (!this.theorySocket || this.theorySocket.readyState !== WebSocket.OPEN) {
            console.error('Theory socket not connected');
            return false;
        }
        
        this.theorySocket.send(JSON.stringify({
            type: 'get_substitutions',
            chord: chord,
            instrument: instrument,
            max_results: maxResults
        }));
        return true;
    }
    
    generatePracticeExercise(exerciseType = 'chord_recognition', difficulty = 1) {
        if (!this.theorySocket || this.theorySocket.readyState !== WebSocket.OPEN) {
            console.error('Theory socket not connected');
            return false;
        }
        
        this.theorySocket.send(JSON.stringify({
            type: 'practice_exercise',
            exercise_type: exerciseType,
            difficulty: difficulty
        }));
        return true;
    }
    
    generateChordProgression(key = 'C', mode = 'major', length = 4) {
        if (!this.theorySocket || this.theorySocket.readyState !== WebSocket.OPEN) {
            console.error('Theory socket not connected');
            return false;
        }
        
        this.theorySocket.send(JSON.stringify({
            type: 'chord_progression',
            key: key,
            mode: mode,
            length: length
        }));
        return true;
    }
    
    // Utility Methods
    ping(socketType = 'both') {
        const timestamp = Date.now();
        
        if (socketType === 'audio' || socketType === 'both') {
            if (this.audioSocket && this.audioSocket.readyState === WebSocket.OPEN) {
                this.audioSocket.send(JSON.stringify({
                    type: 'ping',
                    timestamp: timestamp
                }));
            }
        }
        
        if (socketType === 'theory' || socketType === 'both') {
            if (this.theorySocket && this.theorySocket.readyState === WebSocket.OPEN) {
                this.theorySocket.send(JSON.stringify({
                    type: 'ping',
                    timestamp: timestamp
                }));
            }
        }
    }
    
    // Event System
    on(socketType, eventName, handler) {
        if (!this.eventHandlers[socketType]) {
            console.error('Invalid socket type:', socketType);
            return;
        }
        
        if (!this.eventHandlers[socketType].has(eventName)) {
            this.eventHandlers[socketType].set(eventName, []);
        }
        
        this.eventHandlers[socketType].get(eventName).push(handler);
    }
    
    off(socketType, eventName, handler) {
        if (!this.eventHandlers[socketType] || !this.eventHandlers[socketType].has(eventName)) {
            return;
        }
        
        const handlers = this.eventHandlers[socketType].get(eventName);
        const index = handlers.indexOf(handler);
        if (index > -1) {
            handlers.splice(index, 1);
        }
    }
    
    emit(socketType, eventName, data) {
        if (!this.eventHandlers[socketType] || !this.eventHandlers[socketType].has(eventName)) {
            return;
        }
        
        const handlers = this.eventHandlers[socketType].get(eventName);
        handlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error('Error in event handler:', error);
            }
        });
    }
    
    // Status Methods
    getConnectionStatus() {
        return {
            audio: this.audioSocket ? this.audioSocket.readyState : WebSocket.CLOSED,
            theory: this.theorySocket ? this.theorySocket.readyState : WebSocket.CLOSED,
            isConnected: this.isConnected
        };
    }
    
    isAudioConnected() {
        return this.audioSocket && this.audioSocket.readyState === WebSocket.OPEN;
    }
    
    isTheoryConnected() {
        return this.theorySocket && this.theorySocket.readyState === WebSocket.OPEN;
    }
}

// Global WebSocket Manager instance
window.wsManager = new WebSocketManager();

// Auto-connect when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing WebSocket connections...');
    window.wsManager.connectAll();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    window.wsManager.disconnect();
});

console.log('📡 WebSocket Manager loaded');