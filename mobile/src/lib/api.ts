// PresenceOS Mobile — API Client (fetch-based, no axios)
// Uses native fetch to avoid Hermes URL.protocol compatibility issues

import Constants from "expo-constants";
import { useAuthStore } from "@/stores/authStore";

const API_BASE = __DEV__
  ? "http://192.168.10.114:8000/api/v1"
  : "https://rs3-api-production.up.railway.app/api/v1";

const API_V2_BASE = __DEV__
  ? "http://192.168.10.114:8000/api/v2"
  : "https://rs3-api-production.up.railway.app/api/v2";

// ── 401 interceptor: logout callback set by App.tsx ──
let _onUnauthorized: (() => void) | null = null;

export function setOnUnauthorized(cb: () => void) {
  _onUnauthorized = cb;
}

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
  const appVersion = Constants.expoConfig?.version ?? "1.0.0";
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-App-Version": appVersion,
  };

  const { token, user, refreshToken } = useAuthStore.getState();

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  } else if (user) {
    // Token null but user exists — force refresh
    const freshToken = await refreshToken();
    if (freshToken) {
      headers["Authorization"] = `Bearer ${freshToken}`;
    }
  } else if (__DEV__) {
    // Dev bypass — auto-authenticate when no Firebase user
    headers["Authorization"] = "Bearer dev-token-presenceos";
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
      // 401 → token expired, trigger auto-logout
      if (res.status === 401 && _onUnauthorized) {
        _onUnauthorized();
      }
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

async function requestV2<T = any>(
  method: string,
  path: string,
  options?: {
    body?: any;
    params?: Record<string, any>;
    headers?: Record<string, string>;
    isFormData?: boolean;
  }
): Promise<ApiResponse<T>> {
  const url = `${API_V2_BASE}${path}`;
  const qs = options?.params
    ? "?" + Object.entries(options.params)
        .filter(([, v]) => v !== undefined && v !== null)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
        .join("&")
    : "";
  const fullUrl = url + qs;
  const authHeaders = await getAuthHeaders();

  const headers: Record<string, string> = {
    ...authHeaders,
    ...options?.headers,
  };

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
    const res = await fetch(fullUrl, fetchOptions);
    clearTimeout(timeout);

    let data: any;
    const contentType = res.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      data = await res.json();
    } else {
      data = await res.text();
    }

    if (!res.ok) {
      if (res.status === 401 && _onUnauthorized) {
        _onUnauthorized();
      }
      const error: any = new Error(data?.detail || `HTTP ${res.status}`);
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
  register: (email: string, password: string, fullName: string, workspaceName?: string) =>
    request("POST", "/auth/register", {
      body: { email, password, full_name: fullName, workspace_name: workspaceName },
    }),
  forgotPassword: (email: string) =>
    request("POST", "/auth/forgot-password", { body: { email } }),
  resetPassword: (token: string, newPassword: string) =>
    request("POST", "/auth/reset-password", { body: { token, new_password: newPassword } }),
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
  linkUrl: (brandId: string, platform?: string, redirectUrl?: string) => {
    const params = new URLSearchParams();
    if (platform) params.append("platform", platform);
    if (redirectUrl) params.append("redirect_url", redirectUrl);
    const qs = params.toString();
    return api.get(`/social/link-url/${brandId}${qs ? `?${qs}` : ""}`);
  },
  accounts: (brandId: string) => api.get(`/social/accounts/${brandId}`),
  facebookPages: (brandId: string) =>
    api.get(`/social-auth/facebook-pages/${brandId}`),
  selectPage: (brandId: string, pageId: string) =>
    api.post(`/social-auth/select-page/${brandId}`, { page_id: pageId }),
};

// ── Brands ──
export const brandsApi = {
  mine: () => api.get("/brands/mine"),
};

// ── Video Generation ──
export const videoApi = {
  generate: (brandId: string, prompt: string, duration: number, style: string, aspect_ratio?: string) =>
    api.post("/video/generate", { brand_id: brandId, prompt, duration, style, aspect_ratio }),
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

// ── CM Chat ──
export const cmChatApi = {
  send: (brandId: string, message: string, sessionId?: string) =>
    api.post(`/cm-chat/${brandId}/send`, {
      message,
      session_id: sessionId ?? null,
    }),
  listSessions: (brandId: string, limit = 20, offset = 0) =>
    api.get(`/cm-chat/${brandId}/sessions`, { params: { limit, offset } }),
  getMessages: (brandId: string, sessionId: string) =>
    api.get(`/cm-chat/${brandId}/sessions/${sessionId}/messages`),
  deleteSession: (brandId: string, sessionId: string) =>
    api.delete(`/cm-chat/${brandId}/sessions/${sessionId}`),
};

// ── Brain / AutoPilot ──
export const brainApi = {
  status: (brandId: string) =>
    api.get(`/brain/${brandId}/status`),
  visualStatus: (brandId: string) =>
    api.get(`/brain/${brandId}/visual/status`),
  recall: (brandId: string, query: string, memoryType?: string) =>
    api.post(`/brain/${brandId}/recall`, { query, memory_type: memoryType }),
  remember: (brandId: string, content: string, memoryType: string, source?: string) =>
    api.post(`/brain/${brandId}/remember`, { content, memory_type: memoryType, source }),
  extractDna: (brandId: string, imageUrls: string[]) =>
    api.post(`/brain/${brandId}/extract-dna`, { image_urls: imageUrls }),
  analytics: (brandId: string, days?: number) =>
    api.get(`/brain/${brandId}/analytics`, { params: { days } }),
  calendarEvents: (brandId: string) =>
    api.get(`/brain/${brandId}/calendar/upcoming`),
  ugcList: (brandId: string) =>
    api.get(`/brain/${brandId}/ugc`),
  ugcAdd: (brandId: string, data: any) =>
    api.post(`/brain/${brandId}/ugc`, data),
  registerPushToken: (brandId: string, token: string) =>
    api.post(`/brain/${brandId}/push-token`, { expo_push_token: token }),
};

// ── Ilyas Chat (v2) ──
export const ilyasApi = {
  chat: (brandId: string, message: string, sessionId?: string, imageUrl?: string) =>
    requestV2("POST", `/ilyas/${brandId}/chat`, {
      body: { message, session_id: sessionId ?? null, image_url: imageUrl ?? null },
    }),
  listSessions: (brandId: string, limit = 20, offset = 0) =>
    requestV2("GET", `/ilyas/${brandId}/sessions`, { params: { limit, offset } }),
  getMessages: (brandId: string, sessionId: string) =>
    requestV2("GET", `/ilyas/${brandId}/sessions/${sessionId}/messages`),
  deleteSession: (brandId: string, sessionId: string) =>
    requestV2("DELETE", `/ilyas/${brandId}/sessions/${sessionId}`),
  context: (brandId: string) =>
    requestV2("GET", `/ilyas/${brandId}/context`),
};

// ── Onboarding DNA v2 ──
export const onboardingApi = {
  start: (brandId: string) =>
    requestV2("GET", `/onboarding/brands/${brandId}/onboarding/start`),
  answer: (brandId: string, step: number, answer: string) =>
    requestV2("POST", `/onboarding/brands/${brandId}/onboarding/answer`, {
      body: { step, answer },
    }),
  getDna: (brandId: string) =>
    requestV2("GET", `/onboarding/brands/${brandId}/onboarding/dna`),
  scrape: (brandId: string, url: string) =>
    requestV2("POST", `/onboarding/brands/${brandId}/scrape`, {
      body: { url },
    }),
};

// ── Voice v2 (Whisper transcription — Sprint 7) ──
export const voiceApi = {
  transcribe: (brandId: string, formData: FormData) =>
    requestV2("POST", `/voice/${brandId}/transcribe`, {
      body: formData,
      isFormData: true,
    }),
};

// ── A/B Testing v2 (Sprint 8) ──
export const abTestApi = {
  create: (brandId: string, platform: string, originalCaption: string, postTopic?: string) =>
    requestV2("POST", `/ab/${brandId}/create`, {
      body: { platform, original_caption: originalCaption, post_topic: postTopic ?? "" },
    }),
  list: (brandId: string) =>
    requestV2("GET", `/ab/${brandId}/tests`),
};

// ── Engage v2 (Comments, DMs, Unified Inbox — Sprint 5) ──
export const engageApi = {
  scan: (brandId: string, sinceHours = 24) =>
    requestV2("POST", `/engage/${brandId}/scan`, {
      body: { since_hours: sinceHours },
    }),
  inbox: (brandId: string, statusFilter?: string, limit = 50) =>
    requestV2("GET", `/engage/${brandId}/inbox`, {
      params: { status_filter: statusFilter, limit },
    }),
  approve: (brandId: string, commentId: string, finalReply?: string) =>
    requestV2("POST", `/engage/${brandId}/inbox/${commentId}/approve`, {
      body: { final_reply: finalReply ?? null },
    }),
  reject: (brandId: string, commentId: string) =>
    requestV2("POST", `/engage/${brandId}/inbox/${commentId}/reject`),
  stats: (brandId: string) =>
    requestV2("GET", `/engage/${brandId}/stats`),
};

// ── Social v2 (Blotato + Upload-Post fallback) ──
export const socialV2Api = {
  accounts: (platform?: string) =>
    requestV2("GET", "/social/accounts", { params: platform ? { platform } : undefined }),
  subaccounts: (accountId: string) =>
    requestV2("GET", `/social/accounts/${accountId}/subaccounts`),
  publish: (accountId: string, platform: string, text: string, mediaUrls?: string[], pageId?: string, scheduledAt?: string) =>
    requestV2("POST", "/social/publish", {
      body: { account_id: accountId, platform, text, media_urls: mediaUrls, page_id: pageId, scheduled_at: scheduledAt },
    }),
};

export default api;
