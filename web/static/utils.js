// Utility functions for Bug Tracker frontend

// Loading spinner
function showLoading() {
    document.getElementById('loading-spinner').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-spinner').classList.add('hidden');
}

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="flex justify-between items-center">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="text-muted">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Auto remove after duration
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, duration);
}

// Modal management
let currentModalAction = null;

function showModal(title, body, confirmText = 'Confirm', onConfirm = null) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = body;
    document.getElementById('modal-confirm').textContent = confirmText;
    document.getElementById('modal-overlay').classList.remove('hidden');
    currentModalAction = onConfirm;
}

function closeModal() {
    document.getElementById('modal-overlay').classList.add('hidden');
    currentModalAction = null;
}

function confirmAction() {
    if (currentModalAction) {
        currentModalAction();
    }
    closeModal();
}

// Form validation
function validateForm(formElement) {
    const errors = {};
    const inputs = formElement.querySelectorAll('[required]');
    
    inputs.forEach(input => {
        const value = input.value.trim();
        const fieldName = input.name || input.id;
        
        if (!value) {
            errors[fieldName] = 'This field is required';
        } else {
            // Specific validations
            if (input.type === 'email' && !isValidEmail(value)) {
                errors[fieldName] = 'Please enter a valid email address';
            }
            
            if (input.hasAttribute('minlength') && value.length < parseInt(input.getAttribute('minlength'))) {
                errors[fieldName] = `Minimum length is ${input.getAttribute('minlength')} characters`;
            }
            
            if (input.hasAttribute('maxlength') && value.length > parseInt(input.getAttribute('maxlength'))) {
                errors[fieldName] = `Maximum length is ${input.getAttribute('maxlength')} characters`;
            }
        }
        
        // Clear previous errors
        const errorElement = input.parentElement.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }
        input.classList.remove('error');
    });
    
    // Display errors
    Object.entries(errors).forEach(([fieldName, message]) => {
        const input = formElement.querySelector(`[name="${fieldName}"], #${fieldName}`);
        if (input) {
            input.classList.add('error');
            const errorElement = document.createElement('div');
            errorElement.className = 'form-error';
            errorElement.textContent = message;
            input.parentElement.appendChild(errorElement);
        }
    });
    
    return Object.keys(errors).length === 0;
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// Date formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function formatRelativeDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 30) return `${days}d ago`;
    
    return formatDate(dateString);
}

// Status and priority styling
function getStatusBadgeClass(status) {
    const statusMap = {
        'open': 'badge-warning',
        'in_progress': 'badge-primary',
        'closed': 'badge-success'
    };
    return statusMap[status] || 'badge-secondary';
}

function getPriorityClass(priority) {
    const priorityMap = {
        'high': 'priority-high',
        'medium': 'priority-medium',
        'low': 'priority-low'
    };
    return priorityMap[priority] || '';
}

function getPriorityIcon(priority) {
    const iconMap = {
        'high': 'fas fa-arrow-up',
        'medium': 'fas fa-minus',
        'low': 'fas fa-arrow-down'
    };
    return iconMap[priority] || 'fas fa-minus';
}

// Navigation
function setActivePage(pageName) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[data-page="${pageName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
}

// Tag management utilities
class TagManager {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            placeholder: 'Add tags...',
            suggestions: [],
            ...options
        };
        this.tags = [];
        this.init();
    }
    
    init() {
        this.container.innerHTML = `
            <div class="tag-input-container">
                <div class="tags-display"></div>
                <input type="text" class="tag-input" placeholder="${this.options.placeholder}">
            </div>
            <div class="tag-suggestions hidden"></div>
        `;
        
        this.input = this.container.querySelector('.tag-input');
        this.display = this.container.querySelector('.tags-display');
        this.suggestionsContainer = this.container.querySelector('.tag-suggestions');
        
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('blur', () => {
            setTimeout(() => this.hideSuggestions(), 200);
        });
    }
    
    handleKeydown(e) {
        if (e.key === 'Enter' || e.key === ',') {
            e.preventDefault();
            this.addTag(this.input.value.trim());
        } else if (e.key === 'Backspace' && !this.input.value && this.tags.length > 0) {
            this.removeTag(this.tags.length - 1);
        }
    }
    
    handleInput(e) {
        const value = e.target.value.trim();
        if (value && this.options.suggestions.length > 0) {
            this.showSuggestions(value);
        } else {
            this.hideSuggestions();
        }
    }
    
    addTag(tagName) {
        if (tagName && !this.tags.includes(tagName)) {
            this.tags.push(tagName);
            this.updateDisplay();
            this.input.value = '';
            this.hideSuggestions();
            
            if (this.options.onChange) {
                this.options.onChange(this.tags);
            }
        }
    }
    
    removeTag(index) {
        this.tags.splice(index, 1);
        this.updateDisplay();
        
        if (this.options.onChange) {
            this.options.onChange(this.tags);
        }
    }
    
    updateDisplay() {
        this.display.innerHTML = this.tags.map((tag, index) => `
            <span class="tag-item">
                ${tag}
                <button type="button" class="tag-remove" onclick="tagManager.removeTag(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </span>
        `).join('');
    }
    
    showSuggestions(query) {
        const filtered = this.options.suggestions.filter(tag => 
            tag.toLowerCase().includes(query.toLowerCase()) && !this.tags.includes(tag)
        );
        
        if (filtered.length > 0) {
            this.suggestionsContainer.innerHTML = filtered.map(tag => `
                <div class="tag-suggestion" onclick="tagManager.addTag('${tag}')">${tag}</div>
            `).join('');
            this.suggestionsContainer.classList.remove('hidden');
        } else {
            this.hideSuggestions();
        }
    }
    
    hideSuggestions() {
        this.suggestionsContainer.classList.add('hidden');
    }
    
    setTags(tags) {
        this.tags = [...tags];
        this.updateDisplay();
    }
    
    getTags() {
        return [...this.tags];
    }
}

// Data formatting utilities
function truncateText(text, maxLength = 50) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// URL utilities
function updateURLParams(params) {
    const url = new URL(window.location);
    Object.entries(params).forEach(([key, value]) => {
        if (value) {
            url.searchParams.set(key, value);
        } else {
            url.searchParams.delete(key);
        }
    });
    history.replaceState(null, '', url);
}

function getURLParams() {
    const params = {};
    new URLSearchParams(window.location.search).forEach((value, key) => {
        params[key] = value;
    });
    return params;
}

// Debounce function for search
function debounce(func, wait) {
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

// Global event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Set active navigation based on current path
    const path = window.location.pathname;
    if (path === '/') {
        setActivePage('dashboard');
    } else if (path.includes('projects')) {
        setActivePage('projects');
    } else if (path.includes('issues')) {
        setActivePage('issues');
    } else if (path.includes('tags')) {
        setActivePage('tags');
    }
    
    // Close modal when clicking overlay
    document.getElementById('modal-overlay').addEventListener('click', function(e) {
        if (e.target === this) {
            closeModal();
        }
    });
    
    // Handle escape key for modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
});

// Chart utilities
function createChart(canvasId, type, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: type,
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...options
        }
    });
}
