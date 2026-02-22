// PresenceOS Mobile — API Client (fetch-based, no axios)
// Uses native fetch to avoid Hermes URL.protocol compatibility issues

import * as SecureStore from "expo-secure-store";

const API_BASE = __DEV__
  ? "http://192.168.10.114:8000/api/v1"
  : "https://rs3-api-production.up.railway.app/api/v1";

// ── Lightweight fetch wrapper (axios-compatible response shape) ──

interface ApiResponse<T = any> {
  data: T;
  status: number;
}

function buildUrl(path: string, params?: Record<string, any>): string {
  const url = `${API_BASE}${path}`;
  if (!params) return url;
  const qs = Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
  return qs ? `${url}?${qs}` : url;
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  try {
    const token = await SecureStore.getItemAsync("auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    } else if (__DEV__) {
      // Dev bypass — auto-authenticate when no real token is stored
      headers["Authorization"] = "Bearer dev-token-presenceos";
    }
  } catch {
    // SecureStore might fail on first launch
    if (__DEV__) {
      headers["Authorization"] = "Bearer dev-token-presenceos";
    }
  }
  return headers;
}

async function request<T = any>(
  method: string,
  path: string,
  options?: {
    body?: any;
    params?: Record<string, any>;
    headers?: Record<string, string>;
    isFormData?: boolean;
  }
): Promise<ApiResponse<T>> {
  const url = buildUrl(path, options?.params);
  const authHeaders = await getAuthHeaders();

  const headers: Record<string, string> = {
    ...authHeaders,
    ...options?.headers,
  };

  // Don't set Content-Type for FormData (browser sets it with boundary)
  if (options?.isFormData) {
    delete headers["Content-Type"];
  }

  const fetchOptions: RequestInit = {
    method,
    headers,
  };

  if (options?.body !== undefined) {
    fetchOptions.body = options.isFormData
      ? options.body
      : JSON.stringify(options.body);
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  fetchOptions.signal = controller.signal;

  try {
    const res = await fetch(url, fetchOptions);
    clearTimeout(timeout);

    let data: any;
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      const error: any = new Error(
        data?.detail || `HTTP ${res.status}`
      );
      error.response = { data, status: res.status };
      throw error;
    }

    return { data, status: res.status };
  } catch (err: any) {
    clearTimeout(timeout);
    if (err.name === "AbortError") {
      const error: any = new Error("Request timeout");
      error.code = "ECONNABORTED";
      throw error;
    }
    throw err;
  }
}

// ── Convenience methods (same interface as before) ──

const api = {
  get: <T = any>(path: string, opts?: { params?: Record<string, any> }) =>
    request<T>("GET", path, { params: opts?.params }),
  post: <T = any>(
    path: string,
    body?: any,
    opts?: { headers?: Record<string, string> }
  ) => {
    const isFormData = body instanceof FormData;
    return request<T>("POST", path, {
      body,
      headers: opts?.headers,
      isFormData,
    });
  },
  put: <T = any>(path: string, body?: any) =>
    request<T>("PUT", path, { body }),
  delete: <T = any>(path: string) => request<T>("DELETE", path),
};

// ── Auth ──
export const authApi = {
  login: (email: string, password: string) => {
    // Backend uses OAuth2PasswordRequestForm (form-urlencoded, field = "username")
    const formBody = `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`;
    return request("POST", "/auth/login", {
      body: formBody,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      isFormData: true, // skip JSON.stringify
    });
  },
};

// ── Content Library ──
export const contentApi = {
  listDishes: (brandId: string, params?: Record<string, any>) =>
    api.get(`/content/${brandId}/dishes`, { params }),
  createDish: (brandId: string, data: any) =>
    api.post(`/content/${brandId}/dishes`, data),
  updateDish: (brandId: string, dishId: string, data: any) =>
    api.put(`/content/${brandId}/dishes/${dishId}`, data),
  deleteDish: (brandId: string, dishId: string) =>
    api.delete(`/content/${brandId}/dishes/${dishId}`),
  createRequest: (brandId: string, data: any) =>
    api.post(`/content/${brandId}/request`, data),
};

// ── Menu Scan ──
export const menuApi = {
  scan: (brandId: string, formData: FormData) =>
    api.post(`/menu/${brandId}/scan`, formData),
  importDishes: (brandId: string, dishes: any[]) =>
    api.post(`/menu/${brandId}/scan/import`, { dishes }),
};

// ── Proposals ──
export const proposalsApi = {
  list: (brandId: string, params?: Record<string, any>) =>
    api.get(`/proposals/${brandId}`, { params }),
  approve: (brandId: string, proposalId: string, scheduledAt?: string) =>
    api.post(`/proposals/${brandId}/${proposalId}/approve`, {
      scheduled_at: scheduledAt,
    }),
  reject: (brandId: string, proposalId: string, reason?: string) =>
    api.post(`/proposals/${brandId}/${proposalId}/reject`, { reason }),
  editCaption: (
    brandId: string,
    proposalId: string,
    caption: string,
    hashtags?: string[]
  ) =>
    api.put(`/proposals/${brandId}/${proposalId}/caption`, {
      caption,
      hashtags,
    }),
  regenerate: (brandId: string, proposalId: string) =>
    api.post(`/proposals/${brandId}/${proposalId}/regenerate`),
};

// ── Daily Brief ──
export const briefApi = {
  getToday: (brandId: string) => api.get(`/brief/${brandId}/today`),
  respond: (brandId: string, response: string) =>
    api.post(`/brief/${brandId}/respond`, { response }),
};

// ── Knowledge Base ──
export const kbApi = {
  get: (brandId: string) => api.get(`/kb/${brandId}`),
  rebuild: (brandId: string) => api.post(`/kb/${brandId}/rebuild`),
  completeness: (brandId: string) =>
    api.get(`/kb/${brandId}/completeness`),
};

// ── Assets ──
export const assetsApi = {
  list: (brandId: string, params?: Record<string, any>) =>
    api.get(`/media-library/brands/${brandId}/assets`, { params }),
  upload: (brandId: string, formData: FormData) =>
    api.post(`/media/brands/${brandId}/upload`, formData),
  improve: (brandId: string, assetId: string) =>
    api.post(`/media-library/brands/${brandId}/assets/${assetId}/improve`),
  generatePost: (brandId: string, assetId: string) =>
    api.post(`/content/${brandId}/asset-proposal`, { asset_id: assetId }),
};

// ── Social Accounts (Upload-Post) ──
export const socialApi = {
  linkUrl: (brandId: string) => api.get(`/social/link-url/${brandId}`),
  accounts: (brandId: string) => api.get(`/social/accounts/${brandId}`),
};

// ── Video Generation ──
export const videoApi = {
  generate: (brandId: string, prompt: string, duration: number, style: string) =>
    api.post("/video/generate", { brand_id: brandId, prompt, duration, style }),
  credits: (brandId: string) =>
    api.get(`/video/credits/${brandId}`),
  history: (brandId: string) =>
    api.get(`/video/history/${brandId}`),
};

// ── CM Inbox ──
export const cmApi = {
  listInteractions: (brandId: string, params?: Record<string, any>) =>
    api.get("/cm/interactions", {
      params: { brand_id: brandId, ...params },
    }),
  approve: (interactionId: string, finalResponse?: string) =>
    api.post(`/cm/interactions/${interactionId}/approve`, {
      final_response: finalResponse,
    }),
  reject: (interactionId: string) =>
    api.post(`/cm/interactions/${interactionId}/reject`),
  getStats: (brandId: string, days = 7) =>
    api.get("/cm/stats", { params: { brand_id: brandId, days } }),
};

export default api;
