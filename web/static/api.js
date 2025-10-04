// API Client for Bug Tracker
class BugTrackerAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            if (typeof showLoading === 'function') showLoading();
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            if (typeof showToast === 'function') {
                showToast(error.message, 'error');
            } else {
                alert('Error: ' + error.message);
            }
            throw error;
        } finally {
            if (typeof hideLoading === 'function') hideLoading();
        }
    }

    // Projects
    async getProjects() {
        return this.request('/projects/');
    }

    async getProject(projectId) {
        return this.request(`/projects/${projectId}`);
    }

    async createProject(projectData) {
        return this.request('/projects/', {
            method: 'POST',
            body: projectData
        });
    }

    async updateProject(projectId, projectData) {
        return this.request(`/projects/${projectId}`, {
            method: 'PUT',
            body: projectData
        });
    }

    async deleteProject(projectId) {
        return this.request(`/projects/${projectId}`, {
            method: 'DELETE'
        });
    }

    async getProjectIssues(projectId) {
        return this.request(`/projects/${projectId}/issues`);
    }

    // Issues
    async getIssues(filters = {}) {
        const params = new URLSearchParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                params.append(key, value);
            }
        });
        
        const queryString = params.toString();
        return this.request(`/issues/${queryString ? '?' + queryString : ''}`);
    }

    async getIssue(issueId) {
        return this.request(`/issues/${issueId}`);
    }

    async createIssue(issueData) {
        return this.request('/issues/', {
            method: 'POST',
            body: issueData
        });
    }

    async updateIssue(issueId, issueData) {
        return this.request(`/issues/${issueId}`, {
            method: 'PUT',
            body: issueData
        });
    }

    async deleteIssue(issueId) {
        return this.request(`/issues/${issueId}`, {
            method: 'DELETE'
        });
    }

    async autoAssignIssue(issueId) {
        return this.request(`/issues/${issueId}/auto-assign`, {
            method: 'POST'
        });
    }

    async suggestTags(title, description = null, log = null) {
        const params = new URLSearchParams({ title });
        if (description) params.append('description', description);
        if (log) params.append('log', log);
        
        return this.request(`/issues/suggest-tags?${params.toString()}`, {
            method: 'POST'
        });
    }

    async searchIssues(query) {
        return this.request(`/issues/search?query=${encodeURIComponent(query)}`);
    }

    // Tags
    async getTags() {
        return this.request('/tags/');
    }

    async getTag(tagId) {
        return this.request(`/tags/${tagId}`);
    }

    async deleteTag(tagId) {
        return this.request(`/tags/${tagId}`, {
            method: 'DELETE'
        });
    }

    async renameTag(oldName, newName) {
        return this.request(`/tags/rename?old_name=${encodeURIComponent(oldName)}&new_name=${encodeURIComponent(newName)}`, {
            method: 'PATCH'
        });
    }

    async cleanupUnusedTags() {
        return this.request('/tags/cleanup', {
            method: 'DELETE'
        });
    }

    async getTagUsageStats() {
        return this.request('/tags/stats/usage');
    }
}

// Global API instance
const api = new BugTrackerAPI();
