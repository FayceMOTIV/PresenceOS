"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  CheckCircle,
  XCircle,
  Edit3,
  ThumbsUp,
  ThumbsDown,
  Star,
  AlertTriangle,
  MessageSquare,
  Clock,
  Send,
  Loader2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CMInteraction } from "@/types";
import { cmApi } from "@/lib/api";

interface InteractionCardProps {
  interaction: CMInteraction;
  onUpdate: (updated: CMInteraction) => void;
}

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "bg-emerald-100 text-emerald-700 border-emerald-200",
  negative: "bg-red-100 text-red-700 border-red-200",
  neutral: "bg-gray-100 text-gray-700 border-gray-200",
  question: "bg-blue-100 text-blue-700 border-blue-200",
  crisis: "bg-red-200 text-red-800 border-red-300",
};

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: "En attente", color: "bg-amber-100 text-amber-700", icon: <Clock className="w-3 h-3" /> },
  approved: { label: "Approuve", color: "bg-green-100 text-green-700", icon: <CheckCircle className="w-3 h-3" /> },
  edited: { label: "Modifie", color: "bg-blue-100 text-blue-700", icon: <Edit3 className="w-3 h-3" /> },
  rejected: { label: "Rejete", color: "bg-red-100 text-red-700", icon: <XCircle className="w-3 h-3" /> },
  auto_published: { label: "Auto-publie", color: "bg-emerald-100 text-emerald-700", icon: <Send className="w-3 h-3" /> },
};

const PLATFORM_ICONS: Record<string, string> = {
  google: "G",
  instagram: "IG",
  facebook: "FB",
};

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((s) => (
        <Star
          key={s}
          className={cn(
            "w-3.5 h-3.5",
            s <= rating ? "fill-yellow-400 text-yellow-400" : "text-gray-200"
          )}
        />
      ))}
    </div>
  );
}

function SentimentBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.7 ? "bg-emerald-500" : score >= 0.4 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-gray-100">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-500">{pct}%</span>
    </div>
  );
}

