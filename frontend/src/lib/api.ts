import axios, { AxiosError } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle auth errors — redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("workspace_id");
        localStorage.removeItem("brand_id");
        window.location.href = "/auth/login";
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    workspace_name?: string;
  }) => api.post("/auth/register", data),

  login: (email: string, password: string) => {
    const formData = new FormData();
    formData.append("username", email);
    formData.append("password", password);
    return api.post("/auth/login", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  me: () => api.get("/auth/me"),
  refresh: () => api.post("/auth/refresh"),
};

// Users
export const usersApi = {
  getMe: () => api.get("/users/me"),
  updateMe: (data: { full_name?: string; avatar_url?: string }) =>
    api.patch("/users/me", data),
  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post("/users/me/change-password", data),
  getMyWorkspaces: () => api.get("/users/me/workspaces"),
};

// Workspaces
export const workspacesApi = {
  list: () => api.get("/users/me/workspaces"),
  get: (id: string) => api.get(`/workspaces/${id}`),
  create: (data: { name: string; slug: string; timezone?: string }) =>
    api.post("/workspaces", data),
  update: (id: string, data: Partial<{ name: string; logo_url: string; timezone: string }>) =>
    api.patch(`/workspaces/${id}`, data),
  getBrands: (id: string) => api.get(`/workspaces/${id}/brands`),
  getMembers: (id: string) => api.get(`/workspaces/${id}/members`),
  inviteMember: (id: string, data: { email: string; role?: string }) =>
    api.post(`/workspaces/${id}/members`, data),
  removeMember: (id: string, userId: string) =>
    api.delete(`/workspaces/${id}/members/${userId}`),
  updateMemberRole: (id: string, userId: string, role: string) =>
    api.patch(`/workspaces/${id}/members/${userId}`, { role }),
};

// Brands
export const brandsApi = {
  get: (id: string) => api.get(`/brands/${id}`),
  create: (workspaceId: string, data: any) =>
    api.post(`/brands?workspace_id=${workspaceId}`, data),
  update: (id: string, data: any) => api.patch(`/brands/${id}`, data),
  getVoice: (id: string) => api.get(`/brands/${id}/voice`),
  updateVoice: (id: string, data: any) => api.patch(`/brands/${id}/voice`, data),
  onboard: (id: string, data: any) => api.post(`/brands/${id}/onboard`, data),
};

// Knowledge
export const knowledgeApi = {
  list: (brandId: string, params?: any) =>
    api.get(`/knowledge/brands/${brandId}`, { params }),
  get: (id: string) => api.get(`/knowledge/${id}`),
  create: (brandId: string, data: any) =>
    api.post(`/knowledge/brands/${brandId}`, data),
  update: (id: string, data: any) => api.patch(`/knowledge/${id}`, data),
  delete: (id: string) => api.delete(`/knowledge/${id}`),
  import: (brandId: string, data: any) =>
    api.post(`/knowledge/brands/${brandId}/import`, data),
  getCategories: (brandId: string) =>
    api.get(`/knowledge/brands/${brandId}/categories`),
};

// Ideas
export const ideasApi = {
  list: (brandId: string, params?: any) =>
    api.get(`/ideas/brands/${brandId}`, { params }),
  get: (id: string) => api.get(`/ideas/${id}`),
  create: (brandId: string, data: any) =>
    api.post(`/ideas/brands/${brandId}`, data),
  update: (id: string, data: any) => api.patch(`/ideas/${id}`, data),
  approve: (id: string) => api.post(`/ideas/${id}/approve`),
  reject: (id: string) => api.post(`/ideas/${id}/reject`),
  getDaily: (brandId: string) => api.get(`/ideas/brands/${brandId}/daily`),
};

// Drafts
export const draftsApi = {
  list: (brandId: string, params?: any) =>
    api.get(`/drafts/brands/${brandId}`, { params }),
  get: (id: string) => api.get(`/drafts/${id}`),
  create: (brandId: string, data: any) =>
    api.post(`/drafts/brands/${brandId}`, data),
  update: (id: string, data: any) => api.patch(`/drafts/${id}`, data),
  delete: (id: string) => api.delete(`/drafts/${id}`),
  approve: (id: string) => api.post(`/drafts/${id}/approve`),
  selectVariant: (draftId: string, variantId: string) =>
    api.post(`/drafts/${draftId}/variants/${variantId}/select`),
};

// Connectors
export const connectorsApi = {
  list: (brandId: string) => api.get(`/connectors/brands/${brandId}`),
  get: (id: string) => api.get(`/connectors/${id}`),
  getOAuthUrl: (platform: string, brandId: string) =>
    api.post("/connectors/oauth/url", { platform, brand_id: brandId }),
  callback: (brandId: string, data: any) =>
    api.post(`/connectors/oauth/callback?brand_id=${brandId}`, data),
  refresh: (id: string) => api.post(`/connectors/${id}/refresh`),
  disconnect: (id: string) => api.delete(`/connectors/${id}`),
  sync: (id: string) => api.post(`/connectors/${id}/sync`),
  connectWithApiKey: (platform: string, brandId: string, apiKey: string, accountUsername?: string) =>
    api.post("/connectors/api-key", { platform, brand_id: brandId, api_key: apiKey, account_username: accountUsername }),
};

// Posts
export const postsApi = {
  list: (brandId: string, params?: any) =>
    api.get(`/posts/brands/${brandId}`, { params }),
  get: (id: string) => api.get(`/posts/${id}`),
  schedule: (brandId: string, data: any) =>
    api.post(`/posts/brands/${brandId}`, data),
  update: (id: string, data: any) => api.patch(`/posts/${id}`, data),
  cancel: (id: string) => api.delete(`/posts/${id}`),
  getJobs: (id: string) => api.get(`/posts/${id}/jobs`),
  getCalendar: (brandId: string, params?: { month?: string; start_date?: string; end_date?: string }) =>
    api.get(`/posts/brands/${brandId}/calendar`, { params }),
  bulkSchedule: (data: { items: Array<{ scheduled_post_id: string; new_scheduled_at: string }> }) =>
    api.patch("/posts/bulk-schedule", data),
  quickCreate: (brandId: string, data: {
    title: string;
    caption: string;
    platform: string;
    media_type: string;
    scheduled_at: string;
    connector_id: string;
  }) => api.post(`/posts/brands/${brandId}/quick`, data),
};

// Drafts scheduling
export const draftsScheduleApi = {
  schedule: (draftId: string, data: { connector_id: string; scheduled_at: string; timezone?: string }) =>
    api.patch(`/drafts/${draftId}/schedule`, data),
};

// Metrics
export const metricsApi = {
  getDashboard: (brandId: string, days?: number) =>
    api.get(`/metrics/brands/${brandId}/dashboard`, { params: { days } }),
  getPlatforms: (brandId: string, days?: number) =>
    api.get(`/metrics/brands/${brandId}/platforms`, { params: { days } }),
  getPostMetrics: (postId: string) => api.get(`/metrics/posts/${postId}`),
  getTopPosts: (brandId: string, params?: any) =>
    api.get(`/metrics/brands/${brandId}/top-posts`, { params }),
  getLearning: (brandId: string) =>
    api.get(`/metrics/brands/${brandId}/learning`),
};

// AI
export const aiApi = {
  generateIdeas: (brandId: string, data: any) =>
    api.post(`/ai/brands/${brandId}/ideas/generate`, data),
  saveIdeas: (brandId: string, ideas: any[]) =>
    api.post(`/ai/brands/${brandId}/ideas/save`, ideas),
  generateDraft: (brandId: string, data: any) =>
    api.post(`/ai/brands/${brandId}/drafts/generate`, data),
  saveDraft: (brandId: string, data: any, ideaId?: string) =>
    api.post(
      `/ai/brands/${brandId}/drafts/save${ideaId ? `?idea_id=${ideaId}` : ""}`,
      data
    ),
  analyzeTrends: (brandId: string, data: any) =>
    api.post(`/ai/brands/${brandId}/trends/analyze`, data),
  transcribe: (brandId: string, audio: File) => {
    const formData = new FormData();
    formData.append("audio", audio);
    return api.post(`/ai/brands/${brandId}/voice/transcribe`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  enhanceCaption: (brandId: string, caption: string, platform: string) => {
    const formData = new FormData();
    formData.append("caption", caption);
    formData.append("platform", platform);
    return api.post(`/ai/brands/${brandId}/caption/enhance`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  suggestReply: (brandId: string, comment: string, context?: string) => {
    const formData = new FormData();
    formData.append("comment", comment);
    if (context) formData.append("context", context);
    return api.post(`/ai/brands/${brandId}/reply/suggest`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  // Photo Caption Generation (visual flow)
  generatePhotoCaptions: (brandId: string, file: File, platforms: string = "instagram_post") => {
    const formData = new FormData();
    formData.append("photo", file);
    formData.append("platforms", platforms);
    return api.post(`/ai/brands/${brandId}/photo/captions`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  regenerateHashtags: (brandId: string, data: { caption: string; platform?: string; count?: number }) =>
    api.post(`/ai/brands/${brandId}/captions/regenerate-hashtags`, data),

  changeTone: (brandId: string, data: { caption: string; tone: string; platform?: string }) =>
    api.post(`/ai/brands/${brandId}/captions/change-tone`, data),

  suggestEmojis: (brandId: string, data: { caption: string }) =>
    api.post(`/ai/brands/${brandId}/captions/suggest-emojis`, data),

  getEngagementScore: (brandId: string, data: { caption: string; hashtags: string[]; platform: string }) =>
    api.post(`/ai/brands/${brandId}/captions/engagement-score`, data),
};

// Media Storage
export const mediaApi = {
  upload: (brandId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/media/brands/${brandId}/upload`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  getPresignedUrl: (brandId: string, filename: string, contentType: string) =>
    api.post(`/media/brands/${brandId}/presigned-url`, {
      filename,
      content_type: contentType,
    }),
  delete: (brandId: string, key: string) =>
    api.delete(`/media/brands/${brandId}/media/${key}`),
  getInfo: (brandId: string, key: string) =>
    api.get(`/media/brands/${brandId}/media/${key}`),
};

// Autopilot
export const autopilotApi = {
  getConfig: (brandId: string) =>
    api.get(`/autopilot/brands/${brandId}/autopilot`),
  createConfig: (brandId: string, data: any) =>
    api.post(`/autopilot/brands/${brandId}/autopilot`, data),
  updateConfig: (brandId: string, data: any) =>
    api.patch(`/autopilot/brands/${brandId}/autopilot`, data),
  toggle: (brandId: string) =>
    api.post(`/autopilot/brands/${brandId}/autopilot/toggle`),
  listPending: (brandId: string, params?: any) =>
    api.get(`/autopilot/brands/${brandId}/autopilot/pending`, { params }),
  getPending: (id: string) =>
    api.get(`/autopilot/autopilot/pending/${id}`),
  actionPending: (id: string, data: { action: string; connector_id?: string }) =>
    api.post(`/autopilot/autopilot/pending/${id}/action`, data),
  triggerGeneration: (brandId: string) =>
    api.post(`/autopilot/brands/${brandId}/autopilot/generate`),
};

// Media Library (Sprint 9B)
export const mediaLibraryApi = {
  listAssets: (brandId: string, params?: { media_type?: string; source?: string; archived?: boolean; limit?: number; offset?: number }) =>
    api.get(`/media-library/brands/${brandId}/assets`, { params }),
  getAsset: (assetId: string) =>
    api.get(`/media-library/assets/${assetId}`),
  updateAsset: (assetId: string, data: { ai_description?: string; ai_tags?: string[]; is_archived?: boolean }) =>
    api.patch(`/media-library/assets/${assetId}`, data),
  deleteAsset: (assetId: string) =>
    api.delete(`/media-library/assets/${assetId}`),
  listVoiceNotes: (brandId: string, params?: { transcribed_only?: boolean; limit?: number; offset?: number }) =>
    api.get(`/media-library/brands/${brandId}/voice-notes`, { params }),
  getVoiceNote: (noteId: string) =>
    api.get(`/media-library/voice-notes/${noteId}`),
  deleteVoiceNote: (noteId: string) =>
    api.delete(`/media-library/voice-notes/${noteId}`),
  getStats: (brandId: string) =>
    api.get(`/media-library/brands/${brandId}/stats`),
};

// Onboarding Intelligent (Phase 2 — dedicated endpoints)
export const onboardingApi = {
  start: (data: { website_url?: string; social_profiles?: string[] }) =>
    api.post("/onboarding/start", data),

  answer: (data: { session_id: string; question_key: string; answer: string }) =>
    api.post("/onboarding/answer", data),

  complete: (sessionId: string) =>
    api.post(`/onboarding/complete?session_id=${sessionId}`),

  getStatus: (sessionId: string) =>
    api.get(`/onboarding/status/${sessionId}`),
};

// Content Studio Chat
export const chatApi = {
  sendMessage: (data: {
    msg_type: string;
    text?: string;
    button_id?: string;
    media_id?: string;
    media_url?: string;
    session_id?: string;
  }) => api.post("/chat/message", data),

  uploadMedia: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/chat/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// AI Agents
export const agentsApi = {
  generateContent: (data: {
    brand_id: string;
    platforms: string[];
    num_posts: number;
    topic?: string;
    industry?: string;
    tone?: string;
  }) => api.post("/agents/generate-content", data),

  scanTrends: (data: {
    brand_id: string;
    industry: string;
    platforms?: string[];
  }) => api.post("/agents/scan-trends", data),

  analyzeBrand: (data: { brand_id: string; website_url: string }) =>
    api.post("/agents/analyze-brand", data),

  extractBrand: (websiteUrl: string) =>
    api.post("/agents/extract-brand", { website_url: websiteUrl }),

  getTaskStatus: (taskId: string) => api.get(`/agents/tasks/${taskId}`),

  // Onboarding intelligent
  onboardingStart: (data: { website_url?: string; social_profiles?: string[] }) =>
    api.post("/agents/onboarding/start", data),

  onboardingAnswer: (data: { session_id: string; question_key: string; answer: string }) =>
    api.post("/agents/onboarding/answer", data),

  onboardingComplete: (sessionId: string) =>
    api.post(`/agents/onboarding/complete?session_id=${sessionId}`),
};

// Photo Enhancement (Feature 2)
export const photosApi = {
  enhance: (file: File, style: string = "instagram", aiAnalysis: boolean = false) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post(`/photos/enhance?style=${style}&ai_analysis=${aiAnalysis}`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  checkQuality: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/photos/quality", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  enhanceAllStyles: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/photos/enhance/all-styles", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  getComparison: (enhanceId: string) => api.get(`/photos/compare/${enhanceId}`),
};

// Smart Scheduling (Feature 1)
export const schedulingApi = {
  getOptimalTimes: (brandId: string, platform: string = "instagram", count: number = 5, timezoneOffset: number = 1) =>
    api.get(`/scheduling/optimal-times/${brandId}`, { params: { platform, count, timezone_offset: timezoneOffset } }),

  getNextOptimal: (brandId: string, platform: string = "instagram", timezoneOffset: number = 1) =>
    api.get(`/scheduling/next-optimal/${brandId}`, { params: { platform, timezone_offset: timezoneOffset } }),

  schedule: (data: {
    brand_id: string;
    platform?: string;
    caption?: string;
    media_urls?: string[];
    hashtags?: string[];
    scheduled_at?: string;
    use_optimal?: boolean;
  }) => api.post("/scheduling/schedule", data),

  getCalendar: (brandId: string, startDate?: string, endDate?: string) =>
    api.get(`/scheduling/calendar/${brandId}`, { params: { start_date: startDate, end_date: endDate } }),

  getScheduled: (brandId: string) =>
    api.get(`/scheduling/scheduled/${brandId}`),

  reschedule: (postId: string, newDatetime: string) =>
    api.patch(`/scheduling/reschedule/${postId}`, { new_datetime: newDatetime }),

  cancel: (postId: string) =>
    api.delete(`/scheduling/cancel/${postId}`),
};

// Content Repurposing (Feature 4)
export const repurposeApi = {
  repurpose: (data: {
    brand_id: string;
    caption: string;
    hashtags?: string[];
    media_urls?: string[];
    target_formats?: string[];
  }) => api.post("/repurpose/repurpose", data),

  getPackage: (packageId: string) =>
    api.get(`/repurpose/package/${packageId}`),

  getFormats: () =>
    api.get("/repurpose/formats"),
};

// Google Business Profile (Feature 7)
export const gbpApi = {
  getConfig: (brandId: string) =>
    api.get(`/gbp/config/${brandId}`),

  updateConfig: (brandId: string, data: {
    enabled?: boolean;
    location_id?: string;
    auto_sync?: boolean;
    default_post_type?: string;
    default_cta?: string;
    include_photos?: boolean;
    include_offers?: boolean;
    publish_frequency?: string;
  }) => api.patch(`/gbp/config/${brandId}`, data),

  toggle: (brandId: string) =>
    api.post(`/gbp/config/${brandId}/toggle`),

  publish: (data: {
    brand_id: string;
    caption: string;
    media_urls?: string[];
    post_type?: string;
    cta_type?: string;
    cta_url?: string;
  }) => api.post("/gbp/publish", data),

  getPosts: (brandId: string) =>
    api.get(`/gbp/posts/${brandId}`),

  deletePost: (postId: string) =>
    api.delete(`/gbp/post/${postId}`),

  getStats: (brandId: string) =>
    api.get(`/gbp/stats/${brandId}`),
};

// Analytics Dashboard (Feature 9)
export const analyticsApi = {
  getOverview: (brandId: string, days: number = 30) =>
    api.get(`/analytics/overview/${brandId}`, { params: { days } }),

  getKpis: (brandId: string, days: number = 30) =>
    api.get(`/analytics/kpis/${brandId}`, { params: { days } }),

  getTimeline: (brandId: string, days: number = 30) =>
    api.get(`/analytics/timeline/${brandId}`, { params: { days } }),

  getInsights: (brandId: string) =>
    api.get(`/analytics/insights/${brandId}`),
};

// Reputation Manager (Feature 3)
export const reputationApi = {
  getReviews: (brandId: string, params?: { platform?: string; sentiment?: string; responded?: boolean }) =>
    api.get(`/reputation/reviews/${brandId}`, { params }),

  getReview: (reviewId: string) =>
    api.get(`/reputation/review/${reviewId}`),

  suggestResponse: (reviewId: string) =>
    api.post(`/reputation/review/${reviewId}/suggest`),

  respond: (reviewId: string, responseText: string) =>
    api.post(`/reputation/review/${reviewId}/respond`, { response_text: responseText }),

  getStats: (brandId: string) =>
    api.get(`/reputation/stats/${brandId}`),
};

// Trend Radar (Feature 8)
export const trendsRadarApi = {
  getTrends: (brandId: string, params?: { category?: string; platform?: string; limit?: number }) =>
    api.get(`/trends/trends/${brandId}`, { params }),

  getCategories: () =>
    api.get("/trends/categories"),

  getSummary: (brandId: string) =>
    api.get(`/trends/summary/${brandId}`),
};

// Competitor Intelligence (Feature 5)
export const competitorApi = {
  getCompetitors: (brandId: string) =>
    api.get(`/competitor/list/${brandId}`),

  addCompetitor: (brandId: string, data: { name: string; handle: string; platform?: string }) =>
    api.post(`/competitor/track/${brandId}`, data),

  removeCompetitor: (brandId: string, competitorId: string) =>
    api.delete(`/competitor/untrack/${brandId}/${competitorId}`),

  getBenchmark: (brandId: string) =>
    api.get(`/competitor/benchmark/${brandId}`),
};

// Brand Interview AI
export const interviewApi = {
  start: (brandId: string) =>
    api.post(`/interview/brands/${brandId}/start`),

  sendMessage: (brandId: string, message: string) =>
    api.post(`/interview/brands/${brandId}/message`, { message }),

  getStatus: (brandId: string) =>
    api.get(`/interview/brands/${brandId}/status`),
};

// Content Analysis (Instagram tone extraction)
export const contentAnalysisApi = {
  analyze: (brandId: string, instagramUsername: string) =>
    api.post(`/content-analysis/brands/${brandId}/analyze`, {
      instagram_username: instagramUsername,
    }),

  getStatus: (brandId: string) =>
    api.get(`/content-analysis/brands/${brandId}/status`),
};

// Hyperlocal Intelligence (Feature 10)
export const hyperlocalApi = {
  getContext: (brandId: string, lat?: number, lon?: number) =>
    api.get(`/hyperlocal/context/${brandId}`, { params: { lat, lon } }),

  getWeather: (brandId: string) =>
    api.get(`/hyperlocal/weather/${brandId}`),

  getEvents: (brandId: string) =>
    api.get(`/hyperlocal/events/${brandId}`),

  getSuggestions: (brandId: string) =>
    api.get(`/hyperlocal/suggestions/${brandId}`),
};
