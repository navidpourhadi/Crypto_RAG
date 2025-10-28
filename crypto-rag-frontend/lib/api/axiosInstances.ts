import axios, { AxiosError } from "axios";

interface QueueItem {
  resolve: (value?: unknown) => void;
  reject: (error?: unknown) => void;
}
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api";
let isRefreshing = false;
let failedQueue: QueueItem[] = [];

const processQueue = (
  error: AxiosError | null,
  token: string | null = null
) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// --- Public API Instance (No interceptors, no credentials by default) ---
const publicApi = axios.create({
  baseURL: baseURL,
});

// --- Authenticated API Instance ---
// This instance will include interceptors for handling token refresh
// and will send cookies with requests.
// This is useful for APIs that require authentication.

const authenticatedApi = axios.create({
  baseURL: baseURL,
  withCredentials: true, // send cookies with requests
});

authenticatedApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // For other 401 errors, try to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then(() => authenticatedApi(originalRequest))
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        await authenticatedApi.post("/auth/refresh");
        processQueue(null);
        return authenticatedApi(originalRequest);
      } catch (err) {
        const error = err as AxiosError;
        processQueue(error, null);
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export { authenticatedApi, publicApi };
