const fs = require('fs').promises;
const path = require('path');
const { validateResponse, cleanResponse } = require('./schemas');

/**
 * Loads and processes prompt templates from markdown files
 */
class PromptLoader {
    constructor(promptsDir = path.join(__dirname)) {
        this.promptsDir = promptsDir;
        this.cache = {};
    }

    /**
     * Load a prompt template from file
     * @param {string} name - Name of the prompt file (without .md extension)
     * @returns {Promise<string>} The prompt template content
     */
    async loadPrompt(name) {
        // Check cache first
        if (this.cache[name]) {
            return this.cache[name];
        }

        const filepath = path.join(this.promptsDir, `${name}.md`);
        const content = await fs.readFile(filepath, 'utf-8');

        // Cache for future use
        this.cache[name] = content;
        return content;
    }

    /**
     * Load and format a prompt with variable substitution
     * @param {string} name - Name of the prompt file
     * @param {Object} variables - Variables to substitute in the template
     * @returns {Promise<string>} The formatted prompt
     */
    async formatPrompt(name, variables = {}) {
        let template = await this.loadPrompt(name);

        // Replace variables in template
        Object.entries(variables).forEach(([key, value]) => {
            const regex = new RegExp(`\\{${key}\\}`, 'g');
            template = template.replace(regex, value || '');
        });

        return template;
    }

    /**
     * Clear the prompt cache
     */
    clearCache() {
        this.cache = {};
    }

    /**
     * Format conversation history for prompts
     * @param {Array} qaHistory - Array of Q&A objects
     * @param {number} limit - Maximum number of Q&As to include
     * @returns {string} Formatted Q&A history
     */
    formatQAHistory(qaHistory, limit = null) {
        if (!qaHistory || qaHistory.length === 0) {
            return 'No previous Q&A - this is the initial discovery';
        }

        const items = limit ? qaHistory.slice(-limit) : qaHistory;
        return items
            .map((qa, index) => `Q${index + 1}: ${qa.question}\nA${index + 1}: ${qa.answer}`)
            .join('\n\n');
    }

    /**
     * Format entity list for prompts
     * @param {Object} entities - Entities object from graph
     * @returns {string} Formatted entity list
     */
    formatEntities(entities) {
        if (!entities || Object.keys(entities).length === 0) {
            return 'No entities defined yet';
        }

        return Object.entries(entities)
            .map(([type, items]) => `${type}: ${Object.keys(items).join(', ')}`)
            .join('\n');
    }

    /**
     * Format connections for prompts
     * @param {Array} connections - Array of connection objects
     * @param {number} limit - Maximum number to show
     * @returns {string} Formatted connections
     */
    formatConnections(connections, limit = 10) {
        if (!connections || connections.length === 0) {
            return 'No connections defined yet';
        }

        return connections
            .slice(0, limit)
            .map(edge => `${edge.from} → ${edge.to}`)
            .join('\n');
    }

    /**
     * Calculate entity count
     * @param {Object} entities - Entities object from graph
     * @returns {number} Total number of entities
     */
    countEntities(entities) {
        if (!entities) return 0;
        return Object.values(entities).reduce((sum, type) => sum + Object.keys(type).length, 0);
    }

    /**
     * Validate and clean AI response
     * @param {string} schemaName - Name of the schema to validate against
     * @param {object} data - Response data to validate
     * @returns {object} Validation result with cleaned data
     */
    validateAndClean(schemaName, data) {
        // Clean the data first
        const cleanedData = cleanResponse(schemaName, data);

        // Validate against schema
        const validation = validateResponse(schemaName, cleanedData);

        return {
            data: cleanedData,
            isValid: validation.isValid,
            errors: validation.errors
        };
    }
}

module.exports = PromptLoader;