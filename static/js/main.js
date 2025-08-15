// Main JavaScript for Lost & Found application

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeImagePreview();
    initializeFormValidation();
    initializeSearchFilters();
    initializeContactForm();
    initializeCardAnimations();
    initializeSmoothScrolling();
    initializeAccessibility();
    handleImageErrors();
});

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
}

// Initialize image preview functionality
function initializeImagePreview() {
    const imageInput = document.getElementById('image');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                // Check file size (16MB limit)
                if (file.size > 16 * 1024 * 1024) {
                    alert('File size must be less than 16MB');
                    this.value = '';
                    return;
                }
                
                // Check file type
                const allowedTypes = ['image/png', 'image/jpg', 'image/jpeg', 'image/gif', 'image/webp'];
                if (!allowedTypes.includes(file.type)) {
                    alert('Please select a valid image file (PNG, JPG, JPEG, GIF, or WebP)');
                    this.value = '';
                    return;
                }
                
                // Show preview if container exists
                const previewContainer = document.getElementById('imagePreview');
                if (previewContainer) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        previewContainer.innerHTML = `
                            <img src="${e.target.result}" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">
                            <p class="mt-2 mb-0 text-muted">${file.name}</p>
                        `;
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    }
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[id$="Form"]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });
}

// Form validation function
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            showFieldError(field, 'This field is required');
        } else {
            clearFieldError(field);
        }
    });
    
    // Email validation
    const emailFields = form.querySelectorAll('input[type="email"]');
    emailFields.forEach(field => {
        if (field.value && !isValidEmail(field.value)) {
            isValid = false;
            showFieldError(field, 'Please enter a valid email address');
        }
    });
    
    // Description length validation
    const descriptionField = form.querySelector('#description');
    if (descriptionField && descriptionField.value.trim().length < 10) {
        isValid = false;
        showFieldError(descriptionField, 'Please provide a more detailed description (at least 10 characters)');
    }
    
    return isValid;
}

// Show field error
function showFieldError(field, message) {
    clearFieldError(field);
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

// Clear field error
function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

// Email validation helper
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Initialize search and filter functionality
function initializeSearchFilters() {
    const filterForm = document.querySelector('form[method="GET"]');
    if (filterForm) {
        // Auto-submit on filter change
        const filterInputs = filterForm.querySelectorAll('select, input[type="text"]');
        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                // Add small delay to allow for typing
                setTimeout(() => {
                    if (this.type === 'text') {
                        // Only auto-submit if user has stopped typing for 500ms
                        clearTimeout(this.searchTimeout);
                        this.searchTimeout = setTimeout(() => {
                            filterForm.submit();
                        }, 500);
                    } else {
                        filterForm.submit();
                    }
                }, 100);
            });
        });
    }
    
    // Search functionality in navbar
    const searchForm = document.querySelector('.navbar form[role="search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="q"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                alert('Please enter a search term');
                searchInput.focus();
            }
        });
    }
}

// Initialize contact form functionality
function initializeContactForm() {
    const contactButtons = document.querySelectorAll('a[href^="mailto:"]');
    contactButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Track contact attempts (if analytics is implemented)
            if (typeof gtag !== 'undefined') {
                gtag('event', 'contact_attempt', {
                    'event_category': 'user_engagement',
                    'event_label': 'email_contact'
                });
            }
        });
    });
}

// Utility function to show loading state
function showLoading(element, text = 'Loading...') {
    const originalContent = element.innerHTML;
    element.innerHTML = `
        <span class="spinner-border spinner-border-sm me-2" role="status"></span>
        ${text}
    `;
    element.disabled = true;
    return originalContent;
}

// Utility function to hide loading state
function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
    element.disabled = false;
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// Initialize card animations
function initializeCardAnimations() {
    const cards = document.querySelectorAll('.card');
    
    // Intersection Observer for fade-in animations
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(card);
    });
}

// Initialize smooth scrolling for anchor links
function initializeSmoothScrolling() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]:not([data-bs-toggle])');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            // Skip if href is just "#" or empty
            if (!href || href === '#') {
                return;
            }
            try {
                const target = document.querySelector(href);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            } catch (error) {
                // Invalid selector - ignore
                console.warn('Invalid selector:', href);
            }
        });
    });
}

// Initialize accessibility features
function initializeAccessibility() {
    // Add skip link
    const skipLink = document.createElement('a');
    skipLink.href = '#main-content';
    skipLink.textContent = 'Skip to main content';
    skipLink.className = 'visually-hidden-focusable btn btn-primary position-absolute top-0 start-0 m-2';
    skipLink.style.zIndex = '9999';
    document.body.insertBefore(skipLink, document.body.firstChild);
    
    // Add main content ID if it doesn't exist
    const mainContent = document.querySelector('main');
    if (mainContent && !mainContent.id) {
        mainContent.id = 'main-content';
    }
}

// Error handling for images
function handleImageErrors() {
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('error', function() {
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZGRkIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCwgc2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIG5vdCBmb3VuZDwvdGV4dD48L3N2Zz4=';
            this.alt = 'Image not found';
        });
    });
}

// Initialize all features after DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeCardAnimations();
    initializeSmoothScrolling();
    initializeAccessibility();
    handleImageErrors();
});

// Export functions for potential use in other scripts
window.LostAndFound = {
    showLoading,
    hideLoading,
    formatDate,
    isValidEmail,
    validateForm
};

