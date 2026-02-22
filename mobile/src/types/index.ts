// PresenceOS Mobile — Type Definitions

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  brand_type: string;
  description?: string;
  logo_url?: string;
}

export interface Dish {
  id: string;
  brand_id: string;
  name: string;
  category: string;
  description?: string;
  price?: number;
  is_available: boolean;
  is_featured: boolean;
  cover_asset_id?: string;
  ai_post_count: number;
  last_posted_at?: string;
  display_order: number;
}

export interface MediaAsset {
  id: string;
  brand_id: string;
  public_url: string;
  thumbnail_url?: string;
  improved_url?: string;
  media_type: "image" | "video";
  quality_score?: number;
  processing_status: string;
  asset_label?: string;
  linked_dish_id?: string;
  ai_description?: string;
  used_in_posts: number;
}

export interface AIProposal {
  id: string;
  brand_id: string;
  proposal_type: "post" | "reel" | "story";
  platform: string;
  caption?: string;
  hashtags?: string[];
  image_url?: string;
  video_url?: string;
  improved_image_url?: string;
  source: string;
  status: "pending" | "approved" | "rejected" | "published" | "scheduled" | "expired";
  scheduled_at?: string;
  confidence_score: number;
  created_at: string;
}

export interface DailyBrief {
  id: string;
  brand_id: string;
  date: string;
  response?: string;
  status: "pending" | "answered" | "ignored";
  responded_at?: string;
  generated_proposal_id?: string;
}

export interface CompiledKB {
  brand_id: string;
  kb_version: number;
  completeness_score: number;
  compiled_at?: string;
}

export interface CMInteraction {
  id: string;
  platform: string;
  commenter_name: string;
  content: string;
  rating?: number;
  sentiment_score: number;
  classification: string;
  ai_response_draft?: string;
  final_response?: string;
  response_status: string;
  created_at: string;
}

export interface VideoCreditsInfo {
  credits_remaining: number;
  credits_total: number;
  plan: string;
  reset_date?: string;
}

export interface VideoGenerationResult {
  video_url: string | null;
  duration: number;
  credits_used: number;
  credits_remaining: number;
  status: "completed" | "failed" | "no_api_key";
}

export interface CMStats {
  total_interactions: number;
  pending_count: number;
  published_count: number;
  response_rate: number;
  avg_sentiment: number;
}
