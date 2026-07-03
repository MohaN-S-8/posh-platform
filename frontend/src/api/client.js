import axios from "axios";

// All API calls go through this instance
const apiClient = axios.create({
  baseURL: "/api/v1", // proxied to backend by Nginx
  withCredentials: true, // sends cookies (JWT tokens) automatically
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — reads token from localStorage for Swagger-style testing
// In production, tokens are in httpOnly cookies and sent automatically
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401 (token expired) globally
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh the token
      try {
        await axios.post("/api/v1/auth/refresh", {}, { withCredentials: true });
        // Retry the original request
        return apiClient(error.config);
      } catch {
        // Refresh failed — redirect to login
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default apiClient;
