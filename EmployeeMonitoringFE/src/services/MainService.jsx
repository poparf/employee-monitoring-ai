import axios from 'axios';
import { SERVER_URL } from '../utils/constants';

// Axios instance with base configuration
const apiClient = axios.create({
    baseURL: SERVER_URL,
    headers: {
        'Content-Type': 'application/json'
    },
    // Add withCredentials for CORS with credentials
    withCredentials: true
});

// Automatically add auth token to requests if available
apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add response interceptor to handle CORS errors
apiClient.interceptors.response.use(
    response => response,
    error => {
        if (error.message === 'Network Error' || error.response?.status === 0) {
            console.error('CORS or network error:', error);
            // You could implement retry logic or more specific error handling here
        }
        return Promise.reject(error);
    }
);

// Camera Management
export const getCamerasList = () => {
    return apiClient.get('/video-cameras');
};

export const getCamera = (cameraId) => {
    return apiClient.get(`/video-cameras/${cameraId}`);
};

export const createVideoCamera = (cameraData) => {
    return apiClient.post('/video-cameras', cameraData);
};

export const updateCamera = (cameraId, cameraData) => {
    return apiClient.put(`/video-cameras/${cameraId}`, cameraData);
};

export const deleteCamera = (cameraId) => {
    return apiClient.delete(`/video-cameras/${cameraId}`);
};

// Alert Management
export const getAlerts = (params = {}) => {
    return apiClient.get('/alerts', { params });
};

export const getAlert = (alertId) => {
    return apiClient.get(`/alerts/${alertId}`);
};

export const updateAlert = (alertId, alertData) => {
    return apiClient.put(`/alerts/${alertId}`, alertData);
};

// Employee Management
export const getAllEmployees = () => {
    return apiClient.get('/employees');
};

export const getEmployee = (employeeId) => {
    return apiClient.get(`/employees/${employeeId}`);
};

export const registerEmployee = (employeeData) => {
    // Using FormData, so we need to change the content type header
    const config = {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    };

    console.log('Registering employee with data:', employeeData); // Debugging line
    return apiClient.post('/employees', employeeData, config);
};

export const updateEmployee = (employeeId, employeeData) => {
    // Check if employeeData is FormData (for photo uploads)
    const isFormData = employeeData instanceof FormData;
    const config = isFormData ? {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    } : {};
    
    return apiClient.put(`/employees/${employeeId}`, employeeData, config);
};

export const deleteEmployee = (employeeId) => {
    return apiClient.delete(`/employees/${employeeId}`);
};

// Security Personnel Management
export const getAllSecurity = () => {
    return apiClient.get('/users/security');
};

export const postSecurityInvitation = (code) => {
    return apiClient.post('/users/security/invitation', code);
}

export const getSecurity = (securityId) => {
    return apiClient.get(`/users/security/${securityId}`);
};

export const registerSecurity = (securityData) => {
    const config = {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    };
    return apiClient.post('/security', securityData, config);
};

export const updateSecurity = (securityId, securityData) => {
    const isFormData = securityData instanceof FormData;
    const config = isFormData ? {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    } : {};
    
    return apiClient.put(`/security/${securityId}`, securityData, config);
};

export const deleteSecurity = (securityId) => {
    return apiClient.delete(`/security/${securityId}`);
};

// Zone Management
export const getZones = (cameraId) => {
    return apiClient.get(`/video-cameras/${cameraId}/zones`);
};

export const getZone = (cameraId, zoneId) => {
    return apiClient.get(`/video-cameras/${cameraId}/zones/${zoneId}`);
};

export const createZone = (cameraId, zoneData) => {
    return apiClient.post(`/video-cameras/${cameraId}/zones`, zoneData);
};

export const updateZone = (cameraId, zoneId, zoneData) => {
    return apiClient.put(`/video-cameras/${cameraId}/zones/${zoneId}`, zoneData);
};

export const deleteZone = (cameraId, zoneId) => {
    return apiClient.delete(`/video-cameras/${cameraId}/zones/${zoneId}`);
};
