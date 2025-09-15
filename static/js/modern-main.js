/**
 * Modern NoisyNeuron JavaScript
 * Handles theme switching, navigation, notifications, and UI interactions
 */

class NoisyNeuronApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTheme();
        this.hideLoadingScreen();
        this.initializeDropdowns();
        this.initializeNotifications();
        this.initializeMobileMenu();
        this.initializeScrollEffects();
    }

    setupEventListeners() {
        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Mobile menu toggle
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        if (mobileMenuToggle) {
            mobileMenuToggle.addEventListener('click', () => this.toggleMobileMenu());
        }

        // Alert dismissal
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-dismiss="alert"]') || e.target.closest('[data-dismiss="alert"]')) {
                const alert = e.target.closest('.alert');
                if (alert) {
                    this.dismissAlert(alert);
                }
            }
        });

        // Dropdown handling
        document.addEventListener('click', (e) => {
            const dropdownTrigger = e.target.closest('[data-dropdown-trigger]');
            if (dropdownTrigger) {
                e.preventDefault();
                this.toggleDropdown(dropdownTrigger.closest('[data-dropdown]'));
            } else if (!e.target.closest('[data-dropdown-menu]')) {
                this.closeAllDropdowns();
            }
        });

        // Escape key handling
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllDropdowns();
                this.closeMobileMenu();
            }
        });

        // Form enhancements
        this.enhanceForms();
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle icon
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const lightIcon = themeToggle.querySelector('.light-icon');
            const darkIcon = themeToggle.querySelector('.dark-icon');
            
            if (theme === 'dark') {
                lightIcon?.classList.add('hidden');
                darkIcon?.classList.remove('hidden');
            } else {
                lightIcon?.classList.remove('hidden');
                darkIcon?.classList.add('hidden');
            }
        }
    }

    hideLoadingScreen() {
        setTimeout(() => {
            const loadingScreen = document.getElementById('loading-screen');
            if (loadingScreen) {
                loadingScreen.classList.add('hidden');
                setTimeout(() => {
                    loadingScreen.style.display = 'none';
                }, 300);
            }
        }, 500);
    }

    initializeDropdowns() {
        const dropdowns = document.querySelectorAll('[data-dropdown]');
        dropdowns.forEach(dropdown => {
            const trigger = dropdown.querySelector('[data-dropdown-trigger]');
            const menu = dropdown.querySelector('[data-dropdown-menu]');
            
            if (trigger && menu) {
                trigger.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleDropdown(dropdown);
                });
            }
        });
    }

    toggleDropdown(dropdown) {
        const isActive = dropdown.classList.contains('active');
        
        // Close all other dropdowns
        this.closeAllDropdowns();
        
        // Toggle current dropdown
        if (!isActive) {
            dropdown.classList.add('active');
        }
    }

    closeAllDropdowns() {
        const activeDropdowns = document.querySelectorAll('[data-dropdown].active');
        activeDropdowns.forEach(dropdown => {
            dropdown.classList.remove('active');
        });
    }

    initializeMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        
        if (mobileMenu && mobileMenuToggle) {
            // Close mobile menu when clicking on links
            const mobileLinks = mobileMenu.querySelectorAll('a');
            mobileLinks.forEach(link => {
                link.addEventListener('click', () => {
                    this.closeMobileMenu();
                });
            });
        }
    }

    toggleMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        
        if (mobileMenu && mobileMenuToggle) {
            const isActive = mobileMenu.classList.contains('active');
            
            if (isActive) {
                this.closeMobileMenu();
            } else {
                mobileMenu.classList.add('active');
                mobileMenuToggle.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        }
    }

    closeMobileMenu() {
        const mobileMenu = document.getElementById('mobile-menu');
        const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
        
        if (mobileMenu && mobileMenuToggle) {
            mobileMenu.classList.remove('active');
            mobileMenuToggle.classList.remove('active');
            document.body.style.overflow = '';
        }
    }

    initializeScrollEffects() {
        const navbar = document.getElementById('main-navbar');
        let lastScrollY = window.scrollY;
        
        window.addEventListener('scroll', () => {
            const currentScrollY = window.scrollY;
            
            if (navbar) {
                if (currentScrollY > lastScrollY && currentScrollY > 100) {
                    // Scrolling down
                    navbar.style.transform = 'translateY(-100%)';
                } else {
                    // Scrolling up
                    navbar.style.transform = 'translateY(0)';
                }
                
                // Add background blur effect
                if (currentScrollY > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            }
            
            lastScrollY = currentScrollY;
        });
    }

    initializeNotifications() {
        this.notificationContainer = document.getElementById('notification-container');
        if (!this.notificationContainer) {
            this.notificationContainer = document.createElement('div');
            this.notificationContainer.id = 'notification-container';
            this.notificationContainer.className = 'notification-container';
            document.body.appendChild(this.notificationContainer);
        }
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible`;
        notification.innerHTML = `
            <div class="alert-content">
                <i class="fas fa-${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="alert-close" data-dismiss="alert">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.notificationContainer.appendChild(notification);

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismissAlert(notification);
            }, duration);
        }

        return notification;
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

    dismissAlert(alert) {
        alert.style.animation = 'slideOutRight 0.3s ease-out forwards';
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 300);
    }

    enhanceForms() {
        // Add floating label effects
        const formGroups = document.querySelectorAll('.form-group');
        formGroups.forEach(group => {
            const input = group.querySelector('input, textarea, select');
            const label = group.querySelector('label');
            
            if (input && label) {
                this.setupFloatingLabel(input, label);
            }
        });

        // Add form validation enhancements
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            this.enhanceFormValidation(form);
        });
    }

    setupFloatingLabel(input, label) {
        const updateLabel = () => {
            if (input.value || input === document.activeElement) {
                label.classList.add('floating');
            } else {
                label.classList.remove('floating');
            }
        };

        input.addEventListener('focus', updateLabel);
        input.addEventListener('blur', updateLabel);
        input.addEventListener('input', updateLabel);
        
        // Initial state
        updateLabel();
    }

    enhanceFormValidation(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateField(input);
            });
            
            input.addEventListener('input', () => {
                if (input.classList.contains('error')) {
                    this.validateField(input);
                }
            });
        });

        form.addEventListener('submit', (e) => {
            let isValid = true;
            
            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });

            if (!isValid) {
                e.preventDefault();
                this.showNotification('Please correct the errors in the form.', 'error');
            }
        });
    }

    validateField(input) {
        const value = input.value.trim();
        const type = input.type;
        const required = input.hasAttribute('required');
        let isValid = true;
        let errorMessage = '';

        // Clear previous error state
        input.classList.remove('error');
        const existingError = input.parentNode.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }

        // Required validation
        if (required && !value) {
            isValid = false;
            errorMessage = 'This field is required.';
        }

        // Email validation
        if (isValid && type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address.';
            }
        }

        // Password validation
        if (isValid && type === 'password' && value && input.hasAttribute('data-min-length')) {
            const minLength = parseInt(input.getAttribute('data-min-length'));
            if (value.length < minLength) {
                isValid = false;
                errorMessage = `Password must be at least ${minLength} characters long.`;
            }
        }

        // Show error if invalid
        if (!isValid) {
            input.classList.add('error');
            const errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            errorDiv.textContent = errorMessage;
            input.parentNode.appendChild(errorDiv);
        }

        return isValid;
    }

    // Utility methods
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
    }

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

    // API helper methods
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
            },
        };

        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            this.showNotification('An error occurred. Please try again.', 'error');
            throw error;
        }
    }

    getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.noisyNeuronApp = new NoisyNeuronApp();
});

