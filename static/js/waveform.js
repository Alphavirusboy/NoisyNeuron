/**
 * Waveform visualization utilities
 */

class WaveformGenerator {
    constructor() {
        this.cache = new Map();
    }
    
    generateHeroWaveform() {
        const canvas = document.getElementById('heroWaveform');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        this.animateHeroWaveform(ctx, width, height);
    }
    
    animateHeroWaveform(ctx, width, height) {
        let time = 0;
        
        const animate = () => {
            ctx.clearRect(0, 0, width, height);
            
            // Create gradient
            const gradient = ctx.createLinearGradient(0, 0, 0, height);
            gradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
            gradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.6)');
            gradient.addColorStop(1, 'rgba(255, 255, 255, 0.4)');
            
            ctx.fillStyle = gradient;
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.lineWidth = 2;
            
            // Draw animated waveform
            const centerY = height / 2;
            const amplitude = height * 0.3;
            const frequency = 0.01;
            const speed = 0.02;
            
            ctx.beginPath();
            ctx.moveTo(0, centerY);
            
            for (let x = 0; x < width; x += 2) {
                const y1 = centerY + Math.sin(x * frequency + time) * amplitude * 0.5;
                const y2 = centerY + Math.sin(x * frequency * 1.5 + time * 1.3) * amplitude * 0.3;
                const y3 = centerY + Math.sin(x * frequency * 0.7 + time * 0.8) * amplitude * 0.2;
                
                const y = (y1 + y2 + y3) / 3;
                
                ctx.lineTo(x, y);
            }
            
            ctx.stroke();
            
            // Draw bars
            const numBars = 50;
            const barWidth = width / numBars;
            
            for (let i = 0; i < numBars; i++) {
                const x = i * barWidth;
                const barHeight = Math.abs(
                    Math.sin(i * 0.3 + time) * 
                    Math.sin(i * 0.1 + time * 0.7) * 
                    amplitude
                );
                
                const y = centerY - barHeight / 2;
                
                ctx.globalAlpha = 0.6;
                ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
            }
            
            ctx.globalAlpha = 1;
            time += speed;
            
            requestAnimationFrame(animate);
        };
        
        animate();
    }
    
    generateStaticWaveform(canvasId, data = null, color = '#667eea') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;
        
        ctx.clearRect(0, 0, width, height);
        
        if (data) {
            this.drawDataWaveform(ctx, data, width, height, color);
        } else {
            this.drawMockWaveform(ctx, width, height, color);
        }
    }
    
    drawDataWaveform(ctx, data, width, height, color) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        
        const centerY = height / 2;
        const scaleY = height * 0.4;
        
        ctx.beginPath();
        ctx.moveTo(0, centerY);
        
        for (let i = 0; i < data.length; i++) {
            const x = (i / data.length) * width;
            const y = centerY + (data[i] * scaleY);
            ctx.lineTo(x, y);
        }
        
        ctx.stroke();
    }
    
    drawMockWaveform(ctx, width, height, color) {
        ctx.fillStyle = color;
        
        const numBars = Math.floor(width / 3);
        const barWidth = width / numBars;
        const centerY = height / 2;
        
        for (let i = 0; i < numBars; i++) {
            // Create realistic audio waveform pattern
            const t = i / numBars;
            const envelope = Math.exp(-Math.pow(t - 0.5, 2) * 8); // Gaussian envelope
            const wave = Math.sin(t * Math.PI * 20) * envelope;
            const noise = (Math.random() - 0.5) * 0.2;
            const amplitude = (wave + noise) * 0.8;
            
            const barHeight = Math.abs(amplitude) * height * 0.8;
            const x = i * barWidth;
            const y = centerY - barHeight / 2;
            
            ctx.fillRect(x, y, Math.max(1, barWidth - 0.5), barHeight);
        }
    }
    
    generateMultiTrackWaveforms(containerSelector, tracks) {
        const container = document.querySelector(containerSelector);
        if (!container) return;
        
        tracks.forEach((track, index) => {
            const canvas = document.createElement('canvas');
            canvas.width = 300;
            canvas.height = 60;
            canvas.className = 'track-waveform';
            canvas.dataset.track = track.name;
            
            container.appendChild(canvas);
            
            const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'];
            const color = colors[index % colors.length];
            
            this.generateStaticWaveform(canvas.id, track.data, color);
        });
    }
    
    createInteractiveWaveform(canvasId, audioElement) {
        const canvas = document.getElementById(canvasId);
        if (!canvas || !audioElement) return;
        
        const ctx = canvas.getContext('2d');
        let isDragging = false;
        
        // Draw initial waveform
        this.generateStaticWaveform(canvasId);
        
        // Add progress indicator
        const drawProgress = () => {
            if (!audioElement.duration) return;
            
            const progress = audioElement.currentTime / audioElement.duration;
            const x = progress * canvas.width;
            
            // Redraw waveform
            this.generateStaticWaveform(canvasId);
            
            // Draw progress line
            ctx.strokeStyle = '#ff6b6b';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, canvas.height);
            ctx.stroke();
        };
        
        // Update progress during playback
        audioElement.addEventListener('timeupdate', drawProgress);
        
        // Click to seek
        canvas.addEventListener('click', (e) => {
            if (!audioElement.duration) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const progress = x / canvas.width;
            
            audioElement.currentTime = progress * audioElement.duration;
        });
        
        // Drag to seek
        canvas.addEventListener('mousedown', (e) => {
            isDragging = true;
            canvas.style.cursor = 'grabbing';
        });
        
        canvas.addEventListener('mousemove', (e) => {
            if (!isDragging || !audioElement.duration) return;
            
            const rect = canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const progress = Math.max(0, Math.min(1, x / canvas.width));
            
            audioElement.currentTime = progress * audioElement.duration;
        });
        
        document.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                canvas.style.cursor = 'pointer';
            }
        });
        
        canvas.style.cursor = 'pointer';
    }
}

// Initialize waveform generator
const waveformGenerator = new WaveformGenerator();

// Generate hero waveform on load
document.addEventListener('DOMContentLoaded', () => {
    waveformGenerator.generateHeroWaveform();
});

// Export for global access
window.waveformGenerator = waveformGenerator;
