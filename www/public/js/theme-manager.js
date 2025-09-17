/**
 * Theme Manager for Lucid Commander
 * Handles dynamic theme switching between Dark, JIRA, and Corporate themes
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'wireframe'; // Default theme
        this.themeStorageKey = 'lucid-commander-theme';
        this.init();
    }

    init() {
        // Load saved theme preference
        this.loadSavedTheme();

        // Apply the theme
        this.applyTheme(this.currentTheme);

        // Setup event listeners
        this.setupEventListeners();

        // Update selector to match current theme
        this.updateThemeSelector();

        console.log(`Theme Manager initialized with theme: ${this.currentTheme}`);
    }

    setupEventListeners() {
        const themeSelector = document.getElementById('theme-select');
        if (themeSelector) {
            themeSelector.addEventListener('change', (e) => {
                this.switchTheme(e.target.value);
            });
        } else {
            console.warn('Theme selector not found, retrying in 1 second...');
            setTimeout(() => this.setupEventListeners(), 1000);
        }
    }

    switchTheme(themeName) {
        if (this.isValidTheme(themeName)) {
            // Add transition class for smooth switching
            document.body.classList.add('theme-transitioning');

            // Apply new theme
            this.applyTheme(themeName);
            this.currentTheme = themeName;

            // Save preference
            this.saveThemePreference(themeName);

            // Remove transition class after a brief delay
            setTimeout(() => {
                document.body.classList.remove('theme-transitioning');
            }, 200);

            // Trigger theme change event for other components
            this.triggerThemeChangeEvent(themeName);

            console.log(`Theme switched to: ${themeName}`);
        } else {
            console.error(`Invalid theme: ${themeName}`);
        }
    }

    applyTheme(themeName) {
        const htmlElement = document.documentElement;

        // Remove any existing theme data attributes
        htmlElement.removeAttribute('data-theme');

        // Apply new theme
        htmlElement.setAttribute('data-theme', themeName);

        // Update any dynamic font imports for professional themes
        this.updateFonts(themeName);
    }

    updateFonts(themeName) {
        const existingCorpFont = document.getElementById('corporate-fonts');

        if (themeName === 'corporate' || themeName === 'jira') {
            // Load professional fonts if not already loaded
            if (!existingCorpFont) {
                const link = document.createElement('link');
                link.id = 'corporate-fonts';
                link.rel = 'stylesheet';
                link.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap';
                document.head.appendChild(link);
            }
        } else {
            // Remove professional fonts for dark theme
            if (existingCorpFont) {
                existingCorpFont.remove();
            }
        }
    }

    loadSavedTheme() {
        try {
            const savedTheme = localStorage.getItem(this.themeStorageKey);
            if (savedTheme && this.isValidTheme(savedTheme)) {
                this.currentTheme = savedTheme;
            }
        } catch (error) {
            console.warn('Could not load saved theme preference:', error);
        }
    }

    saveThemePreference(themeName) {
        try {
            localStorage.setItem(this.themeStorageKey, themeName);
        } catch (error) {
            console.warn('Could not save theme preference:', error);
        }
    }

    updateThemeSelector() {
        const themeSelector = document.getElementById('theme-select');
        if (themeSelector) {
            themeSelector.value = this.currentTheme;
        }
    }

    isValidTheme(themeName) {
        const validThemes = ['wireframe', 'dark', 'jira', 'corporate'];
        return validThemes.includes(themeName);
    }

    triggerThemeChangeEvent(themeName) {
        // Dispatch custom event for other components to react to theme changes
        const event = new CustomEvent('themeChanged', {
            detail: {
                theme: themeName,
                previousTheme: this.currentTheme
            }
        });
        document.dispatchEvent(event);
    }

    getCurrentTheme() {
        return this.currentTheme;
    }

    // Public method to programmatically switch themes
    setTheme(themeName) {
        this.switchTheme(themeName);
        this.updateThemeSelector();
    }

    // Get theme-specific configuration
    getThemeConfig() {
        const configs = {
            wireframe: {
                name: 'Wireframe Dark',
                description: 'Flat minimalist wireframe design',
                primaryColor: '#FFFFFF',
                background: '#0A0A0A',
                category: 'Minimal'
            },
            dark: {
                name: 'Dark Theme',
                description: 'Futuristic dark theme with robotic aesthetics',
                primaryColor: '#0076FE',
                background: 'rgba(18, 18, 20, 1)',
                category: 'Technical'
            },
            jira: {
                name: 'JIRA Professional',
                description: 'Clean, task-oriented design inspired by JIRA',
                primaryColor: '#0052cc',
                background: '#fafbfc',
                category: 'Professional'
            },
            corporate: {
                name: 'Corporate Clean',
                description: 'Modern corporate theme with light blue-grey tones',
                primaryColor: '#4a90c2',
                background: '#f8f9fa',
                category: 'Enterprise'
            }
        };

        return configs[this.currentTheme] || configs.wireframe;
    }

    // Auto-detect preferred theme based on system preferences
    detectSystemTheme() {
        if (window.matchMedia) {
            if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
                return 'wireframe';
            } else {
                return 'corporate'; // Light corporate theme for light system preference
            }
        }
        return 'wireframe'; // Fallback
    }

    // Initialize with system preference if no saved preference exists
    initWithSystemPreference() {
        if (!localStorage.getItem(this.themeStorageKey)) {
            const systemTheme = this.detectSystemTheme();
            this.setTheme(systemTheme);
        }
    }
}

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();

    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            console.log('System theme preference changed:', e.matches ? 'dark' : 'light');
            // Optionally auto-switch themes based on system preference
            // window.themeManager.setTheme(e.matches ? 'dark' : 'corporate');
        });
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}