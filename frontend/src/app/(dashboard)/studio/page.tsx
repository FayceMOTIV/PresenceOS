"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Instagram,
  Linkedin,
  Sparkles,
  Send,
  Loader2,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Edit3,
  Video,
  TrendingUp,
  X,
} from "lucide-react";
import { agentsApi } from "@/lib/api";
import { useAgentTask } from "@/hooks/use-agent-task";
import { cn } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import type { GeneratedPost, StudioMessage } from "@/types/agents";
import { TrendsSidebar } from "@/components/studio/trends-sidebar";
import { fireSuccessConfetti } from "@/lib/confetti";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import { AIThinking } from '@/components/ai/ai-thinking';
import { LoadingMessage } from '@/components/loading/loading-message';

const quickSuggestions = [
  "Génère 3 posts Instagram sur notre nouveau menu",
  "Crée un post LinkedIn corporate",
  "Propose des idées TikTok tendance",
  "Rédige un carrousel Instagram educatif",
];

const platformOptions = [
  { id: "instagram", label: "Instagram", icon: Instagram },
  { id: "linkedin", label: "LinkedIn", icon: Linkedin },
  { id: "tiktok", label: "TikTok", icon: Video },
];

function PlatformBadge({ platform }: { platform: string }) {
  const colors: Record<string, string> = {
    instagram: "bg-gradient-to-r from-purple-500 to-pink-500",
    linkedin: "bg-[#0A66C2]",
    tiktok: "bg-black dark:bg-white dark:text-black",
    facebook: "bg-[#1877F2]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium text-white",
        colors[platform.toLowerCase()] || "bg-muted"
      )}
    >
      {platform}
    </span>
  );
}

function PostPreviewCard({
  post,
  onCopy,
  onAccept,
  onReject,
}: {
  post: GeneratedPost;
  onCopy: () => void;
  onAccept: () => void;
  onReject: () => void;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    onCopy();
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl border bg-card p-4 space-y-3"
    >
      <div className="flex items-center justify-between">
        <PlatformBadge platform={post.platform} />
        {post.virality_score && (
          <span className="text-xs text-muted-foreground">
            Score: {post.virality_score}/10
          </span>
        )}
      </div>

      <p className="text-sm whitespace-pre-wrap leading-relaxed">{post.content}</p>

      {post.hashtags && post.hashtags.length > 0 && (
        <p className="text-xs text-primary">
          {post.hashtags.map((h) => (h.startsWith("#") ? h : `#${h}`)).join(" ")}
        </p>
      )}

      {post.suggested_media && (
        <div className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-2">
          Média suggéré: {post.suggested_media}
        </div>
      )}

      {post.review_notes && (
        <div className="text-xs text-muted-foreground bg-primary/5 border border-primary/10 rounded-lg p-2">
          <Sparkles className="w-3 h-3 inline mr-1" />
          {post.review_notes}
        </div>
      )}

      <div className="flex items-center gap-2 pt-1">
        <Button variant="outline" size="sm" onClick={handleCopy}>
          {copied ? <Check className="w-3 h-3 mr-1" /> : <Copy className="w-3 h-3 mr-1" />}
          {copied ? "Copié" : "Copier"}
        </Button>
        <Button variant="outline" size="sm" onClick={onAccept}>
          <ThumbsUp className="w-3 h-3 mr-1" />
          Publier
        </Button>
        <Button variant="outline" size="sm" onClick={onReject}>
          <ThumbsDown className="w-3 h-3 mr-1" />
          Rejeter
        </Button>
        <Button variant="ghost" size="sm">
          <Edit3 className="w-3 h-3 mr-1" />
          Modifier
        </Button>
      </div>
    </motion.div>
  );
}

