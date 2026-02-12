export interface AgentTask {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  message: string;
  created_at?: string;
  result?: ContentCrewResult | BrandExtractionResult | null;
  error?: string | null;
}

export interface GeneratedPost {
  platform: "linkedin" | "instagram" | "facebook" | "tiktok";
  content: string;
  hashtags: string[];
  suggested_media: string;
  cta: string;
  topic: string;
  virality_score?: number;
  brand_voice_score?: number;
  review_notes?: string;
}

export interface ContentCrewResult {
  posts: GeneratedPost[];
  metadata: {
    total_generated: number;
    approved: number;
    rejected: number;
    avg_virality: number;
    raw_output?: string;
    error?: string;
  };
}

export interface BrandExtractionResult {
  business_name: string;
  description: string;
  industry?: string;
  products?: string[];
  target_audience?: string;
  tone_of_voice?: string;
  colors?: { primary: string; secondary: string };
  tagline?: string;
  error?: string;
}

export interface ContentGenerationRequest {
  brand_id: string;
  platforms: string[];
  num_posts: number;
  topic?: string;
  industry?: string;
  tone?: string;
}

export interface TrendItem {
  topic: string;
  relevance_score: number;
  platforms: string[];
  suggested_angle: string;
  hashtags: string[];
}

export interface TrendsScanResult {
  trends: TrendItem[];
  summary: string;
}

export interface StudioMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  type: "text" | "posts" | "loading";
  posts?: GeneratedPost[];
  timestamp: Date;
}

// ── Onboarding Intelligent ──────────────────────────────────────────

export type OnboardingMode = "full_auto" | "semi_auto" | "interview";

export interface OnboardingQuestionOption {
  value: string;
  label: string;
}

export interface OnboardingQuestion {
  key: string;
  question: string;
  type: "text" | "textarea" | "url" | "select" | "multi_select" | "upsell";
  category: string;
  required: boolean;
  modes: string[];
  placeholder?: string;
  skip_label?: string;
  options?: OnboardingQuestionOption[];
  condition?: string;
  upsell_data?: {
    price: string;
    features: string[];
  };
}

export interface OnboardingStartResponse {
  session_id: string;
  mode: OnboardingMode;
  questions: OnboardingQuestion[];
  first_question: OnboardingQuestion | null;
  extracted_data: Record<string, unknown> | null;
  message: string;
}

export interface OnboardingAnswerResponse {
  insight: string | null;
  upsell: {
    type: string;
    title: string;
    message: string;
    price: string;
    features: string[];
    cta: string;
  } | null;
  competitor_analysis: {
    type: string;
    competitors: Array<{
      name: string;
      url: string | null;
      summary: string;
      scraped: boolean;
    }>;
    count: number;
    message: string;
  } | null;
  next_question: OnboardingQuestion | null;
  progress: {
    answered: number;
    total: number;
    percentage: number;
  };
  is_complete: boolean;
}

export interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  type?: "text" | "question" | "insight" | "upsell" | "competitor_analysis" | "complete";
  question?: OnboardingQuestion;
  upsell?: OnboardingAnswerResponse["upsell"];
  competitor_analysis?: OnboardingAnswerResponse["competitor_analysis"];
  timestamp: Date;
}