export function InteractionCard({ interaction, onUpdate }: InteractionCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(interaction.ai_response_draft || "");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);

  const status = STATUS_CONFIG[interaction.response_status] || STATUS_CONFIG.pending;
  const isPending = interaction.response_status === "pending";
  const isPublished = ["approved", "edited", "auto_published"].includes(interaction.response_status);

  const handleApprove = async (customText?: string) => {
    setIsSubmitting(true);
    try {
      const res = await cmApi.approveInteraction(interaction.id, customText);
      onUpdate(res.data);
      setIsEditing(false);
    } catch {
      // silently fail
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      const res = await cmApi.rejectInteraction(interaction.id);
      onUpdate(res.data);
    } catch {
      // silently fail
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRate = async (rating: 1 | -1) => {
    try {
      const res = await cmApi.rateInteraction(interaction.id, rating);
      onUpdate(res.data);
    } catch {
      // silently fail
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={cn(
          "overflow-hidden transition-all duration-200 hover:shadow-md",
          interaction.classification === "crisis" && "ring-2 ring-red-300",
          isPending && "border-l-4 border-l-amber-400"
        )}
      >
        <CardContent className="p-4 space-y-3">
          {/* Header: platform, author, stars, status */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              {/* Platform badge */}
              <div className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center text-xs font-bold shrink-0",
                interaction.platform === "google" && "bg-blue-50 text-blue-700",
                interaction.platform === "instagram" && "bg-pink-50 text-pink-700",
                interaction.platform === "facebook" && "bg-indigo-50 text-indigo-700",
              )}>
                {PLATFORM_ICONS[interaction.platform] || "?"}
              </div>

              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-gray-900 truncate">
                    {interaction.commenter_name}
                  </span>
                  {interaction.rating && <StarRating rating={interaction.rating} />}
                </div>
                <div className="flex items-center gap-2 mt-0.5">
                  <Badge variant="outline" className={cn("text-[10px] px-1.5 py-0", SENTIMENT_COLORS[interaction.classification])}>
                    {interaction.classification === "crisis" && <AlertTriangle className="w-2.5 h-2.5 mr-0.5" />}
                    {interaction.classification}
                  </Badge>
                  <SentimentBar score={interaction.sentiment_score} />
                </div>
              </div>
            </div>

            {/* Status badge */}
            <Badge className={cn("text-[10px] shrink-0 gap-1", status.color)}>
              {status.icon}
              {status.label}
            </Badge>
          </div>

          {/* Customer content */}
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
              <p className="text-sm text-gray-700 leading-relaxed">{interaction.content}</p>
            </div>
          </div>

          {/* AI Response */}
          {interaction.ai_response_draft && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Reponse IA
                </span>
                {interaction.confidence_score > 0 && (
                  <span className={cn(
                    "text-xs font-medium px-1.5 py-0.5 rounded",
                    interaction.confidence_score >= 0.85
                      ? "bg-emerald-50 text-emerald-600"
                      : interaction.confidence_score >= 0.6
                        ? "bg-amber-50 text-amber-600"
                        : "bg-red-50 text-red-600"
                  )}>
                    {Math.round(interaction.confidence_score * 100)}% confiance
                  </span>
                )}
              </div>

              {isEditing ? (
                <div className="space-y-2">
                  <Textarea
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    rows={3}
                    className="text-sm resize-none"
                  />
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="gradient"
                      disabled={isSubmitting || !editText.trim()}
                      onClick={() => handleApprove(editText)}
                    >
                      {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <Send className="w-3 h-3 mr-1" />}
                      Publier
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => { setIsEditing(false); setEditText(interaction.ai_response_draft || ""); }}>
                      Annuler
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="bg-violet-50/50 rounded-lg p-3 border border-violet-100/60">
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {interaction.final_response || interaction.ai_response_draft}
                  </p>
                </div>
              )}

              {/* AI reasoning toggle */}
              {interaction.ai_reasoning && (
                <button
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                >
                  {showReasoning ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  Raisonnement IA
                </button>
              )}
              {showReasoning && interaction.ai_reasoning && (
                <p className="text-xs text-gray-500 italic bg-gray-50 rounded p-2">
                  {interaction.ai_reasoning}
                </p>
              )}
            </div>
          )}

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-1 border-t border-gray-100">
            {/* Left: approve/reject actions */}
            <div className="flex items-center gap-1.5">
              {isPending && !isEditing && (
                <>
                  <Button
                    size="sm"
                    variant="gradient"
                    disabled={isSubmitting}
                    onClick={() => handleApprove()}
                    className="h-7 text-xs"
                  >
                    {isSubmitting ? <Loader2 className="w-3 h-3 animate-spin" /> : <CheckCircle className="w-3 h-3 mr-1" />}
                    Approuver
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={isSubmitting}
                    onClick={() => setIsEditing(true)}
                    className="h-7 text-xs text-gray-500"
                  >
                    <Edit3 className="w-3 h-3 mr-1" />
                    Modifier
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={isSubmitting}
                    onClick={handleReject}
                    className="h-7 text-xs text-red-500 hover:text-red-600 hover:bg-red-50"
                  >
                    <XCircle className="w-3 h-3 mr-1" />
                    Rejeter
                  </Button>
                </>
              )}
            </div>

            {/* Right: feedback */}
            <div className="flex items-center gap-1">
              {isPublished && (
                <>
                  <button
                    onClick={() => handleRate(1)}
                    className={cn(
                      "p-1.5 rounded-md transition-colors",
                      interaction.human_rating === 1
                        ? "bg-emerald-100 text-emerald-600"
                        : "text-gray-300 hover:text-emerald-500 hover:bg-emerald-50"
                    )}
                  >
                    <ThumbsUp className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleRate(-1)}
                    className={cn(
                      "p-1.5 rounded-md transition-colors",
                      interaction.human_rating === -1
                        ? "bg-red-100 text-red-600"
                        : "text-gray-300 hover:text-red-500 hover:bg-red-50"
                    )}
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                  </button>
                </>
              )}
              <span className="text-[10px] text-gray-400 ml-2">
                {new Date(interaction.created_at).toLocaleDateString("fr-FR", {
                  day: "numeric",
                  month: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
