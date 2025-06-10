/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, {
  AxiosError,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from "axios";
import Cookies from "js-cookie"
import { ApiError } from "@/types/common.type";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "https://api.wc504.io.vn/api/v1";


const axiosInstance = axios.create({
  baseURL: `${API_BASE_URL}`,
});

axiosInstance.interceptors.request.use(
  async (config) => {
    let access_token = Cookies.get("access_token");
    const refresh_token = Cookies.get("refresh_token");

    if (!access_token && refresh_token) {
      try {
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          { refresh_token }
        );

        if (
          response.data &&
          response.data.error_code === 0 &&
          response.data.data
        ) {
          access_token = response.data.data.access_token as string;
          const new_refresh_token = response.data.data.refresh_token;

          Cookies.set("access_token", access_token, {
            expires: 1,
            path: "/",
            sameSite: "Lax",
            secure: window.location.protocol === "https:",
          });

          Cookies.set("refresh_token", new_refresh_token, {
            expires: 7,
            path: "/",
            sameSite: "Lax",
            secure: window.location.protocol === "https:",
          });
        } else {
          throw new Error("Failed to refresh token");
        }
      } catch (error) {
        console.error("Token refresh failed in request interceptor:", error);

        Cookies.remove("access_token");
        Cookies.remove("refresh_token");

        if (
          typeof window !== "undefined" &&
          !window.location.pathname.startsWith("/auth")
        ) {
          window.location.href = "/auth";
        }

        return Promise.reject(error);
      }
    }

    if (access_token) {
      config.headers.Authorization = `Bearer ${access_token}`;
    }

    return config;
  },
  (err: any) => {
    return Promise.reject(err);
  }
);

// Response interceptor with token refresh handling
axiosInstance.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    const refreshToken = Cookies.get("refresh_token");

    if (
      (error.response?.status === 401 &&
        !originalRequest._retry &&
        refreshToken &&
        originalRequest.url !== "/auth/refresh") ||
      (error.response?.status === 401 && originalRequest.url !== "/users/me ")
    ) {
      originalRequest._retry = true;

      try {
        const response = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {
            refresh_token: refreshToken,
          }
        );

        if (
          response.data &&
          response.data.error_code === 0 &&
          response.data.data
        ) {
          const { access_token, refresh_token } = response.data.data;

          Cookies.set("access_token", access_token, {
            expires: 1,
            path: "/",
            sameSite: "Lax",
            secure: window.location.protocol === "https:",
          });

          Cookies.set("refresh_token", refresh_token, {
            expires: 7,
            path: "/",
            sameSite: "Lax",
            secure: window.location.protocol === "https:",
          });

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return axiosInstance(originalRequest);
        } else {
          throw new Error("Token refresh failed");
        }
      } catch (refreshError) {
        Cookies.remove("access_token");
        Cookies.remove("refresh_token");

        if (
          typeof window !== "undefined" &&
          !window.location.pathname.startsWith("/auth/")
        ) {
          window.location.href = "/auth";
        }

        return Promise.reject(refreshError);
      }
    }

    const apiError: ApiError = {
      status: error.response?.status || 500,
      error_code: error.response?.data?.error_code || 1,
      message: error.response?.data?.message || "An unknown error occurred",
      errors: error.response?.data?.errors,
    };

    return Promise.reject(apiError);
  }
);

export default axiosInstance;
