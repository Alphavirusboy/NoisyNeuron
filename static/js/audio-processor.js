/**
 * Audio Processing UI Components
 */

class AudioProcessorUI {
    constructor() {
        this.audioContext = null;
        this.audioBuffer = null;
        this.waveformCache = new Map();
        
        this.initAudioContext();
    }
    
    async initAudioContext() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        } catch (error) {
            console.warn('Web Audio API not supported:', error);
        }
    }
    
    async generateWaveform(audioElement, canvasId, color = '#667eea') {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !audioElement) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        try {
            // Check if we have cached waveform data
            const cacheKey = audioElement.src;
            if (this.waveformCache.has(cacheKey)) {
                this.drawWaveform(ctx, this.waveformCache.get(cacheKey), width, height, color);
                return;
            }
            
            // If Web Audio API is available, generate real waveform
            if (this.audioContext && audioElement.duration) {
                await this.generateRealWaveform(audioElement, ctx, width, height, color);
            } else {
                // Fallback to mock waveform
                this.generateMockWaveform(ctx, width, height, color);
            }
        } catch (error) {
            console.warn('Waveform generation failed, using fallback:', error);
            this.generateMockWaveform(ctx, width, height, color);
        }
    }
    
    async generateRealWaveform(audioElement, ctx, width, height, color) {
        try {
            // Create audio buffer from audio element
            const response = await fetch(audioElement.src);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            // Extract audio data
            const channelData = audioBuffer.getChannelData(0);
            const samplesPerPixel = Math.floor(channelData.length / width);
            const waveformData = [];
            
            // Downsample audio data for visualization
            for (let i = 0; i < width; i++) {
                const startSample = i * samplesPerPixel;
                const endSample = startSample + samplesPerPixel;
                
                let min = 0;
                let max = 0;
                
                for (let j = startSample; j < endSample && j < channelData.length; j++) {
                    const sample = channelData[j];
                    if (sample > max) max = sample;
                    if (sample < min) min = sample;
                }
                
                waveformData.push({ min, max });
            }
            
            // Cache the waveform data
            this.waveformCache.set(audioElement.src, waveformData);
            
            // Draw the waveform
            this.drawWaveform(ctx, waveformData, width, height, color);
            
        } catch (error) {
            console.warn('Real waveform generation failed:', error);
            this.generateMockWaveform(ctx, width, height, color);
        }
    }
    
    drawWaveform(ctx, waveformData, width, height, color) {
        ctx.fillStyle = color;
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        
        const centerY = height / 2;
        const scale = height / 2;
        
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        
        for (let i = 0; i < waveformData.length; i++) {
            const x = (i / waveformData.length) * width;
            const { min, max } = waveformData[i];
            
            const yMin = centerY + (min * scale);
            const yMax = centerY + (max * scale);
            
            // Draw vertical line for each sample
            ctx.moveTo(x, yMin);
            ctx.lineTo(x, yMax);
        }
        
        ctx.stroke();
    }
    
    generateMockWaveform(ctx, width, height, color) {
        ctx.fillStyle = color;
        
        const centerY = height / 2;
        const bars = Math.min(width / 2, 150);
        const barWidth = width / bars;
        
        for (let i = 0; i < bars; i++) {
            // Generate realistic-looking waveform data
            const t = i / bars;
            const amplitude = Math.sin(t * Math.PI * 4) * Math.exp(-t * 2);
            const noise = (Math.random() - 0.5) * 0.3;
            const sample = (amplitude + noise) * 0.8;
            
            const barHeight = Math.abs(sample) * height * 0.8;
            const x = i * barWidth;
            const y = centerY - barHeight / 2;
            
            ctx.fillRect(x, y, Math.max(1, barWidth - 1), barHeight);
        }
    }
    
    visualizeProcessingSteps(canvasId, step) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        
        switch (step) {
            case 'analysis':
                this.drawSpectralAnalysis(ctx, width, height);
                break;
            case 'markov':
                this.drawMarkovVisualization(ctx, width, height);
                break;
            case 'separation':
                this.drawSeparationProcess(ctx, width, height);
                break;
            case 'enhancement':
                this.drawEnhancementProcess(ctx, width, height);
                break;
        }
    }
    
    drawSpectralAnalysis(ctx, width, height) {
        // Draw spectrogram-like visualization
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, '#ff6b6b');
        gradient.addColorStop(0.5, '#4ecdc4');
        gradient.addColorStop(1, '#45b7d1');
        
        ctx.fillStyle = gradient;
        
        for (let x = 0; x < width; x += 4) {
            for (let y = 0; y < height; y += 4) {
                const intensity = Math.random() * Math.sin((x + y) * 0.01);
                if (intensity > 0.3) {
                    ctx.globalAlpha = intensity;
                    ctx.fillRect(x, y, 3, 3);
                }
            }
        }
        
        ctx.globalAlpha = 1;
    }
    
    drawMarkovVisualization(ctx, width, height) {
        // Draw network of connected nodes
        const nodes = [];
        const numNodes = 12;
        
        // Generate nodes
        for (let i = 0; i < numNodes; i++) {
            nodes.push({
                x: Math.random() * width,
                y: Math.random() * height,
                size: 3 + Math.random() * 5
            });
        }
        
        // Draw connections
        ctx.strokeStyle = 'rgba(102, 126, 234, 0.3)';
        ctx.lineWidth = 1;
        
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[j].x - nodes[i].x;
                const dy = nodes[j].y - nodes[i].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < 100) {
                    ctx.beginPath();
                    ctx.moveTo(nodes[i].x, nodes[i].y);
                    ctx.lineTo(nodes[j].x, nodes[j].y);
                    ctx.stroke();
                }
            }
        }
        
        // Draw nodes
        ctx.fillStyle = '#667eea';
        for (const node of nodes) {
            ctx.beginPath();
            ctx.arc(node.x, node.y, node.size, 0, 2 * Math.PI);
            ctx.fill();
        }
    }
    
    drawSeparationProcess(ctx, width, height) {
        // Draw multiple waveforms representing separation
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'];
        const numWaveforms = 4;
        
        for (let w = 0; w < numWaveforms; w++) {
            ctx.strokeStyle = colors[w];
            ctx.lineWidth = 2;
            ctx.globalAlpha = 0.8;
            
            const yOffset = (height / numWaveforms) * w + (height / numWaveforms / 2);
            
            ctx.beginPath();
            ctx.moveTo(0, yOffset);
            
            for (let x = 0; x < width; x += 2) {
                const frequency = 0.05 + w * 0.02;
                const amplitude = 20 - w * 3;
                const y = yOffset + Math.sin(x * frequency) * amplitude;
                ctx.lineTo(x, y);
            }
            
            ctx.stroke();
        }
        
        ctx.globalAlpha = 1;
    }
    
    drawEnhancementProcess(ctx, width, height) {
        // Draw before/after comparison
        const centerX = width / 2;
        
        // Before (left side) - noisy
        ctx.fillStyle = 'rgba(255, 107, 107, 0.3)';
        for (let i = 0; i < 100; i++) {
            const x = Math.random() * centerX;
            const y = Math.random() * height;
            const size = Math.random() * 3;
            ctx.fillRect(x, y, size, size);
        }
        
        // After (right side) - clean
        ctx.fillStyle = 'rgba(70, 183, 209, 0.7)';
        ctx.fillRect(centerX, height * 0.3, centerX, height * 0.4);
        
        // Dividing line
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(centerX, 0);
        ctx.lineTo(centerX, height);
        ctx.stroke();
        
        // Labels
        ctx.fillStyle = '#333';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('Before', centerX / 2, 20);
        ctx.fillText('After', centerX + centerX / 2, 20);
    }
    
    createAudioVisualizer(audioElement, canvasId) {
        if (!this.audioContext || !audioElement) return;
        
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        try {
            const source = this.audioContext.createMediaElementSource(audioElement);
            const analyser = this.audioContext.createAnalyser();
            
            analyser.fftSize = 256;
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            source.connect(analyser);
            analyser.connect(this.audioContext.destination);
            
            const draw = () => {
                requestAnimationFrame(draw);
                
                analyser.getByteFrequencyData(dataArray);
                
                ctx.fillStyle = 'rgb(240, 240, 240)';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                const barWidth = (canvas.width / bufferLength) * 2.5;
                let barHeight;
                let x = 0;
                
                for (let i = 0; i < bufferLength; i++) {
                    barHeight = (dataArray[i] / 255) * canvas.height;
                    
                    const r = barHeight + 25 * (i / bufferLength);
                    const g = 250 * (i / bufferLength);
                    const b = 50;
                    
                    ctx.fillStyle = `rgb(${r},${g},${b})`;
                    ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                    
                    x += barWidth + 1;
                }
            };
            
            audioElement.addEventListener('play', () => {
                if (this.audioContext.state === 'suspended') {
                    this.audioContext.resume();
                }
                draw();
            });
            
        } catch (error) {
            console.warn('Audio visualizer setup failed:', error);
        }
    }
}

// Initialize audio processor UI
const audioProcessorUI = new AudioProcessorUI();

// Export for global access
window.audioProcessorUI = audioProcessorUI;
