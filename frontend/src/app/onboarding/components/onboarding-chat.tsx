"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Globe,
  Lightbulb,
  ExternalLink,
  Check,
  SkipForward,
  Loader2,
  AlertTriangle,
  Brain,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Card, CardContent } from "@/components/ui/card";
import { onboardingApi } from "@/lib/api";
import type {
  OnboardingMode,
  OnboardingQuestion,
  OnboardingStartResponse,
  OnboardingAnswerResponse,
  ChatMessage,
} from "@/types/agents";

interface OnboardingChatProps {
  onComplete: (brandData: Record<string, unknown>) => void;
  initialWebsiteUrl?: string;
  initialSocialProfiles?: string[];
}

// Category labels for section headers
const CATEGORY_LABELS: Record<string, string> = {
  identity: "Identite",
  product: "Produits & Services",
  audience: "Audience",
  voice: "Ton & Voix",
  goals: "Objectifs",
};

// SkipWarning component
function SkipWarning({
  questionKey,
  onSkip,
  onCancel,
}: {
  questionKey: string;
  onSkip: () => void;
  onCancel: () => void;
}) {
  const importantKeys = ["target_audience", "products_services", "tone_style"];
  const isImportant = importantKeys.includes(questionKey);

  if (!isImportant) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-start gap-2 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs"
    >
      <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
      <div className="flex-1">
        <p className="text-amber-600 dark:text-amber-400">
          Cette information aide notre IA a mieux personnaliser votre contenu.
        </p>
        <div className="flex gap-2 mt-1.5">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-[10px] px-2 text-amber-600 hover:text-amber-700"
            onClick={onSkip}
          >
            Passer quand meme
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-[10px] px-2"
            onClick={onCancel}
          >
            Repondre
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

export function OnboardingChat({
  onComplete,
  initialWebsiteUrl,
  initialSocialProfiles,
}: OnboardingChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<OnboardingQuestion | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(true);
  const [progress, setProgress] = useState({ answered: 0, total: 1, percentage: 0 });
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [mode, setMode] = useState<OnboardingMode>("interview");
  const [showSkipWarning, setShowSkipWarning] = useState(false);
  const [lastCategory, setLastCategory] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement | HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const addMessage = useCallback((msg: Omit<ChatMessage, "id" | "timestamp">) => {
    setMessages((prev) => [
      ...prev,
      {
        ...msg,
        id: `msg-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        timestamp: new Date(),
      },
    ]);
  }, []);

  // Start session using dedicated /onboarding/ endpoint
  useEffect(() => {
    const startSession = async () => {
      try {
        const { data } = await onboardingApi.start({
          website_url: initialWebsiteUrl,
          social_profiles: initialSocialProfiles,
        }) as { data: OnboardingStartResponse };

        setSessionId(data.session_id);
        setMode(data.mode);

        addMessage({
          role: "assistant",
          content: data.message,
          type: "text",
        });

        if (data.first_question) {
          setTimeout(() => {
            // Show category header if new category
            const category = data.first_question!.category;
            if (category && CATEGORY_LABELS[category]) {
              setLastCategory(category);
            }
            setCurrentQuestion(data.first_question);
            addMessage({
              role: "assistant",
              content: data.first_question!.question,
              type: "question",
              question: data.first_question!,
            });
            setIsStarting(false);
          }, 800);
        } else {
          setIsStarting(false);
        }
      } catch (error) {
        console.error("Failed to start onboarding:", error);
        addMessage({
          role: "assistant",
          content: "Oups, une erreur est survenue. Veuillez rafraichir la page.",
          type: "text",
        });
        setIsStarting(false);
      }
    };

    startSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (answerOverride?: string) => {
    if (!sessionId || !currentQuestion || isLoading) return;

    const answer = answerOverride || inputValue;
    if (!answer.trim() && currentQuestion.required) return;

    setShowSkipWarning(false);

    addMessage({
      role: "user",
      content: answer || "(passe)",
      type: "text",
    });

    setInputValue("");
    setSelectedOptions([]);
    setIsLoading(true);

    try {
      const { data } = await onboardingApi.answer({
        session_id: sessionId,
        question_key: currentQuestion.key,
        answer: answer,
      }) as { data: OnboardingAnswerResponse };

      if (data.progress) {
        setProgress(data.progress);
      }

      if (data.insight) {
        addMessage({
          role: "assistant",
          content: data.insight,
          type: "insight",
        });
      }

      if (data.upsell) {
        addMessage({
          role: "assistant",
          content: data.upsell.message,
          type: "upsell",
          upsell: data.upsell,
        });
      }

      if (data.competitor_analysis) {
        addMessage({
          role: "assistant",
          content: data.competitor_analysis.message,
          type: "competitor_analysis",
          competitor_analysis: data.competitor_analysis,
        });
      }

      if (data.is_complete) {
        addMessage({
          role: "assistant",
          content: "Merci ! J'ai toutes les informations necessaires. Votre profil de marque est pret.",
          type: "complete",
        });
        setCurrentQuestion(null);

        try {
          const { data: completeData } = await onboardingApi.complete(sessionId);
          onComplete(completeData.brand_data);
        } catch {
          console.error("Failed to complete onboarding");
        }
      } else if (data.next_question) {
        setTimeout(() => {
          // Show category transition
          const nextCategory = data.next_question!.category;
          if (nextCategory && nextCategory !== lastCategory && CATEGORY_LABELS[nextCategory]) {
            setLastCategory(nextCategory);
            addMessage({
              role: "assistant",
              content: `--- ${CATEGORY_LABELS[nextCategory]} ---`,
              type: "text",
            });
          }

          setCurrentQuestion(data.next_question);
          addMessage({
            role: "assistant",
            content: data.next_question!.question,
            type: "question",
            question: data.next_question!,
          });
        }, 500);
      }
    } catch (error) {
      console.error("Failed to submit answer:", error);
      addMessage({
        role: "assistant",
        content: "Erreur lors du traitement. Reessayez.",
        type: "text",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    if (!currentQuestion || currentQuestion.required) return;

    // Show warning for important questions
    const importantKeys = ["target_audience", "products_services", "tone_style"];
    if (importantKeys.includes(currentQuestion.key) && !showSkipWarning) {
      setShowSkipWarning(true);
      return;
    }

    setShowSkipWarning(false);
    handleSubmit("");
  };

  const handleSelectOption = (value: string) => {
    if (currentQuestion?.type === "multi_select") {
      setSelectedOptions((prev) =>
        prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
      );
    } else {
      handleSubmit(value);
    }
  };

  const handleMultiSelectSubmit = () => {
    if (selectedOptions.length > 0) {
      handleSubmit(selectedOptions.join(","));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const renderInput = () => {
    if (!currentQuestion || isLoading) {
      return null;
    }

    if (currentQuestion.type === "select" || currentQuestion.type === "multi_select") {
      return (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {currentQuestion.options?.map((opt) => (
              <Button
                key={opt.value}
                variant={
                  currentQuestion.type === "multi_select" && selectedOptions.includes(opt.value)
                    ? "default"
                    : "outline"
                }
                size="sm"
                onClick={() => handleSelectOption(opt.value)}
                className={
                  currentQuestion.type !== "multi_select"
                    ? "hover:bg-primary/10 hover:text-primary hover:border-primary"
                    : selectedOptions.includes(opt.value)
                    ? "bg-primary text-primary-foreground border-primary"
                    : "hover:bg-primary/10 hover:text-primary hover:border-primary"
                }
              >
                {selectedOptions.includes(opt.value) && (
                  <Check className="w-3 h-3 mr-1" />
                )}
                {opt.label}
              </Button>
            ))}
          </div>
          {currentQuestion.type === "multi_select" && selectedOptions.length > 0 && (
            <Button
              onClick={handleMultiSelectSubmit}
              className="bg-gradient-to-r from-primary to-orange-400"
              size="sm"
            >
              <Send className="w-4 h-4 mr-2" />
              Valider ({selectedOptions.length})
            </Button>
          )}
          {currentQuestion.skip_label && !currentQuestion.required && (
            <>
              <Button variant="ghost" size="sm" onClick={handleSkip} className="text-muted-foreground">
                <SkipForward className="w-3 h-3 mr-1" />
                {currentQuestion.skip_label}
              </Button>
              {showSkipWarning && (
                <SkipWarning
                  questionKey={currentQuestion.key}
                  onSkip={() => {
                    setShowSkipWarning(false);
                    handleSubmit("");
                  }}
                  onCancel={() => setShowSkipWarning(false)}
                />
              )}
            </>
          )}
        </div>
      );
    }

    if (currentQuestion.type === "upsell") {
      return (
        <div className="flex gap-2">
          <Button
            onClick={() => handleSubmit("interested")}
            className="bg-gradient-to-r from-primary to-orange-400"
            size="sm"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Oui, je suis interesse
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleSubmit("not_now")}>
            Plus tard
          </Button>
        </div>
      );
    }

    const isTextarea = currentQuestion.type === "textarea";

    return (
      <div className="space-y-2">
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            {isTextarea ? (
              <Textarea
                ref={inputRef as React.RefObject<HTMLTextAreaElement>}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={currentQuestion.placeholder || "Votre reponse..."}
                className="min-h-[80px] resize-none bg-background/50"
              />
            ) : (
              <Input
                ref={inputRef as React.RefObject<HTMLInputElement>}
                type={currentQuestion.type === "url" ? "url" : "text"}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={currentQuestion.placeholder || "Votre reponse..."}
                className="bg-background/50"
              />
            )}
          </div>
          <div className="flex gap-1">
            <Button
              onClick={() => handleSubmit()}
              disabled={!inputValue.trim() && currentQuestion.required}
              size="icon"
              className="bg-gradient-to-r from-primary to-orange-400 hover:from-primary/90 hover:to-orange-400/90"
            >
              <Send className="w-4 h-4" />
            </Button>
            {currentQuestion.skip_label && !currentQuestion.required && (
              <Button variant="ghost" size="icon" onClick={handleSkip} title={currentQuestion.skip_label}>
                <SkipForward className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        {showSkipWarning && (
          <SkipWarning
            questionKey={currentQuestion.key}
            onSkip={() => {
              setShowSkipWarning(false);
              handleSubmit("");
            }}
            onCancel={() => setShowSkipWarning(false)}
          />
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full max-h-[70vh] min-h-[500px]">
      {/* Progress bar — Brain completion */}
      <div className="px-4 py-3 border-b bg-background/50 backdrop-blur-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary" />
            <Badge variant="outline" className="text-xs capitalize">
              {mode === "full_auto"
                ? "Auto-detection"
                : mode === "semi_auto"
                ? "Semi-automatique"
                : "Interview"}
            </Badge>
          </div>
          <span className="text-xs text-muted-foreground">
            Brain {progress.percentage}%
          </span>
        </div>
        <Progress value={progress.percentage} className="h-1.5" />
        {lastCategory && CATEGORY_LABELS[lastCategory] && (
          <p className="text-[10px] text-muted-foreground mt-1">
            Section : {CATEGORY_LABELS[lastCategory]}
          </p>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-orange-400 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
              )}

              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : msg.type === "insight"
                    ? "bg-amber-500/10 border border-amber-500/20"
                    : msg.type === "complete"
                    ? "bg-green-500/10 border border-green-500/20"
                    : "bg-muted"
                }`}
              >
                {msg.type === "insight" && (
                  <div className="flex items-center gap-2 mb-1">
                    <Lightbulb className="w-4 h-4 text-amber-500" />
                    <span className="text-xs font-medium text-amber-500">Insight</span>
                  </div>
                )}

                {msg.type === "complete" && (
                  <div className="flex items-center gap-2 mb-1">
                    <Check className="w-4 h-4 text-green-500" />
                    <span className="text-xs font-medium text-green-500">Termine</span>
                  </div>
                )}

                {msg.type === "upsell" && msg.upsell && (
                  <Card className="mb-2 border-primary/30 bg-primary/5">
                    <CardContent className="p-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4 text-primary" />
                        <span className="font-medium text-sm">{msg.upsell.title}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{msg.upsell.message}</p>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-primary/20 text-primary border-primary/30">
                          {msg.upsell.price}
                        </Badge>
                      </div>
                      <ul className="text-xs space-y-1">
                        {msg.upsell.features.map((f, i) => (
                          <li key={i} className="flex items-center gap-1">
                            <Check className="w-3 h-3 text-green-500" />
                            {f}
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {msg.type === "competitor_analysis" && msg.competitor_analysis && (
                  <Card className="mb-2 border-blue-500/30 bg-blue-500/5">
                    <CardContent className="p-3 space-y-2">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-blue-500" />
                        <span className="font-medium text-sm">Analyse concurrentielle</span>
                      </div>
                      <div className="space-y-2">
                        {msg.competitor_analysis.competitors.map((comp, i) => (
                          <div key={i} className="text-xs p-2 rounded bg-background/50">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{comp.name}</span>
                              {comp.url && (
                                <a
                                  href={comp.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-500 hover:underline"
                                >
                                  <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                              {comp.scraped && (
                                <Badge variant="outline" className="text-[10px] px-1 py-0">
                                  Analyse
                                </Badge>
                              )}
                            </div>
                            <p className="text-muted-foreground mt-1">{comp.summary}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {msg.type !== "upsell" && msg.type !== "competitor_analysis" && (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                )}
                {(msg.type === "upsell" || msg.type === "competitor_analysis") && (
                  <p className="text-sm text-muted-foreground">{msg.content}</p>
                )}
              </div>

              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4" />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Loading indicator */}
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-orange-400 flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-muted rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">Analyse en cours...</span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Starting indicator */}
        {isStarting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-center py-8"
          >
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
              <span className="text-muted-foreground">Preparation de votre session...</span>
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area - sticky bottom */}
      <div className="border-t bg-background/80 backdrop-blur-sm p-4">
        {renderInput()}
      </div>
    </div>
  );
}
