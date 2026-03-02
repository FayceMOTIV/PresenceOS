// PresenceOS Mobile — Brain / AutoPilot Type Definitions

export interface BrainMemory {
  id: string;
  brand_id: string;
  memory_type: "episodic" | "semantic" | "procedural" | "reflection";
  content: string;
  source?: string;
  confidence: number;
  access_count: number;
  similarity?: number;
  created_at: string;
}

export interface BrainStatus {
  total_memories: number;
  memory_counts: Record<string, number>;
  maturity: number; // 0-100
  maturity_label: string; // "Nouveau-né" | "Apprenti" | "Compétent" | "Expert" | "Maître"
}

export interface VisualBrainStatus {
  total_visuals: number;
  scored_visuals: number;
  active_templates: number;
  maturity: number;
}

export interface AnalyticsOverview {
  period_days: number;
  total_posts: number;
  total_engagement: number;
  avg_engagement_rate: number;
  best_performing_type: string;
  best_day: string;
  best_time: string;
  growth_trend: string;
  ai_insights: string[];
  recommendations: string[];
}

export interface CalendarEvent {
  name: string;
  date: string;
  content_ideas: string[];
  priority: "high" | "medium" | "low";
}

export interface UGCPost {
  id: string;
  brand_id: string;
  source_platform: string;
  source_url?: string;
  author_username?: string;
  media_url?: string;
  caption?: string;
  permission_status: "pending" | "requested" | "granted" | "denied";
  reposted: boolean;
  created_at: string;
}

export interface OrchestratorJob {
  id: string;
  brand_id: string;
  job_type: string;
  status: string;
  posts_planned: number;
  posts_generated: number;
  stories_planned: number;
  stories_generated: number;
  created_at: string;
}

export interface ValidationItem {
  id: string;
  type: "post" | "story" | "reel";
  image_url?: string;
  video_url?: string;
  caption?: string;
  hashtags?: string[];
  platform: string;
  scheduled_at?: string;
  confidence_score: number;
  brain_context?: Record<string, any>;
  status: "pending" | "approved" | "rejected";
}
