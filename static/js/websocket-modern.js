/**
 * NoisyNeuron - Modern WebSocket Manager
 * Handles real-time communication for audio processing and collaboration
 */

class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.messageQueue = [];
        this.isConnecting = false;
        
        this.eventListeners = new Map();
        
        this.init();
    }
    
    init() {
        console.log('🔌 Initializing WebSocket Manager');
        this.setupConnections();
    }
    
    setupConnections() {
        // Audio processing WebSocket
        this.createConnection('audio', '/ws/audio-processing/', {
            onMessage: this.handleAudioMessage.bind(this),
            onError: this.handleConnectionError.bind(this, 'audio')
        });
        
        // Music theory WebSocket
        this.createConnection('theory', '/ws/music-theory/', {
            onMessage: this.handleTheoryMessage.bind(this),
            onError: this.handleConnectionError.bind(this, 'theory')
        });
    }
    
    createConnection(name, path, options = {}) {
        if (this.isConnecting) return;
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}${path}`;
        
        console.log(`🔌 Creating WebSocket connection: ${name} -> ${url}`);
        
        try {
            const ws = new WebSocket(url);
            
            ws.onopen = () => {
                console.log(`✅ WebSocket connected: ${name}`);
                this.reconnectAttempts = 0;
                
                // Send queued messages
                this.flushMessageQueue(name);
                
                // Update UI
                this.updateConnectionStatus(name, 'connected');
                
                // Trigger custom event
                this.emit('connectionOpen', { name, ws });
                
                if (options.onOpen) options.onOpen(ws);
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log(`📨 WebSocket message [${name}]:`, data);
                    
                    // Handle common message types
                    this.handleCommonMessages(data, name);
                    
                    // Handle connection-specific messages
                    if (options.onMessage) {
                        options.onMessage(data, ws);
                    }
                    
                    // Trigger custom event
                    this.emit('message', { name, data, ws });
                    
                } catch (error) {
                    console.error(`❌ Failed to parse WebSocket message [${name}]:`, error);
                }
            };
            
            ws.onclose = (event) => {
                console.log(`🔌 WebSocket closed [${name}]:`, event.code, event.reason);
                this.updateConnectionStatus(name, 'disconnected');
                
                // Remove from connections
                this.connections.delete(name);
                
                // Attempt reconnection for non-normal closures
                if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.scheduleReconnect(name, path, options);
                }
                
                // Trigger custom event
                this.emit('connectionClose', { name, event });
                
                if (options.onClose) options.onClose(event);
            };
            
            ws.onerror = (error) => {
                console.error(`❌ WebSocket error [${name}]:`, error);
                this.updateConnectionStatus(name, 'error');
                
                // Trigger custom event
                this.emit('connectionError', { name, error });
                
                if (options.onError) options.onError(error);
            };
            
            // Store connection
            this.connections.set(name, {
                ws,
                options,
                path,
                status: 'connecting'
            });
            
        } catch (error) {
            console.error(`❌ Failed to create WebSocket connection [${name}]:`, error);
            this.updateConnectionStatus(name, 'error');
        }
    }
    
    scheduleReconnect(name, path, options) {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
        
        console.log(`🔄 Scheduling reconnect for ${name} in ${delay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            if (this.reconnectAttempts <= this.maxReconnectAttempts) {
                this.createConnection(name, path, options);
            } else {
                console.error(`❌ Max reconnect attempts reached for ${name}`);
                this.updateConnectionStatus(name, 'failed');
            }
        }, delay);
    }
    
    send(connectionName, data) {
        const connection = this.connections.get(connectionName);
        
        if (!connection) {
            console.warn(`⚠️ Connection not found: ${connectionName}`);
            return false;
        }
        
        const { ws } = connection;
        
        if (ws.readyState === WebSocket.OPEN) {
            try {
                const message = typeof data === 'string' ? data : JSON.stringify(data);
                ws.send(message);
                console.log(`📤 Sent message to ${connectionName}:`, data);
                return true;
            } catch (error) {
                console.error(`❌ Failed to send message to ${connectionName}:`, error);
                return false;
            }
        } else {
            console.warn(`⚠️ WebSocket not ready for ${connectionName}, queueing message`);
            this.queueMessage(connectionName, data);
            return false;
        }
    }
    
    queueMessage(connectionName, data) {
        this.messageQueue.push({ connectionName, data, timestamp: Date.now() });
        
        // Clean old messages (older than 5 minutes)
        const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
        this.messageQueue = this.messageQueue.filter(msg => msg.timestamp > fiveMinutesAgo);
    }
    
    flushMessageQueue(connectionName) {
        const queuedMessages = this.messageQueue.filter(msg => msg.connectionName === connectionName);
        
        queuedMessages.forEach(({ data }) => {
            this.send(connectionName, data);
        });
        
        // Remove sent messages from queue
        this.messageQueue = this.messageQueue.filter(msg => msg.connectionName !== connectionName);
        
        if (queuedMessages.length > 0) {
            console.log(`📤 Flushed ${queuedMessages.length} queued messages for ${connectionName}`);
        }
    }
    
    broadcast(data) {
        let sentCount = 0;
        
        this.connections.forEach((connection, name) => {
            if (this.send(name, data)) {
                sentCount++;
            }
        });
        
        console.log(`📡 Broadcast message to ${sentCount}/${this.connections.size} connections`);
        return sentCount;
    }
    
    close(connectionName) {
        const connection = this.connections.get(connectionName);
        
        if (connection) {
            connection.ws.close(1000, 'Manual close');
            this.connections.delete(connectionName);
            console.log(`🔌 Manually closed connection: ${connectionName}`);
        }
    }
    
    closeAll() {
        this.connections.forEach((connection, name) => {
            connection.ws.close(1000, 'Manual close all');
        });
        
        this.connections.clear();
        console.log('🔌 All WebSocket connections closed');
    }
    
    getConnectionStatus(connectionName) {
        const connection = this.connections.get(connectionName);
        
        if (!connection) return 'not_found';
        
        switch (connection.ws.readyState) {
            case WebSocket.CONNECTING: return 'connecting';
            case WebSocket.OPEN: return 'connected';
            case WebSocket.CLOSING: return 'closing';
            case WebSocket.CLOSED: return 'closed';
            default: return 'unknown';
        }
    }
    
    getAllConnectionStatuses() {
        const statuses = {};
        
        this.connections.forEach((connection, name) => {
            statuses[name] = this.getConnectionStatus(name);
        });
        
        return statuses;
    }
    
    updateConnectionStatus(connectionName, status) {
        // Update UI indicators
        const statusElements = document.querySelectorAll(`[data-connection="${connectionName}"]`);
        statusElements.forEach(element => {
            element.className = `status-dot ${status}`;
        });
        
        // Update general WebSocket status
        if (connectionName === 'audio') {
            const wsStatusElement = document.getElementById('wsStatus');
            if (wsStatusElement) {
                wsStatusElement.className = `status-dot ${status}`;
            }
        }
    }
    
    handleCommonMessages(data, connectionName) {
        switch (data.type) {
            case 'ping':
                this.send(connectionName, { type: 'pong', timestamp: Date.now() });
                break;
                
            case 'pong':
                // Handle pong response
                break;
                
            case 'error':
                console.error(`❌ Server error [${connectionName}]:`, data.message);
                this.showNotification(data.message, 'error');
                break;
                
            case 'notification':
                this.showNotification(data.message, data.level || 'info');
                break;
                
            case 'status_update':
                this.handleStatusUpdate(data, connectionName);
                break;
                
            case 'user_count':
                this.updateUserCount(data.count);
                break;
        }
    }
    
    handleAudioMessage(data, ws) {
        switch (data.type) {
            case 'processing_started':
                this.handleProcessingStarted(data);
                break;
                
            case 'processing_progress':
                this.handleProcessingProgress(data);
                break;
                
            case 'processing_complete':
                this.handleProcessingComplete(data);
                break;
                
            case 'processing_error':
                this.handleProcessingError(data);
                break;
                
            case 'separation_result':
                this.handleSeparationResult(data);
                break;
        }
    }
    
    handleTheoryMessage(data, ws) {
        switch (data.type) {
            case 'chord_analysis':
                this.handleChordAnalysis(data);
                break;
                
            case 'scale_detection':
                this.handleScaleDetection(data);
                break;
                
            case 'rhythm_analysis':
                this.handleRhythmAnalysis(data);
                break;
        }
    }
    
    handleProcessingStarted(data) {
        console.log('🎵 Audio processing started:', data);
        this.showNotification('Audio processing started', 'info');
        
        // Show progress indicator
        this.showProcessingProgress(0, 'Initializing...');
    }
    
    handleProcessingProgress(data) {
        console.log(`📊 Processing progress: ${data.progress}% - ${data.stage}`);
        this.showProcessingProgress(data.progress, data.stage);
    }
    
    handleProcessingComplete(data) {
        console.log('✅ Audio processing complete:', data);
        this.showNotification('Audio processing completed successfully!', 'success');
        this.hideProcessingProgress();
        
        // Update UI with results
        if (data.results) {
            this.displayProcessingResults(data.results);
        }
    }
    
    handleProcessingError(data) {
        console.error('❌ Audio processing error:', data);
        this.showNotification(`Processing failed: ${data.error}`, 'error');
        this.hideProcessingProgress();
    }
    
    handleSeparationResult(data) {
        console.log('🎼 Separation result received:', data);
        
        // Update library with new separated tracks
        this.updateLibrary(data);
    }
    
    handleChordAnalysis(data) {
        console.log('🎹 Chord analysis:', data);
        // Update chord display in practice section
    }
    
    handleScaleDetection(data) {
        console.log('🎵 Scale detection:', data);
        // Update scale information in theory section
    }
    
    handleRhythmAnalysis(data) {
        console.log('🥁 Rhythm analysis:', data);
        // Update rhythm display in practice section
    }
    
    handleStatusUpdate(data, connectionName) {
        console.log(`📊 Status update [${connectionName}]:`, data.status);
        // Update relevant UI components
    }
    
    updateUserCount(count) {
        // Update user count display if needed
        const userCountElement = document.getElementById('user-count');
        if (userCountElement) {
            userCountElement.textContent = count;
        }
    }
    
    showProcessingProgress(progress, stage) {
        // Implementation depends on UI design
        console.log(`Progress: ${progress}% - ${stage}`);
    }
    
    hideProcessingProgress() {
        // Hide progress indicator
        console.log('Hiding processing progress');
    }
    
    displayProcessingResults(results) {
        // Display processing results in UI
        console.log('Displaying results:', results);
    }
    
    updateLibrary(data) {
        // Update music library with new tracks
        console.log('Updating library:', data);
    }
    
    showNotification(message, type = 'info') {
        // Use the main app's notification system
        if (window.app && window.app.showNotification) {
            window.app.showNotification(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
    
    handleConnectionError(connectionName, error) {
        console.error(`❌ Connection error [${connectionName}]:`, error);
        this.updateConnectionStatus(connectionName, 'error');
    }
    
    // Event system for external listeners
    on(event, callback) {
        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }
        this.eventListeners.get(event).push(callback);
    }
    
    off(event, callback) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            const index = listeners.indexOf(callback);
            if (index > -1) {
                listeners.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        const listeners = this.eventListeners.get(event);
        if (listeners) {
            listeners.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`❌ Error in event listener for ${event}:`, error);
                }
            });
        }
    }
    
    // Utility methods
    sendAudioCommand(command, data = {}) {
        return this.send('audio', { type: command, ...data });
    }
    
    sendTheoryCommand(command, data = {}) {
        return this.send('theory', { type: command, ...data });
    }
    
    startProcessing(projectId, options = {}) {
        return this.sendAudioCommand('start_processing', { project_id: projectId, ...options });
    }
    
    stopProcessing(projectId) {
        return this.sendAudioCommand('stop_processing', { project_id: projectId });
    }
    
    analyzeChords(audioData) {
        return this.sendTheoryCommand('analyze_chords', { audio_data: audioData });
    }
    
    detectScale(audioData) {
        return this.sendTheoryCommand('detect_scale', { audio_data: audioData });
    }
    
    // Health check
    ping(connectionName = 'audio') {
        return this.send(connectionName, { type: 'ping', timestamp: Date.now() });
    }
    
    pingAll() {
        const results = {};
        this.connections.forEach((connection, name) => {
            results[name] = this.ping(name);
        });
        return results;
    }
}

// Create global WebSocket manager instance
window.wsManager = new WebSocketManager();

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.wsManager) {
        window.wsManager.closeAll();
    }
});

// Export for external use
export default WebSocketManager;