// Chat Bot Functionality
class ChatBot {
    constructor() {
        this.isOpen = false;
        this.isTyping = false;
        this.webhookUrl = 'http://localhost:5678/webhook/d00e7414-5d87-46fe-af20-a408c62e3e23/chat';
        this.init();
    }

    init() {
        this.bindEvents();
        this.hideBadge();
    }

    bindEvents() {
        // Toggle chat bot
        const toggle = document.getElementById('chatBotToggle');
        if (toggle) {
            toggle.addEventListener('click', () => this.toggleChat());
        }

        // Close chat bot
        const close = document.getElementById('chatBotClose');
        if (close) {
            close.addEventListener('click', () => this.closeChat());
        }

        // Send message
        const send = document.getElementById('chatBotSend');
        if (send) {
            send.addEventListener('click', () => this.sendMessage());
        }

        // Input enter key
        const input = document.getElementById('chatBotInput');
        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage();
                }
            });
        }

        // Touch events for mobile
        if (toggle) {
            toggle.addEventListener('touchstart', (e) => {
                e.preventDefault();
                this.toggleChat();
            });
        }
    }

    toggleChat() {
        const window = document.getElementById('chatBotWindow');
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }

    openChat() {
        const window = document.getElementById('chatBotWindow');
        const input = document.getElementById('chatBotInput');
        
        if (window && input) {
            window.style.display = 'flex';
            this.isOpen = true;
            input.focus();
            
            // Add open animation class
            window.classList.add('chat-open');
            
            // Hide badge when chat is opened
            this.hideBadge();
        }
    }

    closeChat() {
        const window = document.getElementById('chatBotWindow');
        if (window) {
            window.style.display = 'none';
            this.isOpen = false;
            window.classList.remove('chat-open');
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatBotInput');
        const messages = document.getElementById('chatBotMessages');
        const sendButton = document.getElementById('chatBotSend');
        
        if (!input || !messages || !sendButton) return;
        
        const message = input.value.trim();
        if (!message) return;
        
        // Disable input and send button
        input.disabled = true;
        sendButton.disabled = true;
        
        // Add user message
        this.addMessage(message, 'user');
        input.value = '';
        
        // Show typing indicator
        this.showTyping();
        
        try {
            // Send message to webhook
            const response = await this.callWebhook(message);
            
            // Hide typing indicator
            this.hideTyping();
            
            // Add bot response
            if (response && response.reply) {
                this.addMessage(response.reply, 'bot');
            } else {
                this.addMessage('I apologize, but I\'m having trouble processing your request right now. Please try again later.', 'bot');
            }
        } catch (error) {
            console.error('Chat bot error:', error);
            this.hideTyping();
            this.addMessage('I\'m sorry, but I\'m experiencing technical difficulties. Please try again later.', 'bot');
        } finally {
            // Re-enable input and send button
            input.disabled = false;
            sendButton.disabled = false;
            input.focus();
        }
    }

    async callWebhook(message) {
        try {
            const response = await fetch(this.webhookUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    timestamp: new Date().toISOString(),
                    user_agent: navigator.userAgent,
                    session_id: this.getSessionId()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Webhook call failed:', error);
            throw error;
        }
    }

    addMessage(content, type) {
        const messages = document.getElementById('chatBotMessages');
        if (!messages) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'bot') {
            contentDiv.innerHTML = `<i class="fas fa-robot me-2"></i>${this.escapeHtml(content)}`;
        } else {
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        messages.appendChild(messageDiv);
        
        // Scroll to bottom
        messages.scrollTop = messages.scrollHeight;
        
        // Auto-close chat after bot response on mobile
        if (type === 'bot' && window.innerWidth <= 576) {
            setTimeout(() => {
                if (this.isOpen) {
                    this.closeChat();
                }
            }, 3000);
        }
    }

    showTyping() {
        const messages = document.getElementById('chatBotMessages');
        if (!messages) return;
        
        this.isTyping = true;
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chat-message bot-message';
        typingDiv.id = 'typingIndicator';
        
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        
        messages.appendChild(typingDiv);
        messages.scrollTop = messages.scrollHeight;
    }

    hideTyping() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
        this.isTyping = false;
    }

    showBadge() {
        const badge = document.querySelector('.chat-bot-badge');
        if (badge) {
            badge.style.display = 'flex';
        }
    }

    hideBadge() {
        const badge = document.querySelector('.chat-bot-badge');
        if (badge) {
            badge.style.display = 'none';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getSessionId() {
        let sessionId = sessionStorage.getItem('chatBotSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            sessionStorage.setItem('chatBotSessionId', sessionId);
        }
        return sessionId;
    }

    // Method to trigger chat bot programmatically
    trigger() {
        if (!this.isOpen) {
            this.openChat();
        }
    }
}

// Initialize chat bot when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize existing features
    initializeTooltips();
    initializeImagePreview();
    initializeFormValidation();
    initializeSearchFilters();
    initializeContactForm();
    initializeCardAnimations();
    initializeSmoothScrolling();
    initializeAccessibility();
    handleImageErrors();
    
    // Initialize chat bot
    window.chatBot = new ChatBot();
    
    // Add touch event listeners for mobile devices
    const chatBotToggle = document.getElementById('chatBotToggle');
    if (chatBotToggle) {
        chatBotToggle.addEventListener('touchstart', function(e) {
            e.preventDefault();
            if (window.chatBot) {
                window.chatBot.trigger();
            }
        });
    }
});

// Export chat bot for global access
window.ChatBot = ChatBot;