function MessageBubble({ message }: { message: StudioMessage }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex gap-3 max-w-4xl", isUser ? "ml-auto flex-row-reverse" : "")}
    >
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser ? "bg-primary text-primary-foreground" : "bg-gradient-to-br from-primary to-purple-600"
        )}
      >
        {isUser ? (
          <span className="text-xs font-bold">U</span>
        ) : (
          <Sparkles className="w-4 h-4 text-white" />
        )}
      </div>

      <div className={cn("flex-1 space-y-3", isUser ? "text-right" : "")}>
        {message.type === "loading" ? (
          <AIThinking message="Je crée 3 textes différents pour votre photo... ✨" />
        ) : message.type === "posts" && message.posts ? (
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{message.content}</p>
            {message.posts.map((post, i) => (
              <PostPreviewCard
                key={i}
                post={post}
                onCopy={() => {
                  const text = `${post.content}\n\n${post.hashtags?.map((h) => (h.startsWith("#") ? h : `#${h}`)).join(" ") || ""}`;
                  navigator.clipboard.writeText(text);
                  toast({ title: "Copié !", description: "Post copié dans le presse-papier" });
                }}
                onAccept={() => {
                  toast({ title: "Post accepté", description: "Le post a été ajouté à vos brouillons" });
                }}
                onReject={() => {
                  toast({ title: "Post rejeté", description: "Le post a été supprimé" });
                }}
              />
            ))}
          </div>
        ) : (
          <div
            className={cn(
              "inline-block px-4 py-2 rounded-2xl text-sm",
              isUser
                ? "bg-primary text-primary-foreground"
                : "bg-muted"
            )}
          >
            {message.content}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
  onSuggestionClick,
  showSuggestions,
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: () => void;
  disabled: boolean;
  onSuggestionClick: (s: string) => void;
  showSuggestions: boolean;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [value]);

  return (
    <div className="space-y-3">
      {showSuggestions && (
        <div className="flex flex-wrap gap-2">
          {quickSuggestions.map((s) => (
            <button
              key={s}
              onClick={() => onSuggestionClick(s)}
              className="text-xs px-3 py-1.5 rounded-full border bg-card hover:bg-muted transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="flex items-end gap-2 bg-card border rounded-2xl p-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Demandez à l'IA de générer du contenu..."
          className="flex-1 bg-transparent resize-none text-sm px-2 py-1.5 focus:outline-none min-h-[36px] max-h-[120px]"
          rows={1}
          disabled={disabled}
        />
        <Button
          size="sm"
          onClick={onSend}
          disabled={!value.trim() || disabled}
          className="rounded-xl"
        >
          {disabled ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

export default function StudioPage() {
  const [messages, setMessages] = useState<StudioMessage[]>([]);
  const [input, setInput] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([
    "instagram",
    "linkedin",
  ]);
  const [showTrends, setShowTrends] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const { task } = useAgentTask(taskId);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Handle task completion
  useEffect(() => {
    if (!task || !taskId) return;

    if (task.status === "completed" && task.result) {
      const result = task.result as { posts?: GeneratedPost[]; metadata?: Record<string, unknown> };
      const posts = result.posts || [];

      setMessages((prev) =>
        prev
          .filter((m) => m.type !== "loading")
          .concat({
            id: crypto.randomUUID(),
            role: "assistant",
            content: posts.length
              ? `J'ai généré ${posts.length} post${posts.length > 1 ? "s" : ""} pour vous :`
              : "Je n'ai pas pu générer de contenu. Veuillez réessayer.",
            type: posts.length ? "posts" : "text",
            posts: posts.length ? posts : undefined,
            timestamp: new Date(),
          })
      );
      setIsProcessing(false);
      setTaskId(null);
      if (posts.length > 0) {
        fireSuccessConfetti();
      }
    } else if (task.status === "failed") {
      setMessages((prev) =>
        prev
          .filter((m) => m.type !== "loading")
          .concat({
            id: crypto.randomUUID(),
            role: "assistant",
            content: `Erreur: ${task.error || "Une erreur est survenue"}. Veuillez réessayer.`,
            type: "text",
            timestamp: new Date(),
          })
      );
      setIsProcessing(false);
      setTaskId(null);
    }
  }, [task, taskId]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isProcessing) return;

    const brandId = localStorage.getItem("brand_id");
    if (!brandId) {
      toast({
        title: "Aucune marque",
        description: "Sélectionnez une marque d'abord",
        variant: "destructive",
      });
      return;
    }

    // Add user message
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        type: "text",
        timestamp: new Date(),
      },
    ]);
    setInput("");
    setIsProcessing(true);

    // Add loading message
    setMessages((prev) => [
      ...prev,
      {
        id: "loading",
        role: "assistant",
        content: "",
        type: "loading",
        timestamp: new Date(),
      },
    ]);

    try {
      const response = await agentsApi.generateContent({
        brand_id: brandId,
        platforms: selectedPlatforms,
        num_posts: 3,
        topic: text,
      });

      setTaskId(response.data.task_id);
    } catch {
      setMessages((prev) =>
        prev
          .filter((m) => m.type !== "loading")
          .concat({
            id: crypto.randomUUID(),
            role: "assistant",
            content: "Impossible de lancer la génération. Vérifiez votre connexion.",
            type: "text",
            timestamp: new Date(),
          })
      );
      setIsProcessing(false);
    }
  };

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  };

  return (
    <div className="flex h-[calc(100vh-2rem)] gap-4">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between pb-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-primary" />
              Studio IA <HelpTooltip content="Cliquez et attendez 10 secondes. L'IA va écrire 3 textes différents pour votre photo" />
            </h1>
            <p className="text-sm text-muted-foreground">
              Générez du contenu avec l&apos;IA
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* Platform toggles */}
            {platformOptions.map((p) => (
              <button
                key={p.id}
                onClick={() => togglePlatform(p.id)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all",
                  selectedPlatforms.includes(p.id)
                    ? "bg-primary/10 border-primary text-primary"
                    : "border-border text-muted-foreground hover:border-muted-foreground"
                )}
              >
                <p.icon className="w-3.5 h-3.5" />
                {p.label}
              </button>
            ))}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTrends(!showTrends)}
              className={cn(showTrends && "bg-primary/10 border-primary text-primary")}
            >
              <TrendingUp className="w-4 h-4 mr-1" />
              Tendances
            </Button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-2">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center">
                  <Sparkles className="w-8 h-8 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Bienvenue dans le Studio IA</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Décrivez le contenu que vous souhaitez créer. Nos agents
                    IA analyseront votre marque, définiront la stratégie, et
                    généreront des posts optimisés.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
            </AnimatePresence>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Chat input */}
        <div className="pt-2 border-t">
          <ChatInput
            value={input}
            onChange={setInput}
            onSend={handleSend}
            disabled={isProcessing}
            showSuggestions={messages.length === 0}
            onSuggestionClick={(s) => {
              setInput(s);
            }}
          />
        </div>
      </div>

      {/* Trends sidebar */}
      <AnimatePresence>
        {showTrends && (
          <motion.div
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 340, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden flex-shrink-0"
          >
            <TrendsSidebar
              onClose={() => setShowTrends(false)}
              onCreatePost={(topic) => {
                setInput(topic);
                setShowTrends(false);
              }}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