// Add additional CSS animations
const additionalStyles = `
@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

.form-group {
    position: relative;
    margin-bottom: 1.5rem;
}

.form-group label {
    position: absolute;
    top: 0.75rem;
    left: 0.75rem;
    color: var(--color-text-muted);
    font-size: var(--font-size-sm);
    transition: all var(--transition-fast);
    pointer-events: none;
    z-index: 1;
}

.form-group label.floating {
    top: -0.5rem;
    left: 0.5rem;
    font-size: var(--font-size-xs);
    color: var(--color-primary);
    background: var(--color-bg-primary);
    padding: 0 0.25rem;
}

.form-group input,
.form-group textarea,
.form-group select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-md);
    font-size: var(--font-size-sm);
    transition: all var(--transition-fast);
    background: var(--color-bg-primary);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input.error,
.form-group textarea.error,
.form-group select.error {
    border-color: var(--color-error);
}

.field-error {
    color: var(--color-error);
    font-size: var(--font-size-xs);
    margin-top: 0.25rem;
}

.mobile-menu-toggle.active span:nth-child(1) {
    transform: rotate(45deg) translate(5px, 5px);
}

.mobile-menu-toggle.active span:nth-child(2) {
    opacity: 0;
}

.mobile-menu-toggle.active span:nth-child(3) {
    transform: rotate(-45deg) translate(7px, -6px);
}

.notification-container {
    position: fixed;
    top: calc(var(--navbar-height) + var(--spacing-md));
    right: var(--spacing-md);
    z-index: var(--z-toast);
    max-width: 400px;
    pointer-events: none;
}

.notification-container .alert {
    pointer-events: auto;
    margin-bottom: var(--spacing-sm);
}
`;

// Inject additional styles
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);