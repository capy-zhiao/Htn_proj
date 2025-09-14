/**
 * Data Manager Module
 * Handles all API calls, data processing, and state management
 */

class DataManager {
    constructor() {
        this.allData = { projects: [], projectSummaries: [] };
        this.filteredProjects = [];
        this.selectedProject = null;
    }

    /**
     * Load project data from API
     */
    async loadData() {
        try {
            console.log('Starting to load data...');
            const response = await fetch(CONFIG.API.PROJECTS);
            console.log('API response status:', response.status);
            
            if (!response.ok) {
                throw new Error('Failed to fetch project data');
            }
            
            const rawData = await response.json();
            console.log('Raw data loaded:', rawData);
            
            // Process the project summaries to ensure they have all expected fields
            if (rawData.projectSummaries) {
                rawData.projectSummaries = rawData.projectSummaries.map((project, index) => {
                    return this.processProjectData(project, index);
                });
            }
            
            this.allData = rawData;
            console.log('Processed data:', this.allData);
            
            this.filteredProjects = this.allData.projectSummaries || [];
            
            return this.allData;
        } catch (error) {
            console.error('Error loading data:', error);
            throw error;
        }
    }

    /**
     * Filter projects based on search criteria
     */
    filterProjects(searchQuery = '', projectFilter = 'all', typeFilter = 'all') {
        const query = searchQuery.toLowerCase();
        
        this.filteredProjects = this.allData.projectSummaries.filter(project => {
            const matchesSearch = !query || 
                (project.title && project.title.toLowerCase().includes(query)) ||
                (project.summary && project.summary.toLowerCase().includes(query)) ||
                (project.projectName && project.projectName.toLowerCase().includes(query)) ||
                (project.tags && project.tags.some(tag => tag.toLowerCase().includes(query)));

            const matchesProject = projectFilter === 'all' || project.projectName === projectFilter;
            const matchesType = typeFilter === 'all' || project.type === typeFilter;

            return matchesSearch && matchesProject && matchesType;
        });

        return this.filteredProjects;
    }

    /**
     * Get filtered projects
     */
    getFilteredProjects() {
        return this.filteredProjects;
    }

    /**
     * Get all projects
     */
    getAllProjects() {
        return this.allData.projects;
    }

    /**
     * Select a project
     */
    selectProject(project) {
        this.selectedProject = project;
        return this.selectedProject;
    }

    /**
     * Get selected project
     */
    getSelectedProject() {
        return this.selectedProject;
    }

    /**
     * Convert tag to type
     */
    getTypeFromTag(tag) {
        return CONFIG.TYPE_MAPPINGS[tag] || 'Other';
    }

    /**
     * Extract function-related content from conversation
     * Improved to filter out technical noise and focus on meaningful features
     */
    extractFunctions(data) {
        const functions = [];
        const messages = data.messages || [];
        
        // Patterns to exclude (technical noise)
        const excludePatterns = [
            /function_calls/i,
            /antml:function_calls/i,
            /antml:invoke/i,
            /parameter name/i,
            /parameter>/i,
            /invoke name/i,
            /result>/i,
            /output>/i,
            /<[^>]+>/g, // Any XML/HTML tags
            /\{[^}]*\}/g, // JSON-like structures
            /^\s*[-•]\s*$/, // Just bullet points
            /^\s*\d+\|\s*/, // Line numbers
        ];
        
        // Keywords that indicate actual features/functionality
        const featureKeywords = [
            'added', 'implemented', 'created', 'built', 'developed',
            'enhanced', 'improved', 'updated', 'modified', 'refactored',
            'feature', 'functionality', 'component', 'module', 'system'
        ];
        
