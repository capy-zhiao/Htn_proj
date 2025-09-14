/**
 * UI Components Module
 * Handles rendering of all UI components
 */

class UIComponents {
    constructor(dataManager) {
        this.dataManager = dataManager;
    }

    /**
     * Render the projects list in the sidebar
     */
    renderProjects() {
        const projectsList = UIUtils.getElementById(CONFIG.ELEMENTS.PROJECTS_LIST);
        if (!projectsList) return;

        UIUtils.clearElement(projectsList);
        const projects = this.dataManager.getAllProjects();

        projects.forEach(project => {
            const projectDiv = UIUtils.createElement('div',
                'flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors hover:bg-gray-50'
            );

            projectDiv.innerHTML = `
                <div class="flex items-center gap-2">
                    <i data-lucide="folder-open" class="w-4 h-4 text-gray-400"></i>
                    <div>
                        <div class="text-sm font-medium">${UIUtils.escapeHtml(project.name)}</div>
                        <div class="text-xs text-gray-500">${UIUtils.escapeHtml(project.status)}</div>
                    </div>
                </div>
                <span class="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                    ${project.updates}
                </span>
            `;

            UIUtils.addEventListenerSafe(projectDiv, 'click', () => {
                const projectFilter = UIUtils.getElementById(CONFIG.ELEMENTS.PROJECT_FILTER);
                if (projectFilter) {
                    projectFilter.value = project.name;
                    this.handleFilterChange();
                }
            });

            projectsList.appendChild(projectDiv);
        });

        UIUtils.initializeIcons();
    }

    /**
     * Render the updates list
     */
    renderUpdates() {
        const updatesList = UIUtils.getElementById(CONFIG.ELEMENTS.UPDATES_LIST);
        const updateCount = UIUtils.getElementById(CONFIG.ELEMENTS.UPDATE_COUNT);

        if (!updatesList || !updateCount) return;

        const filteredProjects = this.dataManager.getFilteredProjects();
        const selectedProject = this.dataManager.getSelectedProject();

        updateCount.textContent = filteredProjects.length;
        UIUtils.clearElement(updatesList);

        filteredProjects.forEach(project => {
            const updateDiv = UIUtils.createElement('div');
            const isSelected = selectedProject?.id === project.id;

            updateDiv.className = `p-4 cursor-pointer transition-colors ${isSelected ? CONFIG.CSS_CLASSES.SELECTED_PROJECT : CONFIG.CSS_CLASSES.HOVER_EFFECT
                }`;

            updateDiv.innerHTML = `
                <div class="mb-2">
                    <h3 class="text-sm font-medium text-gray-900 ${CONFIG.CSS_CLASSES.LINE_CLAMP_2}">
                        ${UIUtils.escapeHtml(project.title)}
                    </h3>
                    <p class="text-xs text-gray-600 mt-1 ${CONFIG.CSS_CLASSES.LINE_CLAMP_1}">
                        ${UIUtils.renderMarkdown(project.summary)}
                    </p>
                </div>
                
                <div class="flex items-center gap-2 text-xs mb-2">
                    <span class="bg-gray-100 px-2 py-1 rounded flex items-center gap-1">
                        <i data-lucide="folder-open" class="w-3 h-3"></i>
                        ${UIUtils.escapeHtml(project.projectName)}
                    </span>
                    <span class="px-2 py-1 rounded flex items-center gap-1 ${UIUtils.getTypeColor(project.type)}">
                        ${UIUtils.getTypeIcon(project.type)}
                        ${UIUtils.escapeHtml(project.type)}
                    </span>
                    ${(project.before_code && project.after_code) ? `
                        <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded flex items-center gap-1" title="Contains before/after code changes">
                            <i data-lucide="git-compare" class="w-3 h-3"></i>
                            Diff
                        </span>
                    ` : ''}
                </div>
                
                <div class="flex items-center justify-between text-xs text-gray-500">
                    <div class="flex items-center gap-1">
                        <i data-lucide="calendar" class="w-3 h-3"></i>
                        ${project.timestamp ? UIUtils.formatTimestamp(project.timestamp) : 'Unknown'}
                    </div>
                    <div class="flex items-center gap-1">
                        <i data-lucide="message-square" class="w-3 h-3"></i>
                        ${UIUtils.escapeHtml(project.aiModel || 'AI')}
                    </div>
                </div>
            `;

            UIUtils.addEventListenerSafe(updateDiv, 'click', () => {
                this.selectProject(project);
            });

            updatesList.appendChild(updateDiv);
        });

        UIUtils.initializeIcons();
    }

