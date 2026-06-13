const API_BASE = '/api/v1';

class ApiService {
    static async request(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `API Error: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`[API Error] ${endpoint}:`, error);
            throw error;
        }
    }

    static async getStatus() {
        return this.request('/status');
    }

    static async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/upload', {
            method: 'POST',
            body: formData
        });
    }

    static async query(text, sessionId = null, topK = 50, topN = 5) {
        const body = { query: text, top_k: topK, top_n: topN };
        if (sessionId) {
            body.session_id = sessionId;
        }
        return this.request('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
    }

    static async queryStream(text, sessionId = null, topK = 50, topN = 5, onMetadata, onToken, onDone, onError) {
        const body = { query: text, top_k: topK, top_n: topN };
        if (sessionId) {
            body.session_id = sessionId;
        }
        try {
            const response = await fetch(`${API_BASE}/query/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `API Error: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    const cleanLine = line.trim();
                    if (!cleanLine) continue;
                    if (!cleanLine.startsWith('data: ')) continue;

                    const dataStr = cleanLine.substring(6);
                    if (dataStr === '[DONE]') {
                        if (onDone) onDone();
                        return;
                    }

                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'metadata') {
                            if (onMetadata) onMetadata(data);
                        } else if (data.type === 'token') {
                            if (onToken) onToken(data.content);
                        }
                    } catch (e) {
                        console.error('Failed to parse SSE line:', cleanLine, e);
                    }
                }
            }
        } catch (error) {
            console.error('[API Error] /query/stream:', error);
            if (onError) onError(error);
        }
    }

    static async getSessions() {
        return this.request('/sessions');
    }

    static async getSessionMessages(sessionId) {
        return this.request(`/sessions/${sessionId}/messages`);
    }

    static async deleteSession(sessionId) {
        return this.request(`/sessions/${sessionId}`, {
            method: 'DELETE'
        });
    }

    static async renameSession(sessionId, title) {
        return this.request(`/sessions/${sessionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title })
        });
    }
}

export default ApiService;
