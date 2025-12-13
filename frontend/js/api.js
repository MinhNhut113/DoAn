// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Token management
// frontend/js/api.js - Dòng 5-15
function getToken() {
    return localStorage.getItem('auth_token');  
}

function setToken(token) {
    localStorage.setItem('auth_token', token);  
}

function removeToken() {
    localStorage.removeItem('auth_token');  
}

function isAuthenticated() {
    return !!getToken();
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (token) {
        // FIX: Remove "Bearer " prefix if already present to prevent "Bearer Bearer token"
        const cleanToken = token.replace(/^Bearer\s+/i, '');
        defaultOptions.headers['Authorization'] = `Bearer ${cleanToken}`;
    }
    
    const config = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        
        if (response.status === 401) {
            removeToken();
            redirectTo('../index.html');
            throw new Error('Unauthorized');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Request Error:', error);
        throw error;
    }
}

// Auth API
const authAPI = {
    async register(userData) {
        return apiRequest('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    },
    
    async login(credentials) {
        const data = await apiRequest('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        });
        
        if (data.token) {
            setToken(data.token);
        }
        
        return data;
    },
    
    async getProfile() {
        return apiRequest('/auth/profile');
    },
    
    async updateProfile(updates) {
        return apiRequest('/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }
};

// Courses API
const coursesAPI = {
    async getAll(enrolled = false) {
        const query = enrolled ? '?enrolled=true' : '';
        return apiRequest(`/courses${query}`);
    },
    
    async getById(courseId) {
        return apiRequest(`/courses/${courseId}`);
    },
    
    async enroll(courseId) {
        return apiRequest(`/courses/${courseId}/enroll`, {
            method: 'POST'
        });
    },
    
    async getLessons(courseId) {
        return apiRequest(`/courses/${courseId}/lessons`);
    }
};

// Lessons API
const lessonsAPI = {
    async getById(lessonId) {
        return apiRequest(`/lessons/${lessonId}`);
    },
    
    async markComplete(lessonId) {
        return apiRequest(`/lessons/${lessonId}/complete`, {
            method: 'POST'
        });
    }
};

// Quizzes API
const quizzesAPI = {
    async getQuizzes(filters = {}) {
        const params = new URLSearchParams(filters);
        return apiRequest(`/quizzes?${params}`);
    },
    
    async getQuiz(quizId) {
        return apiRequest(`/quizzes/${quizId}`);
    },
    
    async submitQuiz(quizId, answers, timeTaken) {
        return apiRequest(`/quizzes/${quizId}/submit`, {
            method: 'POST',
            body: JSON.stringify({
                answers: answers,
                time_taken_minutes: timeTaken
            })
        });
    },
    
    async getResults(quizId = null) {
        const query = quizId ? `?quiz_id=${quizId}` : '';
        return apiRequest(`/quizzes/results${query}`);
    }
};

// Progress API
const progressAPI = {
    async getDashboard() {
        return apiRequest('/progress/dashboard');
    },
    
    async getCourseProgress(courseId) {
        return apiRequest(`/progress/course/${courseId}`);
    }
};

// AI API
const aiAPI = {
    async getRecommendations(courseId = null, includeReasons = true) {
        const params = new URLSearchParams();
        if (courseId) params.append('course_id', courseId);
        if (includeReasons) params.append('include_reasons', 'true');
        
        return apiRequest(`/ai/recommendations?${params}`);
    },
    
    async askQuestion(question, context = null) {
        return apiRequest('/ai/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: question,
                context: context
            })
        });
    },
    
    async getExplanation(questionId, userAnswer) {
        return apiRequest('/ai/explain', {
            method: 'POST',
            body: JSON.stringify({
                question_id: questionId,
                user_answer: userAnswer
            })
        });
    }
};

// Admin API
const adminAPI = {
    async getUsers() {
        return apiRequest('/admin/users');
    },
    
    async updateUser(userId, updates) {
        return apiRequest(`/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    },
    
    async deleteUser(userId) {
        return apiRequest(`/admin/users/${userId}`, {
            method: 'DELETE'
        });
    },
    
    async createCourse(courseData) {
        return apiRequest('/admin/courses', {
            method: 'POST',
            body: JSON.stringify(courseData)
        });
    },
    
    async updateCourse(courseId, updates) {
        return apiRequest(`/admin/courses/${courseId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    },
    
    async deleteCourse(courseId) {
        return apiRequest(`/admin/courses/${courseId}`, {
            method: 'DELETE'
        });
    },
    
    async createLesson(lessonData) {
        return apiRequest('/admin/lessons', {
            method: 'POST',
            body: JSON.stringify(lessonData)
        });
    },
    
    async updateLesson(lessonId, updates) {
        return apiRequest(`/admin/lessons/${lessonId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    },
    
    async deleteLesson(lessonId) {
        return apiRequest(`/admin/lessons/${lessonId}`, {
            method: 'DELETE'
        });
    },
    
    async getStatistics() {
        return apiRequest('/admin/statistics');
    },

    async sendNotification(notificationData) {
        return apiRequest('/admin/notifications/send', {
            method: 'POST',
            body: JSON.stringify(notificationData)
        });
    }
};

// Notifications API
const notificationsAPI = {
    async getMyNotifications(unreadOnly = false) {
        const query = unreadOnly ? '?unread=true' : '';
        return apiRequest(`/admin/notifications${query}`);
    },
    
    async markRead(notificationId) {
        return apiRequest(`/notifications/${notificationId}/read`, {
            method: 'POST'
        });
    }
};

// Utility functions
function logout() {
    removeToken();
    redirectTo('../index.html');
}

function redirectTo(path) {
    window.location.href = path;
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#dc2626' : type === 'success' ? '#16a34a' : '#2563eb'};
        color: white;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    alert.textContent = message;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);