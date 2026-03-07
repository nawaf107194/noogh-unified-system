// NOOGH Dashboard API Service
// Connects React frontend to Dashboard API backend with JWT authentication

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001/api/v1';

class DashboardAPI {
    constructor() {
        this.baseURL = API_BASE_URL;
    }

    /**
     * Make authenticated API request
     * Automatically attaches JWT token from localStorage
     */
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('noogh_token');
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { 'Authorization': `Bearer ${token}` }),
                    ...options.headers,
                },
            });

            // Handle 401 Unauthorized - token expired
            if (response.status === 401) {
                localStorage.removeItem('noogh_token');
                window.location.href = '/login';
                throw new Error('Session expired');
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // ========== Auth Endpoints ==========

    async login(username, password) {
        const response = await fetch(`${this.baseURL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Login failed');
        }

        return await response.json();
    }

    async getCurrentUser() {
        return this.request('/auth/me');
    }

    // ========== System Endpoints ==========

    async getSystemStatus() {
        return this.request('/system/status');
    }

    async getSystemHealth() {
        return this.request('/system/health');
    }

    // ========== Agents Endpoints ==========

    async listAgents() {
        return this.request('/agents');
    }

    async getAgent(agentId) {
        return this.request(`/agents/${agentId}`);
    }

    // ========== Tasks Endpoints ==========

    async listTasks(params = {}) {
        const query = new URLSearchParams(params).toString();
        const endpoint = query ? `/tasks?${query}` : '/tasks';
        return this.request(endpoint);
    }

    async getTask(taskId) {
        return this.request(`/tasks/${taskId}`);
    }
}

// Export singleton instance
export const dashboardAPI = new DashboardAPI();
export default dashboardAPI;
