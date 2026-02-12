"use client";

import { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, AlertCircle, CheckCircle2, User } from "lucide-react";
import { type AIMessage } from "@/hooks/useContentCreator";
import { ActionButtons } from "./ActionButtons";
import { ThinkingIndicator } from "./ThinkingIndicator";

interface AIMessageStreamProps {
  messages: AIMessage[];
  isLoading: boolean;
  onClickButton: (id: string, title: string) => void;
}

export function AIMessageStream({
  messages,
  isLoading,
  onClickButton,
}: AIMessageStreamProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto space-y-1 pr-1 scroll-smooth"
    >
      <AnimatePresence mode="popLayout">
        {messages.map((msg) => {
          const isUserMsg = msg.sender === "user";

          if (msg.type === "error") {
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-start gap-3 py-2"
              >
                <div className="w-8 h-8 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
                  <AlertCircle className="w-4 h-4 text-destructive" />
                </div>
                <p className="text-sm text-destructive pt-1.5">{msg.content}</p>
              </motion.div>
            );
          }

          if (msg.type === "success") {
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-start gap-3 py-2"
              >
                <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                </div>
                <p className="text-sm text-green-400 pt-1.5 whitespace-pre-line">
                  {msg.content}
                </p>
              </motion.div>
            );
          }

          if (msg.type === "buttons") {
            return (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 }}
                className="py-2"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    {msg.header && (
                      <p className="text-xs font-medium text-primary mb-1">
                        {msg.header}
                      </p>
                    )}
                    <p className="text-sm text-foreground/90 whitespace-pre-line leading-relaxed">
                      {msg.content}
                    </p>
                    {msg.buttons && (
                      <ActionButtons
                        buttons={msg.buttons}
                        onClickButton={onClickButton}
                      />
                    )}
                  </div>
                </div>
              </motion.div>
            );
          }

          // Regular text message
          return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex items-start gap-3 py-2 ${isUserMsg ? "flex-row-reverse" : ""}`}
            >
              {isUserMsg ? (
                <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-muted-foreground" />
                </div>
              ) : (
                <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-primary" />
                </div>
              )}
              <p
                className={`text-sm pt-1.5 whitespace-pre-line leading-relaxed max-w-[85%] ${
                  isUserMsg
                    ? "bg-secondary/80 rounded-2xl rounded-tr-sm px-4 py-2 text-foreground"
                    : "text-foreground/90"
                }`}
              >
                {msg.content}
              </p>
            </motion.div>
          );
        })}

        {isLoading && <ThinkingIndicator key="thinking" />}
      </AnimatePresence>
    </div>
  );
}
