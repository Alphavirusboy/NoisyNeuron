// Main Application Controller
class NoisyNeuronApp {
    constructor() {
        this.currentSection = 'dashboard';
        this.userProgress = {
            guitar: { level: 3, songsLearned: 42, chordsKnown: 156 },
            piano: { level: 2, songsLearned: 18, chordsKnown: 89 }
        };
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupFloatingActionButton();
        this.loadUserProgress();
        this.initializeServices();
    }

    initializeServices() {
        // Initialize all service modules
        if (window.musicTheory) {
            console.log('Music Theory Engine initialized');
        }
        if (window.practiceToolkit) {
            console.log('Practice Toolkit initialized');
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
        
        // Section-specific initialization
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
            case 'community':
                this.initializeCommunitySection();
                break;
        }
    }

    setupFloatingActionButton() {
        const fab = document.getElementById('mainFab');
        const fabMenu = document.getElementById('fabMenu');
        
        if (fab && fabMenu) {
            fab.addEventListener('click', () => {
                fabMenu.classList.toggle('active');
            });

            // Close FAB menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!fab.contains(e.target) && !fabMenu.contains(e.target)) {
                    fabMenu.classList.remove('active');
                }
            });

            // FAB menu item handlers
            fabMenu.querySelectorAll('.fab-item').forEach(item => {
                item.addEventListener('click', (e) => {
                    const action = e.currentTarget.dataset.action;
                    this.handleFabAction(action);
                    fabMenu.classList.remove('active');
                });
            });
        }
    }

    handleFabAction(action) {
        switch (action) {
            case 'upload':
                this.navigateToSection('separate');
                setTimeout(() => {
                    document.getElementById('fileSelectBtn')?.click();
                }, 300);
                break;
            case 'practice':
                this.navigateToSection('practice');
                break;
            case 'tune':
                if (window.practiceToolkit?.tuner) {
                    window.practiceToolkit.tuner.toggle();
                }
                break;
        }
    }

    refreshDashboard() {
        this.updateProgressStats();
        this.updateRecentActivity();
        this.updateSkillLevels();
    }

    updateProgressStats() {
        // Update dashboard statistics
        const totalSongs = Object.values(this.userProgress)
            .reduce((sum, instrument) => sum + instrument.songsLearned, 0);
        const totalChords = Object.values(this.userProgress)
            .reduce((sum, instrument) => sum + instrument.chordsKnown, 0);
        
        const songsStat = document.querySelector('.stat-number');
        const chordsStat = document.querySelectorAll('.stat-number')[1];
        
        if (songsStat) songsStat.textContent = totalSongs;
        if (chordsStat) chordsStat.textContent = totalChords;
    }

    updateRecentActivity() {
        // This would typically load from server
        // For now, we'll use mock data
        const activities = [
            {
                icon: 'fas fa-music',
                text: 'Practiced "Wonderwall" on guitar',
                time: '2 hours ago'
            },
            {
                icon: 'fas fa-waveform',
                text: 'Separated "Bohemian Rhapsody"',
                time: '5 hours ago'
            },
            {
                icon: 'fas fa-trophy',
                text: 'Achieved 90% accuracy on C major',
                time: '1 day ago'
            }
        ];

        const activityList = document.querySelector('.activity-list');
        if (activityList) {
            activityList.innerHTML = activities.map(activity => `
                <div class="activity-item">
                    <i class="${activity.icon}"></i>
                    <div>
                        <span>${activity.text}</span>
                        <small>${activity.time}</small>
                    </div>
                </div>
            `).join('');
        }
    }

    updateSkillLevels() {
        Object.entries(this.userProgress).forEach(([instrument, progress]) => {
            const skillElement = document.querySelector(`[data-instrument="${instrument}"] .skill-fill`);
            if (skillElement) {
                const percentage = (progress.level / 5) * 100;
                skillElement.style.width = `${percentage}%`;
            }
        });
    }

    initializeLearningSection() {
        console.log('Initializing learning section');
        // The MusicTheoryEngine handles most of this
    }

    initializeSeparationSection() {
        console.log('Initializing separation section');
        // The SongAnalyzer handles file uploads and processing
    }

    initializePracticeSection() {
        console.log('Initializing practice section');
        // The PracticeToolkit handles practice tools
    }

    initializeCommunitySection() {
        this.loadCommunityPosts();
    }

    loadCommunityPosts() {
        // Mock community posts
        const posts = [
            {
                user: 'GuitarHero123',
                content: 'Just learned my first barre chord! Thanks to the chord substitution feature.',
                time: '3 hours ago',
                likes: 12
            },
            {
                user: 'PianoNewbie',
                content: 'The metronome feature is amazing for keeping tempo!',
                time: '6 hours ago',
                likes: 8
            },
            {
                user: 'MusicTeacher',
                content: 'Using this app to help my students learn chord progressions.',
                time: '1 day ago',
                likes: 25
            }
        ];

        const postList = document.querySelector('.post-list');
        if (postList) {
            postList.innerHTML = posts.map(post => `
                <div class="community-post">
                    <div class="post-header">
                        <div class="post-user">
                            <img src="https://via.placeholder.com/32" alt="${post.user}" class="user-avatar">
                            <span class="username">${post.user}</span>
                        </div>
                        <span class="post-time">${post.time}</span>
                    </div>
                    <div class="post-content">
                        <p>${post.content}</p>
                    </div>
                    <div class="post-actions">
                        <button class="like-btn">
                            <i class="fas fa-heart"></i>
                            <span>${post.likes}</span>
                        </button>
                        <button class="comment-btn">
                            <i class="fas fa-comment"></i>
                            Reply
                        </button>
                    </div>
                </div>
            `).join('');
        }
    }

    loadUserProgress() {
        // This would typically load from server
        // For now, we'll use localStorage or default values
        const savedProgress = localStorage.getItem('userProgress');
        if (savedProgress) {
            this.userProgress = JSON.parse(savedProgress);
        }
    }

    saveUserProgress() {
        localStorage.setItem('userProgress', JSON.stringify(this.userProgress));
    }

    // Utility methods
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
                <span>${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.parentNode.removeChild(notification);
        });
    }

    // Public API methods for other modules
    updateUserProgress(instrument, field, value) {
        if (!this.userProgress[instrument]) {
            this.userProgress[instrument] = { level: 1, songsLearned: 0, chordsKnown: 0 };
        }
        
        this.userProgress[instrument][field] = value;
        this.saveUserProgress();
        
        if (this.currentSection === 'dashboard') {
            this.refreshDashboard();
        }
    }

    addPracticeSession(sessionData) {
        // Add to recent activity
        const activityList = document.querySelector('.activity-list');
        if (activityList) {
            const newActivity = document.createElement('div');
            newActivity.className = 'activity-item';
            newActivity.innerHTML = `
                <i class="fas fa-music"></i>
                <div>
                    <span>Practiced ${sessionData.song || 'chord exercises'}</span>
                    <small>Just now</small>
                </div>
            `;
            activityList.insertBefore(newActivity, activityList.firstChild);
        }
    }
}

// Audio processing utilities
class AudioProcessor {
    constructor() {
        this.isProcessing = false;
    }

    async separateAudio(file, options = {}) {
        if (this.isProcessing) {
            throw new Error('Audio processing already in progress');
        }

        this.isProcessing = true;
        
        try {
            const formData = new FormData();
            formData.append('audio_file', file);
            
            // Add separation options
            Object.entries(options).forEach(([key, value]) => {
                formData.append(key, value);
            });

            const response = await fetch('/api/audio/process/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
            
        } finally {
            this.isProcessing = false;
        }
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

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    window.app = new NoisyNeuronApp();
    window.audioProcessor = new AudioProcessor();
    
    console.log('NoisyNeuron app initialized successfully!');
});

// Export for testing and debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { NoisyNeuronApp, AudioProcessor };
}
