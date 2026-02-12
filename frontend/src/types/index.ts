// User & Auth
export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  oauth_provider?: string;
  created_at: string;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  logo_url?: string;
  timezone: string;
  default_language: string;
  billing_plan: string;
  created_at: string;
}

// Brand
export type BrandType = "restaurant" | "saas" | "ecommerce" | "service" | "personal" | "other";

export interface TargetPersona {
  name: string;
  age_range?: string;
  interests?: string[];
  pain_points?: string[];
  goals?: string[];
}

export interface ContentPillars {
  education: number;
  entertainment: number;
  engagement: number;
  promotion: number;
  behind_scenes: number;
}

export interface Brand {
  id: string;
  workspace_id: string;
  name: string;
  slug: string;
  brand_type: BrandType;
  description?: string;
  logo_url?: string;
  cover_url?: string;
  website_url?: string;
  target_persona?: TargetPersona;
  locations?: string[];
  constraints?: Record<string, any>;
  content_pillars?: ContentPillars;
  is_active: boolean;
  voice?: BrandVoice;
  created_at: string;
  updated_at: string;
}

export interface BrandVoice {
  id: string;
  brand_id: string;
  tone_formal: number;
  tone_playful: number;
  tone_bold: number;
  tone_technical: number;
  tone_emotional: number;
  example_phrases?: string[];
  words_to_avoid?: string[];
  words_to_prefer?: string[];
  emojis_allowed?: string[];
  max_emojis_per_post: number;
  hashtag_style: string;
  primary_language: string;
  allow_english_terms: boolean;
  custom_instructions?: string;
  created_at: string;
  updated_at: string;
}

// Knowledge
export type KnowledgeType =
  | "menu"
  | "product"
  | "offer"
  | "faq"
  | "proof"
  | "script"
  | "event"
  | "process"
  | "team"
  | "other";

export interface KnowledgeItem {
  id: string;
  brand_id: string;
  knowledge_type: KnowledgeType;
  category?: string;
  title: string;
  content: string;
  metadata?: Record<string, any>;
  image_urls?: string[];
  is_active: boolean;
  is_featured: boolean;
  is_seasonal: boolean;
  season_months?: number[];
  created_at: string;
  updated_at: string;
}

// Content
export type IdeaSource = "ai_generated" | "trend_inspired" | "user_created" | "repurposed" | "calendar_event";
export type IdeaStatus = "new" | "approved" | "in_progress" | "drafted" | "rejected" | "archived";
export type Platform =
  | "instagram_post"
  | "instagram_story"
  | "instagram_reel"
  | "tiktok"
  | "linkedin"
  | "facebook";
export type DraftStatus = "draft" | "review" | "approved" | "scheduled" | "published" | "failed";
export type VariantStyle = "conservative" | "balanced" | "bold" | "faical_style";

export interface ContentIdea {
  id: string;
  brand_id: string;
  title: string;
  description?: string;
  source: IdeaSource;
  status: IdeaStatus;
  content_pillar?: string;
  target_platforms?: string[];
  trend_reference?: string;
  ai_reasoning?: string;
  hooks?: string[];
  suggested_date?: string;
  user_score?: number;
  created_at: string;
  updated_at: string;
}

export interface ContentVariant {
  id: string;
  draft_id: string;
  style: VariantStyle;
  caption: string;
  hashtags?: string[];
  is_selected: boolean;
  ai_notes?: string;
  created_at: string;
}

export interface ContentDraft {
  id: string;
  brand_id: string;
  idea_id?: string;
  platform: Platform;
  status: DraftStatus;
  caption: string;
  hashtags?: string[];
  media_urls?: string[];
  media_type?: string;
  platform_data?: Record<string, any>;
  ai_model_used?: string;
  prompt_version?: string;
  variants: ContentVariant[];
  created_at: string;
  updated_at: string;
}

// Publishing
export type SocialPlatform = "instagram" | "tiktok" | "linkedin" | "facebook";
export type ConnectorStatus = "connected" | "expired" | "revoked" | "error";
export type PostStatus = "scheduled" | "queued" | "publishing" | "published" | "failed" | "cancelled";

