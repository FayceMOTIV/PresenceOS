"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Star,
  MessageSquare,
  Sparkles,
  Loader2,
  Send,
  ThumbsUp,
  ThumbsDown,
  Minus,
  MapPin,
  Facebook,
  BarChart3,
} from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Review {
  id: string;
  brand_id: string;
  platform: string;
  author: string;
  rating: number;
  text: string;
  sentiment: string;
  responded: boolean;
  response: string | null;
  created_at: string;
}

interface ReputationStats {
  total: number;
  avg_rating: number;
  by_sentiment: { positive: number; neutral: number; negative: number };
  by_platform: { google: number; facebook: number; tripadvisor: number };
  response_rate: number;
  pending_responses: number;
}

interface ReviewFeedProps {
  brandId: string;
}

const PLATFORM_ICONS: Record<string, typeof MapPin> = {
  google: MapPin,
  facebook: Facebook,
  tripadvisor: Star,
};

const SENTIMENT_CONFIG: Record<string, { icon: typeof ThumbsUp; color: string; label: string }> = {
  positive: { icon: ThumbsUp, color: "text-emerald-400", label: "Positif" },
  neutral: { icon: Minus, color: "text-zinc-400", label: "Neutre" },
  negative: { icon: ThumbsDown, color: "text-red-400", label: "Negatif" },
};

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`w-3 h-3 ${i <= rating ? "text-amber-400 fill-amber-400" : "text-gray-200"}`}
        />
      ))}
    </div>
  );
}

