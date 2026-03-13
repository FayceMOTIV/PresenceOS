// PresenceOS Mobile — Ilyas Chat Hook
// Manages Ilyas sessions, messages, and AI interactions with vision support

import { useState, useCallback, useRef } from "react";
import { ilyasApi } from "@/lib/api";
import { useBusinessStore } from "@/stores/businessStore";
import type { CMChatSession, CMChatMessage } from "@/types";

interface UseIlyasChatReturn {
  sessions: CMChatSession[];
  activeSession: CMChatSession | null;
  messages: CMChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;

  loadSessions: () => Promise<void>;
  selectSession: (sessionId: string) => Promise<void>;
  sendMessage: (text: string, imageUrl?: string) => Promise<void>;
  newSession: () => void;
  deleteSession: (sessionId: string) => Promise<void>;
}

export function useIlyasChat(): UseIlyasChatReturn {
  const activeBrand = useBusinessStore((s) => s.activeBrand);

  const [sessions, setSessions] = useState<CMChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<CMChatSession | null>(null);
  const [messages, setMessages] = useState<CMChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sessionIdRef = useRef<string | null>(null);
  const brandId = activeBrand?.id;

  // ── Load sessions ──
  const loadSessions = useCallback(async () => {
    if (!brandId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await ilyasApi.listSessions(brandId);
      setSessions(res.data.sessions ?? []);
    } catch (err: any) {
      setError(err.message || "Erreur chargement sessions");
    } finally {
      setIsLoading(false);
    }
  }, [brandId]);

  // ── Select session & load messages ──
  const selectSession = useCallback(
    async (sessionId: string) => {
      if (!brandId) return;
      setIsLoading(true);
      setError(null);
      try {
        const res = await ilyasApi.getMessages(brandId, sessionId);
        const msgs: CMChatMessage[] = res.data.messages ?? [];
        setMessages(msgs);
        const found = sessions.find((s) => s.id === sessionId) ?? null;
        setActiveSession(found);
        sessionIdRef.current = sessionId;
      } catch (err: any) {
        setError(err.message || "Erreur chargement messages");
      } finally {
        setIsLoading(false);
      }
    },
    [brandId, sessions]
  );

  // ── Send message (with optional image) ──
  const sendMessage = useCallback(
    async (text: string, imageUrl?: string) => {
      if (!brandId || !text.trim()) return;
      setIsSending(true);
      setError(null);

      const optimisticMsg: CMChatMessage = {
        id: `tmp-${Date.now()}`,
        session_id: sessionIdRef.current ?? "",
        role: "user",
        content: text,
        tokens_used: 0,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimisticMsg]);

      try {
        const res = await ilyasApi.chat(
          brandId,
          text,
          sessionIdRef.current ?? undefined,
          imageUrl
        );
        const { session, message: assistantMsg } = res.data;

        sessionIdRef.current = session.id;
        setActiveSession(session);

        setMessages((prev) => {
          const withoutOptimistic = prev.filter((m) => m.id !== optimisticMsg.id);
          return [...withoutOptimistic, optimisticMsg, assistantMsg];
        });

        setSessions((prev) => {
          const exists = prev.find((s) => s.id === session.id);
          if (exists) {
            return prev.map((s) => (s.id === session.id ? session : s));
          }
          return [session, ...prev];
        });
      } catch (err: any) {
        setError(err.message || "Erreur envoi message");
        setMessages((prev) => prev.filter((m) => m.id !== optimisticMsg.id));
      } finally {
        setIsSending(false);
      }
    },
    [brandId]
  );

  // ── New session ──
  const newSession = useCallback(() => {
    sessionIdRef.current = null;
    setActiveSession(null);
    setMessages([]);
    setError(null);
  }, []);

  // ── Delete session ──
  const deleteSession = useCallback(
    async (sessionId: string) => {
      if (!brandId) return;
      try {
        await ilyasApi.deleteSession(brandId, sessionId);
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
        if (activeSession?.id === sessionId) {
          newSession();
        }
      } catch (err: any) {
        setError(err.message || "Erreur suppression session");
      }
    },
    [brandId, activeSession, newSession]
  );

  return {
    sessions,
    activeSession,
    messages,
    isLoading,
    isSending,
    error,
    loadSessions,
    selectSession,
    sendMessage,
    newSession,
    deleteSession,
  };
}