        for (const msg of messages) {
            const content = msg.content || '';
            
            // Skip if message contains too much technical noise
            const noiseCount = excludePatterns.reduce((count, pattern) => {
                return count + (content.match(pattern) || []).length;
            }, 0);
            
            if (noiseCount > 3) continue; // Skip very technical messages
            
            if (featureKeywords.some(keyword => content.toLowerCase().includes(keyword))) {
                // Split by sentences and filter
                const sentences = content.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 10);
                
                for (const sentence of sentences) {
                    // Check if sentence contains feature keywords and isn't technical noise
                    const hasFeatureKeyword = featureKeywords.some(keyword => 
                        sentence.toLowerCase().includes(keyword)
                    );
                    
                    const isTechnicalNoise = excludePatterns.some(pattern => 
                        pattern.test && pattern.test(sentence)
                    );
                    
                    if (hasFeatureKeyword && !isTechnicalNoise && sentence.length < 150) {
                        // Clean up the sentence
                        let cleanSentence = sentence
                            .replace(/^\s*[-•*]\s*/, '') // Remove bullet points
                            .replace(/^\d+\.\s*/, '') // Remove numbered lists
                            .replace(/\s+/g, ' ') // Normalize whitespace
                            .trim();
                        
                        if (cleanSentence.length > 15 && !functions.includes(cleanSentence)) {
                            functions.push(cleanSentence);
                        }
                    }
                }
            }
        }
        
        return functions.slice(0, CONFIG.UI.MAX_FUNCTIONS_DISPLAY);
    }

    /**
     * Extract bug fix related content from conversation
     * Improved to filter out technical noise and focus on meaningful fixes
     */
    extractBugFixes(data) {
        const bugFixes = [];
        const messages = data.messages || [];
        
        // Patterns to exclude (technical noise)
        const excludePatterns = [
            /function_calls/i,
            /antml:function_calls/i,
            /antml:invoke/i,
            /parameter name/i,
            /parameter>/i,
            /invoke name/i,
            /result>/i,
            /output>/i,
            /<[^>]+>/g, // Any XML/HTML tags
            /\{[^}]*\}/g, // JSON-like structures
            /^\s*[-•]\s*$/, // Just bullet points
            /^\s*\d+\|\s*/, // Line numbers
        ];
        
        // Keywords that indicate actual bug fixes
        const bugFixKeywords = [
            'fixed', 'resolved', 'corrected', 'repaired', 'debugged',
            'solved', 'addressed', 'patched', 'bug', 'error', 'issue'
        ];
        
        for (const msg of messages) {
            const content = msg.content || '';
            
            // Skip if message contains too much technical noise
            const noiseCount = excludePatterns.reduce((count, pattern) => {
                return count + (content.match(pattern) || []).length;
            }, 0);
            
            if (noiseCount > 3) continue; // Skip very technical messages
            
            if (bugFixKeywords.some(keyword => content.toLowerCase().includes(keyword))) {
                // Split by sentences and filter
                const sentences = content.split(/[.!?]+/).map(s => s.trim()).filter(s => s.length > 10);
                
                for (const sentence of sentences) {
                    // Check if sentence contains bug fix keywords and isn't technical noise
                    const hasBugFixKeyword = bugFixKeywords.some(keyword => 
                        sentence.toLowerCase().includes(keyword)
                    );
                    
                    const isTechnicalNoise = excludePatterns.some(pattern => 
                        pattern.test && pattern.test(sentence)
                    );
                    
                    if (hasBugFixKeyword && !isTechnicalNoise && sentence.length < 150) {
                        // Clean up the sentence
                        let cleanSentence = sentence
                            .replace(/^\s*[-•*]\s*/, '') // Remove bullet points
                            .replace(/^\d+\.\s*/, '') // Remove numbered lists
                            .replace(/\s+/g, ' ') // Normalize whitespace
                            .trim();
                        
                        if (cleanSentence.length > 15 && !bugFixes.includes(cleanSentence)) {
                            bugFixes.push(cleanSentence);
                        }
                    }
                }
            }
        }
        
        return bugFixes.slice(0, CONFIG.UI.MAX_BUG_FIXES_DISPLAY);
    }

    /**
     * Extract tags from data
     */
    extractTags(data) {
        const tags = [];
        const tag = data.tag || '';
        const description = data.description || data.summary || '';
        
        // Add tag
        if (tag && tag !== 'other') {
            tags.push(tag.replace(' ', '-'));
        }
        
        // Extract keywords from description
        if (description) {
            const keywords = description.toLowerCase().split(' ');
            for (const keyword of keywords) {
                if (keyword.length > 3 && !tags.includes(keyword) && tags.length < CONFIG.UI.MAX_TAGS_DISPLAY) {
                    tags.push(keyword);
                }
            }
        }
        
        // Add some default tags based on message types if available
        if (data.messages && Array.isArray(data.messages)) {
            const messageTypes = [...new Set(data.messages.map(m => m.type).filter(Boolean))];
            messageTypes.forEach(type => {
                if (type && !tags.includes(type) && tags.length < CONFIG.UI.MAX_TAGS_DISPLAY) {
                    tags.push(type);
                }
            });
        }
        
        return tags.slice(0, CONFIG.UI.MAX_TAGS_DISPLAY);
    }

    /**
     * Format code changes
     */
    formatCodeChanges(beforeCode, afterCode) {
        if (!beforeCode && !afterCode) {
            return '// No code changes detected';
        }
        
        let result = '';
        
        if (beforeCode) {
            result += '// Before:\n' + beforeCode + '\n\n';
        }
        
        if (afterCode) {
            result += '// After:\n' + afterCode;
        }
        
        return result;
    }

    /**
     * Generate impact description
     */
    generateImpactDescription(tag, description) {
        return CONFIG.IMPACT_DESCRIPTIONS[tag] || 'Had a positive impact on project development';
    }

    /**
     * Process raw project data into formatted project summary
     */
    processProjectData(data, index) {
        // Extract code changes from messages if not present at top level
        let before_code = data.before_code;
        let after_code = data.after_code;
        let codeChanges = '';
        
        if (data.messages && Array.isArray(data.messages)) {
            const codeBlocks = [];
            for (const msg of data.messages) {
                if (msg.code_changes) {
                    codeBlocks.push(msg.code_changes);
                }
                if (msg.before_code && !before_code) {
                    before_code = msg.before_code;
                }
                if (msg.after_code && !after_code) {
                    after_code = msg.after_code;
                }
            }
            if (codeBlocks.length > 0) {
                codeChanges = codeBlocks.join('\n\n');
            }
        }
        
        return {
            id: data.conversation_id || data.id || `project-${index + 1}`,
            projectName: data.project_name || data.projectName || CONFIG.DEFAULTS.UNKNOWN_PROJECT,
            title: data.title || `Update ${index + 1}`,
            summary: data.summary || data.description || '',
            type: this.getTypeFromTag(data.tag || 'other'),
            timestamp: data.created_at || data.timestamp || new Date().toISOString(),
            aiModel: data.ai_model || CONFIG.DEFAULTS.AI_MODEL,
            functions: this.extractFunctions(data),
            bugFixes: this.extractBugFixes(data),
            tags: this.extractTags(data),
            codeChanges: codeChanges || this.formatCodeChanges(before_code || '', after_code || ''),
            before_code: before_code || null,
            after_code: after_code || null,
            impact: this.generateImpactDescription(data.tag || 'other', data.description || data.summary || ''),
            messageCount: data.message_count || data.messageCount || (data.messages ? data.messages.length : 0),
            participants: data.participants || ['User', 'AI'],
            messages: data.messages || []  // Include the original messages array!
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DataManager;
} else {
    window.DataManager = DataManager;
}
