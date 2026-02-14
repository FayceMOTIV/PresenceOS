"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Brain, Send, Loader2, CheckCircle2, Sparkles, MessageCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";

import { interviewApi } from "@/lib/api";
import { InterviewMessage, BrandCompleteness } from "@/types";

interface BrandInterviewChatProps {
  onKnowledgeUpdated: () => void;
}

export function BrandInterviewChat({ onKnowledgeUpdated }: BrandInterviewChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<InterviewMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [completeness, setCompleteness] = useState<BrandCompleteness>({
    overall: 0,
    identity: 0,
    voice: 0,
    knowledge: 0,
  });
  const [isComplete, setIsComplete] = useState(false);
  const [hasActiveSession, setHasActiveSession] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const brandId = typeof window !== "undefined" ? localStorage.getItem("brand_id") : null;

  // Fetch status on mount
  useEffect(() => {
    if (!brandId) return;
    interviewApi
      .getStatus(brandId)
      .then((res) => {
        setCompleteness(res.data.completeness);
        setHasActiveSession(res.data.has_active_session);
      })
      .catch(() => {});
  }, [brandId]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  // Start or resume interview when sheet opens
  const handleOpen = useCallback(async () => {
    if (!brandId) return;
    setIsOpen(true);
    setIsLoading(true);
    try {
      const res = await interviewApi.start(brandId);
      setMessages(res.data.messages || []);
      setCompleteness(res.data.completeness);
    } catch (error) {
      console.error("Failed to start interview:", error);
    } finally {
      setIsLoading(false);
    }
  }, [brandId]);

  // Send message
  const handleSend = useCallback(async () => {
    if (!brandId || !inputValue.trim() || isSending) return;

    const userMsg: InterviewMessage = {
      role: "user",
      content: inputValue.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsSending(true);

    try {
      const res = await interviewApi.sendMessage(brandId, userMsg.content);
      const { ai_message, extracted_items, completeness: newCompleteness, is_complete } = res.data;

      const aiMsg: InterviewMessage = {
        role: "assistant",
        content: ai_message,
        timestamp: new Date().toISOString(),
        extracted_items: extracted_items?.map((e: any) => ({ type: e.type, title: e.title })),
      };

      setMessages((prev) => [...prev, aiMsg]);
      setCompleteness(newCompleteness);
      setIsComplete(is_complete);

      // If items were extracted, refresh the brain page
      if (extracted_items && extracted_items.length > 0) {
        onKnowledgeUpdated();
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Désolé, une erreur est survenue. Réessaie !",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsSending(false);
      textareaRef.current?.focus();
    }
  }, [brandId, inputValue, isSending, onKnowledgeUpdated]);

  // Handle Enter key
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const overallScore = completeness.overall || 0;

  return (
    <>
      {/* Trigger Card */}
      <Card className="border-dashed border-2 border-primary/30 bg-primary/5 hover:bg-primary/10 transition-colors cursor-pointer"
        onClick={handleOpen}
      >
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="flex-shrink-0 w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Brain className="w-6 h-6 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-lg">
                {hasActiveSession ? "Reprendre l'interview" : "Apprenez-moi tout sur votre marque"}
              </h3>
              <p className="text-sm text-muted-foreground">
                L&apos;IA vous pose des questions pour générer du contenu qui vous ressemble
              </p>
            </div>
            <div className="flex-shrink-0 flex items-center gap-3">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary">{overallScore}%</div>
                <div className="text-xs text-muted-foreground">complete</div>
              </div>
              <Button variant="default" size="sm">
                <MessageCircle className="w-4 h-4 mr-2" />
                {hasActiveSession ? "Reprendre" : "Commencer"}
              </Button>
            </div>
          </div>
          {overallScore > 0 && (
            <div className="mt-4">
              <Progress value={overallScore} className="h-2" />
              <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                <span>Identite {completeness.identity}%</span>
                <span>Ton {completeness.voice}%</span>
                <span>Connaissances {completeness.knowledge}%</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Chat Sheet */}
      <Sheet open={isOpen} onOpenChange={setIsOpen}>
        <SheetContent className="w-full sm:max-w-lg flex flex-col p-0">
          {/* Header */}
          <SheetHeader className="px-6 py-4 border-b">
            <SheetTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-primary" />
              Interview IA
            </SheetTitle>
            <div className="mt-2">
              <Progress value={overallScore} className="h-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {overallScore}% complete
                {isComplete && " — Interview terminée !"}
              </p>
            </div>
          </SheetHeader>

          {/* Messages */}
          <ScrollArea className="flex-1 px-4 py-4" ref={scrollRef}>
            <div className="space-y-4">
              {isLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  <span className="ml-2 text-muted-foreground">Chargement...</span>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted"
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                      {/* Show extracted items badges */}
                      {msg.extracted_items && msg.extracted_items.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {msg.extracted_items.map((item, j) => (
                            <Badge key={j} variant="secondary" className="text-xs">
                              <CheckCircle2 className="w-3 h-3 mr-1" />
                              {item.title}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              {isSending && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-2xl px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 animate-pulse text-primary" />
                      <span className="text-sm text-muted-foreground">L&apos;IA reflechit...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="border-t px-4 py-3">
            {isComplete ? (
              <div className="text-center py-2">
                <p className="text-sm text-muted-foreground flex items-center justify-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  Interview terminée ! Les infos sont enregistrées.
                </p>
              </div>
            ) : (
              <div className="flex gap-2">
                <Textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Écris ta réponse..."
                  className="min-h-[44px] max-h-[120px] resize-none"
                  rows={1}
                  disabled={isSending}
                />
                <Button
                  size="icon"
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isSending}
                >
                  {isSending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </div>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