    /**
     * Render the detail view for selected project
     */
    renderDetailView() {
        const selectedProject = this.dataManager.getSelectedProject();
        const detailView = UIUtils.getElementById(CONFIG.ELEMENTS.DETAIL_VIEW);

        if (!detailView) return;

        if (!selectedProject) {
            detailView.innerHTML = `
                <div class="flex items-center justify-center h-full text-gray-500">
                    <div class="text-center">
                        <i data-lucide="folder-open" class="w-12 h-12 mx-auto mb-4 text-gray-300"></i>
                        <p class="text-lg font-medium mb-2">Select a project update to view details</p>
                        <p class="text-sm">Browse your project summaries and AI-generated insights</p>
                    </div>
                </div>
            `;
            UIUtils.initializeIcons();
            return;
        }

        detailView.innerHTML = `
            <!-- Header Section -->
            <div class="border-b border-gray-200 pb-6 mb-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex-1">
                        <h1 class="text-2xl font-bold text-gray-900 mb-3 leading-tight">
                            ${UIUtils.escapeHtml(selectedProject.title)}
                        </h1>
                        <div class="flex items-center gap-3 mb-4">
                            <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium">
                                <i data-lucide="folder-open" class="w-4 h-4"></i>
                                ${UIUtils.escapeHtml(selectedProject.projectName)}
                            </span>
                            <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${UIUtils.getTypeColor(selectedProject.type)}">
                                ${UIUtils.getTypeIcon(selectedProject.type)}
                                ${UIUtils.escapeHtml(selectedProject.type)}
                            </span>
                            ${(selectedProject.before_code && selectedProject.after_code) ? `
                                <span class="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-100 text-blue-800 rounded-lg text-sm font-medium">
                                    <i data-lucide="git-compare" class="w-4 h-4"></i>
                                    Code Changes
                                </span>
                            ` : ''}
                        </div>
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-500">
                        <i data-lucide="calendar" class="w-4 h-4"></i>
                        ${selectedProject.timestamp ? UIUtils.formatTimestamp(selectedProject.timestamp) : 'Unknown'}
                    </div>
                </div>
                
                <!-- Tags -->
                ${(selectedProject.tags || []).length > 0 ? `
                    <div class="flex flex-wrap gap-2">
                        ${selectedProject.tags.map(tag => `
                            <span class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                                <i data-lucide="tag" class="w-3 h-3"></i>
                                ${UIUtils.escapeHtml(tag)}
                            </span>
                        `).join('')}
                    </div>
                ` : ''}
            </div>

            <!-- Main Content -->
            <div class="space-y-8">
                <!-- Summary Section -->
                <div class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 bg-blue-100 rounded-lg">
                            <i data-lucide="file-text" class="w-5 h-5 text-blue-600"></i>
                        </div>
                        <h2 class="text-xl font-semibold text-gray-900">Conversation Summary</h2>
                    </div>
                    <div class="prose prose-sm max-w-none">
                        ${UIUtils.formatSummaryParagraphs(selectedProject.summary)}
                    </div>
                </div>

                ${this.renderCodeChangesSection(selectedProject)}

                <!-- Features and Fixes Grid -->
                <div class="grid lg:grid-cols-2 gap-6">
                    <!-- Features Section -->
                    <div class="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-xl p-6">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="p-2 bg-green-100 rounded-lg">
                                <i data-lucide="plus-circle" class="w-5 h-5 text-green-600"></i>
                            </div>
                            <h3 class="text-lg font-semibold text-gray-900">New Features</h3>
                        </div>
                        ${(selectedProject.functions || []).length > 0 ? `
                            <div class="space-y-3">
                                ${selectedProject.functions.map(func => `
                                    <div class="flex items-start gap-3 p-3 bg-white/60 rounded-lg border border-green-100">
                                        <div class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                                        <p class="text-sm text-gray-700 leading-relaxed">${UIUtils.escapeHtml(func)}</p>
                                    </div>
                                `).join('')}
                            </div>
                        ` : `
                            <div class="text-center py-8">
                                <i data-lucide="search" class="w-8 h-8 text-green-300 mx-auto mb-3"></i>
                                <p class="text-sm text-green-600 font-medium">No specific features identified</p>
                                <p class="text-xs text-green-500 mt-1">This conversation may focus on other aspects</p>
                            </div>
                        `}
                    </div>

                    <!-- Bug Fixes Section -->
                    <div class="bg-gradient-to-br from-red-50 to-rose-50 border border-red-200 rounded-xl p-6">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="p-2 bg-red-100 rounded-lg">
                                <i data-lucide="bug" class="w-5 h-5 text-red-600"></i>
                            </div>
                            <h3 class="text-lg font-semibold text-gray-900">Bug Fixes</h3>
                        </div>
                        ${(selectedProject.bugFixes || []).length > 0 ? `
                            <div class="space-y-3">
                                ${selectedProject.bugFixes.map(fix => `
                                    <div class="flex items-start gap-3 p-3 bg-white/60 rounded-lg border border-red-100">
                                        <div class="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                                        <p class="text-sm text-gray-700 leading-relaxed">${UIUtils.escapeHtml(fix)}</p>
                                    </div>
                                `).join('')}
                            </div>
                        ` : `
                            <div class="text-center py-8">
                                <i data-lucide="check-circle" class="w-8 h-8 text-red-300 mx-auto mb-3"></i>
                                <p class="text-sm text-red-600 font-medium">No specific bug fixes identified</p>
                                <p class="text-xs text-red-500 mt-1">This conversation may focus on other aspects</p>
                            </div>
                        `}
                    </div>
                </div>

                <!-- Impact Section -->
                <div class="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 bg-purple-100 rounded-lg">
                            <i data-lucide="trending-up" class="w-5 h-5 text-purple-600"></i>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900">Impact & Results</h3>
                    </div>
                    <p class="text-gray-700 leading-relaxed">${UIUtils.escapeHtml(selectedProject.impact)}</p>
                </div>

                <!-- Conversation Stats -->
                <div class="bg-gray-50 border border-gray-200 rounded-xl p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 bg-gray-100 rounded-lg">
                            <i data-lucide="bar-chart-3" class="w-5 h-5 text-gray-600"></i>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900">Conversation Details</h3>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center p-4 bg-white rounded-lg border border-gray-100">
                            <div class="text-2xl font-bold text-gray-900">${selectedProject.messageCount || 0}</div>
                            <div class="text-sm text-gray-500 mt-1">Messages</div>
                        </div>
                        <div class="text-center p-4 bg-white rounded-lg border border-gray-100">
                            <div class="text-2xl font-bold text-gray-900">${(selectedProject.participants || []).length}</div>
                            <div class="text-sm text-gray-500 mt-1">Participants</div>
                        </div>
                        <div class="text-center p-4 bg-white rounded-lg border border-gray-100">
                            <div class="text-2xl font-bold text-gray-900">${(selectedProject.tags || []).length}</div>
                            <div class="text-sm text-gray-500 mt-1">Tags</div>
                        </div>
                        <div class="text-center p-4 bg-white rounded-lg border border-gray-100">
                            <div class="text-2xl font-bold text-blue-600">
                                <i data-lucide="message-square" class="w-6 h-6 mx-auto"></i>
                            </div>
                            <div class="text-sm text-gray-500 mt-1">${UIUtils.escapeHtml(selectedProject.aiModel || 'AI')}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        UIUtils.initializeIcons();
    }

    /**
     * Update filter options
     */
    updateFilters() {
        const projectFilter = UIUtils.getElementById(CONFIG.ELEMENTS.PROJECT_FILTER);
        if (!projectFilter) return;

        projectFilter.innerHTML = '<option value="all">All Projects</option>';

        const projects = this.dataManager.getAllProjects();
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.name;
            option.textContent = project.name;
            projectFilter.appendChild(option);
        });
    }

    /**
     * Select a project and update UI
     */
    selectProject(project) {
        this.dataManager.selectProject(project);
        this.renderDetailView();
        this.renderUpdates(); // Re-render to update selected state
    }

    /**
     * Render the code changes section with message-by-message display
     * Only shows messages that contain code changes
     */
    renderCodeChangesSection(project) {
        // Ensure project is defined and has the expected properties
        if (!project || !project.messages) {
            return '';
        }

        // Filter messages to show ONLY those with code changes
        const allMessages = project.messages || [];
        const codeMessages = allMessages.filter(msg => this.hasCodeContent(msg));

        if (codeMessages.length === 0) {
            return `
                <div class="bg-white border border-gray-200 rounded-xl p-6">
                    <div class="flex items-center gap-3 mb-4">
                        <div class="p-2 bg-gray-100 rounded-lg">
                            <i data-lucide="code" class="w-5 h-5 text-gray-500"></i>
                        </div>
                        <h3 class="text-lg font-semibold text-gray-900">Code Changes</h3>
                    </div>
                    <div class="text-center py-8">
                        <i data-lucide="file-code" class="w-12 h-12 text-gray-300 mx-auto mb-4"></i>
                        <p class="text-gray-500 font-medium">No code changes found</p>
                        <p class="text-sm text-gray-400 mt-1">This conversation doesn't contain any code modifications</p>
                    </div>
                </div>
            `;
        }

        const timelineId = `timeline-${Date.now()}`;

        return `
            <div class="bg-white border border-gray-200 rounded-xl p-6">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex items-center gap-3">
                        <div class="p-2 bg-blue-100 rounded-lg">
                            <i data-lucide="code" class="w-5 h-5 text-blue-600"></i>
                        </div>
                        <div>
                            <h3 class="text-lg font-semibold text-gray-900">Code Changes Timeline</h3>
                            <p class="text-sm text-gray-500">${codeMessages.length} message${codeMessages.length > 1 ? 's' : ''} with code changes (filtered from ${allMessages.length} total)</p>
                        </div>
                    </div>
                    
                    <!-- Expand/Collapse Button -->
                    <button 
                        onclick="window.toggleTimeline('${timelineId}')" 
                        class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors duration-200"
                        id="toggle-${timelineId}"
                    >
                        <span class="toggle-text">Show Details</span>
                        <i data-lucide="chevron-down" class="w-4 h-4 toggle-icon transition-transform duration-200"></i>
                    </button>
                </div>
                
                <!-- Collapsible Timeline Content -->
                <div id="${timelineId}" class="timeline-content hidden">
                    <div class="space-y-4">
                        ${codeMessages.map((msg, index) => this.renderSingleMessage(msg, index, true)).join('')}
                    </div>
                </div>
                
                <!-- Collapsed Summary -->
                <div id="${timelineId}-summary" class="timeline-summary">
                    <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <div class="flex items-center gap-2 mb-2">
                            <i data-lucide="info" class="w-4 h-4 text-blue-600"></i>
                            <span class="text-sm font-medium text-blue-800">Timeline Summary</span>
                        </div>
                        <p class="text-sm text-blue-700">
                            ${codeMessages.length} code change${codeMessages.length > 1 ? 's' : ''} recorded in this conversation. 
                            Click "Show Details" above to view the complete timeline with code diffs.
                        </p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Check if a message has any code content
     */
    hasCodeContent(message) {
        // Check for direct code fields
        if (message.before_code || message.after_code || message.code_changes) {
            return true;
        }

        // Check for code blocks in message content
        if (message.content && message.content.includes('```')) {
            return true;
        }

        return false;
    }

    /**
     * Render a single message in the timeline
     */
    renderSingleMessage(message, index, isCodeFiltered = false) {
        const messageTime = message.timestamp ? UIUtils.formatTimestamp(message.timestamp) : `Message ${index + 1}`;
        const messageType = message.type || 'message';

        // Extract any code from the message
        let codeBlocks = [];

        // Check for direct code fields
        if (message.before_code || message.after_code) {
            if (message.before_code && message.after_code) {
                codeBlocks.push({
                    type: 'before-after',
                    before: message.before_code,
                    after: message.after_code
                });
            } else if (message.before_code) {
                codeBlocks.push({
                    type: 'before',
                    code: message.before_code
                });
            } else if (message.after_code) {
                codeBlocks.push({
                    type: 'after',
                    code: message.after_code
                });
            }
        } else if (message.code_changes) {
            codeBlocks.push({
                type: 'code',
                code: message.code_changes
            });
        }

        // Also check for code in message content
        if (message.content && message.content.includes('```')) {
            const contentCodeBlocks = message.content.match(/```[\s\S]*?```/g);
            if (contentCodeBlocks) {
                contentCodeBlocks.forEach(block => {
                    const cleanCode = block.replace(/```\w*\n?/, '').replace(/```$/, '').trim();
                    if (cleanCode) {
                        codeBlocks.push({
                            type: 'content',
                            code: cleanCode
                        });
                    }
                });
            }
        }

        // Get message type icon and color
        const typeInfo = this.getMessageTypeInfo(messageType);

        return `
            <div class="border border-gray-200 rounded-lg bg-white shadow-sm">
                <!-- Message Header -->
                <div class="px-4 py-3 border-b border-gray-100 ${isCodeFiltered ? 'bg-blue-50' : 'bg-gray-50'}">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full ${isCodeFiltered ? 'bg-blue-100' : typeInfo.bgColor} flex items-center justify-center">
                                <i data-lucide="${isCodeFiltered ? 'code' : typeInfo.icon}" class="w-4 h-4 ${isCodeFiltered ? 'text-blue-600' : typeInfo.textColor}"></i>
                            </div>
                            <div>
                                <span class="font-medium text-gray-900">${isCodeFiltered ? 'Code Change' : 'Message'} ${index + 1}</span>
                                ${!isCodeFiltered ? `
                                    <span class="ml-2 px-2 py-1 ${typeInfo.bgColor} ${typeInfo.textColor} text-xs rounded-full font-medium">
                                        ${messageType}
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-medium ${isCodeFiltered ? 'text-blue-600' : 'text-gray-900'}">${messageTime}</div>
                            ${isCodeFiltered ? '<div class="text-xs text-blue-500">Code Modified</div>' : ''}
                        </div>
                    </div>
                </div>
                
                <!-- Message Content -->
                <div class="p-4">
                    ${!isCodeFiltered && message.content ? `
                        <div class="mb-4">
                            <h4 class="text-sm font-medium text-gray-700 mb-2">Message Content:</h4>
                            <div class="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-700 max-h-32 overflow-y-auto">
                                ${UIUtils.escapeHtml(message.content.substring(0, 300))}${message.content.length > 300 ? '...' : ''}
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Code Blocks -->
                    ${codeBlocks.length > 0 ? `
                        <div class="space-y-4">
                            <h4 class="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <i data-lucide="code" class="w-4 h-4"></i>
                                ${isCodeFiltered ? 'Code Changes:' : 'Code in this message:'}
                            </h4>
                            ${codeBlocks.map((codeBlock, codeIndex) => this.renderCodeBlock(codeBlock, codeIndex)).join('')}
                        </div>
                    ` : `
                        <div class="text-center py-4 text-gray-500 text-sm">
                            <i data-lucide="message-square" class="w-8 h-8 mx-auto mb-2 text-gray-300"></i>
                            No code found in this message
                        </div>
                    `}
                </div>
            </div>
        `;
    }

    /**
     * Get message type styling information
     */
    getMessageTypeInfo(type) {
        const typeMap = {
            'code-change': {
                icon: 'code',
                bgColor: 'bg-blue-100',
                textColor: 'text-blue-800'
            },
            'question': {
                icon: 'help-circle',
                bgColor: 'bg-purple-100',
                textColor: 'text-purple-800'
            },
            'discussion': {
                icon: 'message-circle',
                bgColor: 'bg-green-100',
                textColor: 'text-green-800'
            },
            'clarification': {
                icon: 'info',
                bgColor: 'bg-yellow-100',
                textColor: 'text-yellow-800'
            },
            'unknown': {
                icon: 'message-square',
                bgColor: 'bg-gray-100',
                textColor: 'text-gray-800'
            }
        };

        return typeMap[type] || typeMap['unknown'];
    }

    /**
     * Render a single code block
     */
    renderCodeBlock(codeBlock, index) {
        // Map colors to full Tailwind classes (no string-building)
        const palette = {
            red: { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', btnBg: 'bg-red-100', btnText: 'text-red-700', hover: 'hover:bg-red-200' },
            green: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', btnBg: 'bg-green-100', btnText: 'text-green-700', hover: 'hover:bg-green-200' },
            blue: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200', btnBg: 'bg-blue-100', btnText: 'text-blue-700', hover: 'hover:bg-blue-200' },
            gray: { bg: 'bg-gray-50', text: 'text-gray-700', border: 'border-gray-200', btnBg: 'bg-gray-100', btnText: 'text-gray-700', hover: 'hover:bg-gray-200' },
        };

        const block = (label, colorKey, icon, code) => {
            const c = palette[colorKey] || palette.gray;
            const jsString = JSON.stringify(String(code ?? "")); // safe for JS context
            return `
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="${c.bg} px-3 py-2 text-sm font-medium ${c.text} ${c.border} flex items-center justify-between">
          <span class="flex items-center gap-1">
            <i data-lucide="${icon}" class="w-3 h-3"></i>${label}
          </span>
          <button class="text-xs px-2 py-1 ${c.btnBg} ${c.btnText} rounded ${c.hover}"
                  onclick='UIUtils.copyToClipboard(${jsString})'>
            Copy
          </button>
        </div>
        <pre class="p-3 text-sm text-gray-800 font-mono leading-relaxed overflow-x-auto max-h-64 overflow-y-auto bg-white"><code>${UIUtils.escapeHtml(code ?? "")}</code></pre>
      </div>`;
        };

        if (codeBlock.type === 'before-after') {
            return `
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <div class="bg-gray-100 px-3 py-2 text-sm font-medium text-gray-700 border-b border-gray-200">
          Before & After Comparison
        </div>
        <div class="grid md:grid-cols-2 gap-0">
          <div class="border-r border-gray-200">
            ${block('Before', 'red', 'minus-circle', codeBlock.before)}
          </div>
          <div>
            ${block('After', 'green', 'plus-circle', codeBlock.after)}
          </div>
        </div>
      </div>`;
        }

        // Single block
        const meta = {
            'before': { label: 'Before Code', color: 'red', icon: 'minus-circle' },
            'after': { label: 'After Code', color: 'green', icon: 'plus-circle' },
            'code': { label: 'Code Changes', color: 'blue', icon: 'code' },
            'content': { label: 'Code Block', color: 'gray', icon: 'file-code' },
        }[codeBlock.type] || { label: 'Code Block', color: 'gray', icon: 'file-code' };

        return block(meta.label, meta.color, meta.icon, codeBlock.code);
    }

    /**
     * Handle filter changes
     */
    handleFilterChange() {
        const searchQuery = UIUtils.getElementById(CONFIG.ELEMENTS.SEARCH_INPUT)?.value || '';
        const projectFilter = UIUtils.getElementById(CONFIG.ELEMENTS.PROJECT_FILTER)?.value || 'all';
        const typeFilter = UIUtils.getElementById(CONFIG.ELEMENTS.TYPE_FILTER)?.value || 'all';

        this.dataManager.filterProjects(searchQuery, projectFilter, typeFilter);
        this.renderUpdates();
    }
}

// Global function for timeline toggle (accessible from onclick)
window.toggleTimeline = function (timelineId) {
    const content = document.getElementById(timelineId);
    const summary = document.getElementById(`${timelineId}-summary`);
    const toggleButton = document.getElementById(`toggle-${timelineId}`);
    const toggleText = toggleButton?.querySelector('.toggle-text');
    const toggleIcon = toggleButton?.querySelector('.toggle-icon');

    if (!content || !summary || !toggleButton) return;

    const isExpanded = !content.classList.contains('hidden');

    if (isExpanded) {
        // Collapse
        content.classList.add('hidden');
        summary.classList.remove('hidden');
        toggleText.textContent = 'Show Details';
        toggleIcon.style.transform = 'rotate(0deg)';
    } else {
        // Expand
        content.classList.remove('hidden');
        summary.classList.add('hidden');
        toggleText.textContent = 'Hide Details';
        toggleIcon.style.transform = 'rotate(180deg)';

        // Re-initialize icons for the newly shown content
        if (typeof UIUtils !== 'undefined') {
            UIUtils.initializeIcons();
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIComponents;
} else {
    window.UIComponents = UIComponents;
}

