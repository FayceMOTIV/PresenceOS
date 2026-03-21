// PresenceOS Mobile — Cinematic Video API Service
// Dedicated service for the 3-clip cinematic pipeline (Kling 2.6 Pro).
// Separate from lib/api.ts because it uses extended timeouts (130s)
// and a distinct endpoint structure.

import Constants from "expo-constants";
import { useAuthStore } from "@/stores/authStore";

// ── API Base ──

const API_V2_BASE = __DEV__
  ? "http://192.168.10.114:8000/api/v2"
  : "https://rs3-api-production.up.railway.app/api/v2";

// ── Types ──

export interface CinematicVideoResult {
  success: boolean;
  video_url: string | null;
  clips: string[];
  clips_count: number;
  cost_usd: number;
}

interface PublishResult {
  success: boolean;
  post_id?: string;
  platform?: string;
  published_at?: string;
}

interface SaveDraftResult {
  success: boolean;
  draft_id?: string;
}

// ── Auth Headers (mirrors lib/api.ts pattern) ──

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
    const freshToken = await refreshToken();
    if (freshToken) {
      headers["Authorization"] = `Bearer ${freshToken}`;
    }
  } else if (__DEV__) {
    headers["Authorization"] = "Bearer dev-token-presenceos";
  }

  return headers;
}

// ── Fetch with AbortController timeout ──

async function fetchWithTimeout<T>(
  url: string,
  options: RequestInit,
  timeoutMs: number,
): Promise<T | null> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    const contentType = res.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json")
      ? await res.json()
      : await res.text();

    if (!res.ok) {
      console.error(
        `[videoApi] HTTP ${res.status} — ${typeof data === "string" ? data : JSON.stringify(data)}`,
      );
      return null;
    }

    return data as T;
  } catch (err: unknown) {
    clearTimeout(timeoutId);
    if (err instanceof Error && err.name === "AbortError") {
      console.error("[videoApi] Request timed out after", timeoutMs, "ms");
    } else {
      console.error("[videoApi] Fetch error:", err);
    }
    return null;
  }
}

// ── Exported API Functions ──

/**
 * Generate a cinematic video (3 clips, Kling 2.6 Pro).
 * Timeout: 130s because Kling takes 45-90s per clip × 3 clips.
 */
export async function generateCinematicVideo(
  brandId: string,
  dishName: string,
  aspectRatio: string = "9:16",
): Promise<CinematicVideoResult | null> {
  const headers = await getAuthHeaders();
  const url = `${API_V2_BASE}/ai-video/brands/${encodeURIComponent(brandId)}/cinematic`;

  return fetchWithTimeout<CinematicVideoResult>(
    url,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        dish_name: dishName,
        aspect_ratio: aspectRatio,
      }),
    },
    130_000,
  );
}

/**
 * Publish a video to a social platform via Postiz.
 */
export async function publishVideo(
  brandId: string,
  videoUrl: string,
  caption: string,
  platform: string,
  scheduledAt?: string,
): Promise<PublishResult | null> {
  const headers = await getAuthHeaders();
  const url = `${API_V2_BASE}/publish/brands/${encodeURIComponent(brandId)}/publish`;

  const body: Record<string, unknown> = {
    video_url: videoUrl,
    caption,
    platform,
  };
  if (scheduledAt) {
    body.scheduled_at = scheduledAt;
  }

  return fetchWithTimeout<PublishResult>(
    url,
    {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    },
    30_000,
  );
}

/**
 * Save a video as draft (no immediate publish).
 */
export async function saveVideoAsDraft(
  brandId: string,
  videoUrl: string,
  caption: string,
  platform: string,
): Promise<SaveDraftResult | null> {
  const headers = await getAuthHeaders();
  const url = `${API_V2_BASE}/publish/brands/${encodeURIComponent(brandId)}/drafts`;

  return fetchWithTimeout<SaveDraftResult>(
    url,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        video_url: videoUrl,
        caption,
        platform,
      }),
    },
    30_000,
  );
}