export interface SocialConnector {
  id: string;
  brand_id: string;
  platform: SocialPlatform;
  account_id: string;
  account_name?: string;
  account_username?: string;
  account_avatar_url?: string;
  status: ConnectorStatus;
  token_expires_at?: string;
  daily_posts_count: number;
  daily_posts_reset_at?: string;
  last_sync_at?: string;
  last_error?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScheduledPost {
  id: string;
  brand_id: string;
  draft_id?: string;
  connector_id: string;
  scheduled_at: string;
  timezone: string;
  status: PostStatus;
  content_snapshot: {
    caption: string;
    hashtags?: string[];
    media_urls?: string[];
    media_type?: string;
    platform_data?: Record<string, any>;
  };
  platform_post_id?: string;
  platform_post_url?: string;
  published_at?: string;
  last_error?: string;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

// Metrics
export interface DashboardMetrics {
  total_posts_published: number;
  total_posts_scheduled: number;
  total_impressions: number;
  total_engagement: number;
  average_engagement_rate: number;
  top_platform?: string;
  best_posting_time?: string;
  ai_insight?: string;
}

export interface PlatformBreakdown {
  platform: string;
  posts_count: number;
  total_impressions: number;
  total_engagement: number;
  average_engagement_rate: number;
}

// Top Posts (Analytics)
export interface TopPost {
  post_id: string;
  platform_post_url?: string;
  published_at?: string;
  caption_preview: string;
  impressions: number;
  reach: number;
  likes: number;
  comments: number;
  shares: number;
  engagement_rate: number;
}

// Learning Insights (Analytics)
export interface LearningInsights {
  summary: string;
  what_works: string[];
  recommendations: string[];
  content_mix_suggestion: {
    education: number;
    entertainment: number;
    engagement: number;
    promotion: number;
    behind_scenes: number;
  };
}

// Trend Analysis
export interface TrendInput {
  url?: string;
  description: string;
  platform?: string;
}

export interface GeneratedIdea {
  title: string;
  description: string;
  content_pillar: string;
  target_platforms: string[];
  hooks: string[];
  ai_reasoning: string;
  suggested_date?: string;
}

export interface TrendAnalysisResult {
  summary: string;
  key_themes: string[];
  ideas?: GeneratedIdea[];
}

// Calendar
export interface CalendarDay {
  date: string;
  scheduled_posts: ScheduledPost[];
  ideas: string[];
}

// Autopilot (Sprint 9)
export type AutopilotFrequency = "daily" | "weekdays" | "3_per_week" | "weekly";
export type PendingPostStatus = "pending" | "approved" | "rejected" | "auto_published" | "expired";

export interface AutopilotConfig {
  id: string;
  brand_id: string;
  is_enabled: boolean;
  platforms: string[] | null;
  frequency: AutopilotFrequency;
  generation_hour: number;
  auto_publish: boolean;
  approval_window_hours: number;
  whatsapp_enabled: boolean;
  whatsapp_phone: string | null;
  preferred_posting_time: string | null;
  topics: string[] | null;
  total_generated: number;
  total_published: number;
  created_at: string;
  updated_at: string;
}

export interface PendingPost {
  id: string;
  config_id: string;
  brand_id: string;
  platform: string;
  caption: string;
  hashtags: string[] | null;
  media_urls: string[] | null;
  ai_reasoning: string | null;
  virality_score: number | null;
  status: PendingPostStatus;
  whatsapp_message_id: string | null;
  reviewed_at: string | null;
  expires_at: string | null;
  scheduled_post_id: string | null;
  created_at: string;
  updated_at: string;
}

// Media Library (Sprint 9B)
export type MediaSourceType = "whatsapp" | "upload" | "ai_generated";
export type MediaTypeEnum = "image" | "video";

export interface MediaAsset {
  id: string;
  brand_id: string;
  storage_key: string;
  public_url: string;
  thumbnail_url: string | null;
  media_type: MediaTypeEnum;
  mime_type: string;
  file_size: number;
  original_filename: string | null;
  width: number | null;
  height: number | null;
  duration_seconds: number | null;
  source: MediaSourceType;
  ai_description: string | null;
  ai_tags: string[] | null;
  ai_analyzed: boolean;
  used_in_posts: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface VoiceNote {
  id: string;
  brand_id: string;
  storage_key: string;
  public_url: string;
  mime_type: string;
  file_size: number;
  duration_seconds: number | null;
  transcription: string | null;
  is_transcribed: boolean;
  sender_phone: string | null;
  parsed_instructions: Record<string, any> | null;
  pending_post_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface MediaLibraryStats {
  total_images: number;
  total_videos: number;
  total_voice_notes: number;
  total_size_bytes: number;
  from_whatsapp: number;
  from_upload: number;
  ai_analyzed_count: number;
}

// Photo Caption Generation (visual flow)
export type CaptionStyle = "gourmande" | "promo" | "story";
export type ToneOption = "fun" | "premium" | "urgence";

export interface PhotoCaptionSuggestion {
  style: CaptionStyle;
  caption: string;
  hashtags: string[];
  ai_notes: string;
}

export interface ImageAnalysis {
  description: string;
  tags: string[];
  detected_objects: string[];
  mood: string;
  suitable_platforms: string[];
}

export interface EngagementScore {
  total: number;
  has_hook: number;
  has_cta: number;
  hashtag_score: number;
  emoji_score: number;
  length_score: number;
  readability_score: number;
  trending_score: number;
}

export interface PhotoCaptionsResponse {
  image_analysis: ImageAnalysis;
  photo_url: string;
  suggestions: PhotoCaptionSuggestion[];
  engagement_scores: Record<string, EngagementScore>;
  model_used: string;
  prompt_version: string;
}

export const PLATFORM_CHAR_LIMITS: Record<string, number> = {
  instagram_post: 2200,
  instagram_story: 2200,
  instagram_reel: 2200,
  facebook: 63206,
  linkedin: 3000,
  tiktok: 150,
};
