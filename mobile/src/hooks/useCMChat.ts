// PresenceOS Mobile — CM Chat Hook
// Manages chat sessions, messages, and AI interactions

import { useState, useCallback, useRef } from "react";
import { cmChatApi } from "@/lib/api";
import { useBusinessStore } from "@/stores/businessStore";
import type { CMChatSession, CMChatMessage } from "@/types";

interface UseCMChatReturn {
  sessions: CMChatSession[];
  activeSession: CMChatSession | null;
  messages: CMChatMessage[];
  isLoading: boolean;
  isSending: boolean;
  error: string | null;

  loadSessions: () => Promise<void>;
  selectSession: (sessionId: string) => Promise<void>;
  sendMessage: (text: string) => Promise<void>;
  newSession: () => void;
  deleteSession: (sessionId: string) => Promise<void>;
}

export function useCMChat(): UseCMChatReturn {
  const activeBrand = useBusinessStore((s) => s.activeBrand);

  const [sessions, setSessions] = useState<CMChatSession[]>([]);
  const [activeSession, setActiveSession] = useState<CMChatSession | null>(
    null
  );
  const [messages, setMessages] = useState<CMChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track current session id for the send flow
  const sessionIdRef = useRef<string | null>(null);

  const brandId = activeBrand?.id;

  // ── Load sessions list ──
  const loadSessions = useCallback(async () => {
    if (!brandId) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await cmChatApi.listSessions(brandId);
      setSessions(res.data.sessions ?? []);
    } catch (err: any) {
      setError(err.message || "Erreur chargement sessions");
    } finally {
      setIsLoading(false);
    }
  }, [brandId]);

  // ── Select a session & load its messages ──
  const selectSession = useCallback(
    async (sessionId: string) => {
      if (!brandId) return;
      setIsLoading(true);
      setError(null);
      try {
        const res = await cmChatApi.getMessages(brandId, sessionId);
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

  // ── Send a message ──
  const sendMessage = useCallback(
    async (text: string) => {
      if (!brandId || !text.trim()) return;
      setIsSending(true);
      setError(null);

      // Optimistic: show user message immediately
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
        const res = await cmChatApi.send(
          brandId,
          text,
          sessionIdRef.current ?? undefined
        );
        const { session, message: assistantMsg } = res.data;

        // Update session reference
        sessionIdRef.current = session.id;
        setActiveSession(session);

        // Replace optimistic user msg with real data + add assistant msg
        setMessages((prev) => {
          const withoutOptimistic = prev.filter(
            (m) => m.id !== optimisticMsg.id
          );
          // Add user msg (from server context) by keeping existing ones
          // then add the assistant response
          return [...withoutOptimistic, optimisticMsg, assistantMsg];
        });

        // Refresh sessions list for sidebar/title updates
        setSessions((prev) => {
          const exists = prev.find((s) => s.id === session.id);
          if (exists) {
            return prev.map((s) => (s.id === session.id ? session : s));
          }
          return [session, ...prev];
        });
      } catch (err: any) {
        setError(err.message || "Erreur envoi message");
        // Remove optimistic message on error
        setMessages((prev) =>
          prev.filter((m) => m.id !== optimisticMsg.id)
        );
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
        await cmChatApi.deleteSession(brandId, sessionId);
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
