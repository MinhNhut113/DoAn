// API Configuration - Tự động phát hiện URL
function getApiBaseUrl() {
    // Nếu chạy file HTML trực tiếp từ máy tính (file://)
    if (window.location.protocol === 'file:') {
        return 'http://localhost:5000/api';
    }
    
    // Nếu chạy qua Live Server hoặc Python http.server (ví dụ localhost:8000)
    // Mặc định Backend chạy ở port 5000
    const hostname = window.location.hostname;
    return `http://${hostname}:5000/api`;
}

// Chỉ khai báo MỘT LẦN
const API_BASE_URL = getApiBaseUrl();
console.log('🔗 API Base URL:', API_BASE_URL);

// Get auth token from localStorage
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

// Helper functions
function isAuthenticated() {
    return !!localStorage.getItem('auth_token');
}

function redirectTo(path) {
    window.location.href = path;
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 9999;
        color: white;
        font-weight: bold;
        animation: slideIn 0.3s ease-in;
    `;
    
    if (type === 'error') {
        alertDiv.style.backgroundColor = '#dc3545';
    } else if (type === 'success') {
        alertDiv.style.backgroundColor = '#28a745';
    } else {
        alertDiv.style.backgroundColor = '#17a2b8';
    }
    
    alertDiv.textContent = message;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    if (token) {
        // Ensure we don't double-prefix 'Bearer' if token already contains it
        const rawToken = token.startsWith('Bearer ') ? token.split(' ')[1] : token;
        defaultOptions.headers['Authorization'] = `Bearer ${rawToken}`;
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
        const response = await fetch(url, config);
        
        let data;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            const text = await response.text();
            throw new Error(`Server returned non-JSON: ${text.substring(0, 100)}`);
        }
        
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            throw new Error('Không thể kết nối đến server. Đảm bảo Backend đang chạy tại ' + API_BASE_URL.replace('/api', ''));
        }
        
        if (!error.message) {
            throw new Error('Lỗi không xác định: ' + error.toString());
        }
        
        throw error;
    }
}

// Auth API
const authAPI = {
    register: (userData) => apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify(userData)
    }),
    
    login: (username, password) => apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    }),
    
    getProfile: () => apiRequest('/auth/profile'),
    
    updateProfile: (userData) => apiRequest('/auth/profile', {
        method: 'PUT',
        body: JSON.stringify(userData)
    }),
    
    changePassword: (oldPassword, newPassword) => apiRequest('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
    })
};

// Courses API
const coursesAPI = {
    getAll: (enrolledOnly = false) => apiRequest(`/courses?enrolled_only=${enrolledOnly}`),
    
    getById: (courseId) => apiRequest(`/courses/${courseId}`),
    
    enroll: (courseId) => apiRequest(`/courses/${courseId}/enroll`, {
        method: 'POST'
    })
};

// Lessons API
const lessonsAPI = {
    getByCourse: (courseId) => apiRequest(`/lessons/course/${courseId}`),
    
    getById: (lessonId) => apiRequest(`/lessons/${lessonId}`),
    getQuiz: (lessonId) => apiRequest(`/lessons/${lessonId}/quiz`),
    complete: (lessonId) => apiRequest(`/lessons/${lessonId}/complete`, {
        method: 'POST'
    })
};

// Quizzes API
const quizzesAPI = {
    getAll: (courseId = null, topicId = null) => {
        let url = '/quizzes';
        if (courseId) url += `?course_id=${courseId}`;
        if (topicId) url += (courseId ? '&' : '?') + `topic_id=${topicId}`;
        return apiRequest(url);
    },
    
    getById: (quizId) => apiRequest(`/quizzes/${quizId}`),
    
    submit: (quizId, answers, timeTaken) => apiRequest(`/quizzes/${quizId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers, time_taken_minutes: timeTaken })
    }),
    
    getResults: (quizId = null) => {
        let url = '/quizzes/results';
        if (quizId) url += `?quiz_id=${quizId}`;
        return apiRequest(url);
    }
};

// Progress API
const progressAPI = {
    getCourseProgress: (courseId) => apiRequest(`/progress/course/${courseId}`),
    
    getAnalytics: (courseId = null) => {
        let url = '/progress/analytics';
        if (courseId) url += `?course_id=${courseId}`;
        return apiRequest(url);
    },
    
    getDashboard: () => apiRequest('/progress/dashboard')
};

// AI Recommendations API
const aiAPI = {
    generate: (courseId = null) => apiRequest('/ai/generate', {
        method: 'POST',
        body: JSON.stringify({ course_id: courseId })
    }),
    
    getRecommendations: (type = null, viewed = null) => {
        let url = '/ai/recommendations';
        if (type) url += `?type=${type}`;
        if (viewed !== null) url += (type ? '&' : '?') + `viewed=${viewed}`;
        return apiRequest(url);
    },
    
    markViewed: (recommendationId) => apiRequest(`/ai/${recommendationId}/view`, {
        method: 'POST'
    }),
    
    askQuestion: (question, courseId = null) => apiRequest('/ai/chat', { 
        method: 'POST',
        body: JSON.stringify({ message: question, course_id: courseId }) 
    }),
    generateLesson: (topic, level = 'beginner') => apiRequest('/ai/generate-lesson', {
        method: 'POST',
        body: JSON.stringify({ topic, level })
    })
};

// Admin API
const adminAPI = {
    getUsers: () => apiRequest('/admin/users'),
    
    deactivateUser: (userId) => apiRequest(`/admin/users/${userId}/deactivate`, {
        method: 'POST'
    }),
    
    activateUser: (userId) => apiRequest(`/admin/users/${userId}/activate`, {
        method: 'POST'
    }),
    
    deleteUser: (userId) => apiRequest(`/admin/users/${userId}`, {
        method: 'DELETE'
    }),
    
    createCourse: (courseData) => apiRequest('/admin/courses', {
        method: 'POST',
        body: JSON.stringify(courseData)
    }),
    
    updateCourse: (courseId, courseData) => apiRequest(`/admin/courses/${courseId}`, {
        method: 'PUT',
        body: JSON.stringify(courseData)
    }),
    
    deleteCourse: (courseId) => apiRequest(`/admin/courses/${courseId}`, {
        method: 'DELETE'
    }),
    
    createLesson: (lessonData) => apiRequest('/admin/lessons', {
        method: 'POST',
        body: JSON.stringify(lessonData)
    }),
    
    updateLesson: (lessonId, lessonData) => apiRequest(`/admin/lessons/${lessonId}`, {
        method: 'PUT',
        body: JSON.stringify(lessonData)
    }),
    
    deleteLesson: (lessonId) => apiRequest(`/admin/lessons/${lessonId}`, {
        method: 'DELETE'
    }),
    
    createQuestion: (questionData) => apiRequest('/admin/questions', {
        method: 'POST',
        body: JSON.stringify(questionData)
    }),
    
    updateQuestion: (questionId, questionData) => apiRequest(`/admin/questions/${questionId}`, {
        method: 'PUT',
        body: JSON.stringify(questionData)
    }),
    
    deleteQuestion: (questionId) => apiRequest(`/admin/questions/${questionId}`, {
        method: 'DELETE'
    }),
    
    getStatistics: () => apiRequest('/admin/statistics')
};

// Logout function
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
    window.location.href = '/';
}