function ReviewCard({
  review,
  onSuggest,
  onRespond,
}: {
  review: Review;
  onSuggest: () => void;
  onRespond: (text: string) => void;
}) {
  const [responseText, setResponseText] = useState("");
  const [showInput, setShowInput] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);

  const PlatformIcon = PLATFORM_ICONS[review.platform] || MapPin;
  const sentimentCfg = SENTIMENT_CONFIG[review.sentiment] || SENTIMENT_CONFIG.neutral;
  const SentimentIcon = sentimentCfg.icon;

  const handleSuggest = async () => {
    setIsSuggesting(true);
    setShowInput(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/reputation/review/${review.id}/suggest`, {
        method: "POST",
      });
      const data = await res.json();
      setResponseText(data.suggested_response || "");
    } catch {
      setResponseText("");
    } finally {
      setIsSuggesting(false);
    }
  };

  const handleSubmit = () => {
    if (responseText.trim()) {
      onRespond(responseText);
      setShowInput(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white border border-gray-200/60 rounded-xl p-4 space-y-3 shadow-sm"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <PlatformIcon className="w-4 h-4 text-gray-500" />
          <span className="text-sm font-semibold text-gray-800">{review.author}</span>
          <StarRating rating={review.rating} />
        </div>
        <div className="flex items-center gap-2">
          <SentimentIcon className={`w-3 h-3 ${sentimentCfg.color}`} />
          <span className={`text-[10px] font-medium ${sentimentCfg.color}`}>
            {sentimentCfg.label}
          </span>
        </div>
      </div>

      {/* Review text */}
      <p className="text-sm text-gray-800 leading-relaxed">{review.text}</p>

      {/* Response */}
      {review.responded && review.response && (
        <div className="bg-gray-100/80 border border-gray-200 rounded-lg p-3">
          <p className="text-xs text-gray-600">
            <span className="font-medium text-amber-400">Votre reponse :</span>{" "}
            {review.response}
          </p>
        </div>
      )}

      {/* Response input */}
      <AnimatePresence>
        {showInput && !review.responded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            <textarea
              value={responseText}
              onChange={(e) => setResponseText(e.target.value)}
              placeholder="Votre reponse..."
              rows={3}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:border-amber-500/50 focus:outline-none resize-none"
            />
            <div className="flex gap-2">
              <button
                onClick={handleSubmit}
                disabled={!responseText.trim()}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-amber-400 hover:from-amber-400 hover:to-amber-300 text-black text-xs font-medium transition-colors disabled:opacity-50"
              >
                <Send className="w-3 h-3" />
                Envoyer
              </button>
              <button
                onClick={() => setShowInput(false)}
                className="px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 text-xs hover:bg-gray-100 transition-colors"
              >
                Annuler
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Actions */}
      {!review.responded && !showInput && (
        <div className="flex gap-2">
          <button
            onClick={handleSuggest}
            disabled={isSuggesting}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium hover:bg-amber-500/20 transition-colors"
          >
            {isSuggesting ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Sparkles className="w-3 h-3" />
            )}
            Reponse IA
          </button>
          <button
            onClick={() => setShowInput(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 text-xs hover:bg-gray-100 transition-colors"
          >
            <MessageSquare className="w-3 h-3" />
            Repondre
          </button>
        </div>
      )}

      {/* Date */}
      <p className="text-[10px] text-gray-400">
        {new Date(review.created_at).toLocaleDateString("fr-FR", {
          day: "numeric",
          month: "long",
          year: "numeric",
        })}
      </p>
    </motion.div>
  );
}

export function ReviewFeed({ brandId }: ReviewFeedProps) {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [stats, setStats] = useState<ReputationStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    if (!brandId) return;
    setIsLoading(true);
    Promise.all([
      fetch(`${API_BASE_URL}/api/v1/reputation/reviews/${brandId}`).then((r) => r.json()),
      fetch(`${API_BASE_URL}/api/v1/reputation/stats/${brandId}`).then((r) => r.json()),
    ])
      .then(([reviewsData, statsData]) => {
        setReviews(reviewsData);
        setStats(statsData);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [brandId]);

  const handleRespond = async (reviewId: string, text: string) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/reputation/review/${reviewId}/respond`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ response_text: text }),
      });
      const updated = await res.json();
      setReviews((prev) => prev.map((r) => (r.id === reviewId ? updated : r)));
    } catch (err) {
      console.error("Error responding:", err);
    }
  };

  const filtered = filter
    ? reviews.filter((r) => r.sentiment === filter)
    : reviews;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-5">
      {/* Stats bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-white border border-gray-200/60 rounded-xl p-3 text-center shadow-sm">
            <div className="flex items-center justify-center gap-1 mb-1">
              <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
              <span className="text-xl font-bold text-gray-900">{stats.avg_rating}</span>
            </div>
            <div className="text-[10px] text-gray-500 uppercase">Note moyenne</div>
          </div>
          <div className="bg-white border border-gray-200/60 rounded-xl p-3 text-center shadow-sm">
            <div className="text-xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-[10px] text-gray-500 uppercase">Total avis</div>
          </div>
          <div className="bg-white border border-gray-200/60 rounded-xl p-3 text-center shadow-sm">
            <div className="text-xl font-bold text-gray-900">{stats.response_rate}%</div>
            <div className="text-[10px] text-gray-500 uppercase">Taux reponse</div>
          </div>
          <div className="bg-white border border-gray-200/60 rounded-xl p-3 text-center shadow-sm">
            <div className="text-xl font-bold text-amber-400">{stats.pending_responses}</div>
            <div className="text-[10px] text-gray-500 uppercase">En attente</div>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="flex gap-2">
        {[
          { value: null, label: "Tous" },
          { value: "positive", label: "Positifs" },
          { value: "neutral", label: "Neutres" },
          { value: "negative", label: "Negatifs" },
        ].map((f) => (
          <button
            key={f.value ?? "all"}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              filter === f.value
                ? "bg-amber-500/15 text-amber-400 border border-amber-500/40"
                : "bg-gray-100/60 text-gray-600 border border-gray-200/60 hover:bg-gray-100"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Reviews list */}
      <div className="space-y-3">
        {filtered.map((review) => (
          <ReviewCard
            key={review.id}
            review={review}
            onSuggest={() => {}}
            onRespond={(text) => handleRespond(review.id, text)}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-8">
          <MessageSquare className="w-8 h-8 text-gray-200 mx-auto mb-2" />
          <p className="text-sm text-gray-500">Aucun avis avec ce filtre</p>
        </div>
      )}
    </motion.div>
  );
}
