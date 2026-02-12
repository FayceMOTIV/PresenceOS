"use client";

import { useState, useCallback, useRef } from "react";
import { chatApi } from "@/lib/api";

export type AIMessage = {
  id: string;
  type: "text" | "buttons" | "media" | "caption_preview" | "success" | "error" | "reaction";
  sender: "user" | "ai";
  content: string;
  buttons?: { id: string; title: string }[];
  header?: string;
  media_url?: string;
  media_type?: string;
  emoji?: string;
  timestamp: Date;
};

export type ContentStep = "upload" | "enriching" | "preview" | "publishing" | "published";

export function useContentCreator() {
  const [step, setStep] = useState<ContentStep>("upload");
  const [photos, setPhotos] = useState<File[]>([]);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [caption, setCaption] = useState("");
  const [platforms, setPlatforms] = useState<string[]>(["instagram"]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const msgCounter = useRef(0);

  const addMessage = useCallback((msg: Omit<AIMessage, "id" | "timestamp" | "sender"> & { sender?: "user" | "ai" }) => {
    msgCounter.current += 1;
    setMessages((prev) => [
      ...prev,
      { ...msg, sender: msg.sender || "ai", id: `msg-${msgCounter.current}`, timestamp: new Date() },
    ]);
  }, []);

  const processResponses = useCallback(
    (responses: any[], newSessionId: string) => {
      setSessionId(newSessionId);

      for (const r of responses) {
        // Detect caption preview from content
        const isPreview =
          r.type === "buttons" &&
          r.content &&
          (r.content.includes("publication") || r.content.includes("Voici"));

        if (isPreview) {
          // Extract caption from content between quotes
          const match = r.content.match(/"([^"]+)"/);
          if (match) {
            setCaption(match[1]);
          }
          setStep("preview");
        }

        if (r.type === "buttons") {
          // Check if these are enriching or confirming buttons
          const hasPublish = r.buttons?.some(
            (b: any) => b.id === "enrich_publish" || b.id === "confirm_publish"
          );
          if (
            r.buttons?.some((b: any) => b.id === "enrich_publish") &&
            step !== "preview"
          ) {
            setStep("enriching");
          }

          addMessage({
            type: "buttons",
            content: r.content || "",
            header: r.header,
            buttons: r.buttons,
          });
        } else if (r.type === "text") {
          // Check for success (publication confirmed)
          const isSuccess =
            r.content.includes("Publie") || r.content.includes("✅");
          if (isSuccess) {
            addMessage({ type: "success", content: r.content });
            setStep("published");
          } else {
            addMessage({ type: "text", content: r.content });
          }
        } else if (r.type === "media") {
          addMessage({
            type: "media",
            content: r.content || "",
            media_url: r.media_url,
            media_type: r.media_type,
          });
        } else if (r.type === "reaction") {
          addMessage({ type: "reaction", content: "", emoji: r.emoji });
        }
      }
    },
    [addMessage, step]
  );

  const uploadPhoto = useCallback(
    async (file: File) => {
      setIsLoading(true);
      try {
        // Show local preview immediately
        const localUrl = URL.createObjectURL(file);
        setPhotos((prev) => [...prev, file]);
        setPhotoUrls((prev) => [...prev, localUrl]);

        // Upload to server
        const uploadRes = await chatApi.uploadMedia(file);
        const { media_id } = uploadRes.data;

        // Send to conversation engine
        const msgRes = await chatApi.sendMessage({
          msg_type: "image",
          media_id,
          session_id: sessionId || undefined,
        });

        processResponses(msgRes.data.messages, msgRes.data.session_id);
      } catch (error: any) {
        addMessage({
          type: "error",
          content: "Erreur lors de l'upload. Reessaie !",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, processResponses, addMessage]
  );

  const sendText = useCallback(
    async (text: string) => {
      setIsLoading(true);
      addMessage({ type: "text", content: text, sender: "user" });
      try {
        const res = await chatApi.sendMessage({
          msg_type: "text",
          text,
          session_id: sessionId || undefined,
        });
        processResponses(res.data.messages, res.data.session_id);
      } catch {
        addMessage({
          type: "error",
          content: "Erreur de connexion. Reessaie !",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, processResponses, addMessage]
  );

  const clickButton = useCallback(
    async (buttonId: string, buttonTitle: string) => {
      setIsLoading(true);
      addMessage({ type: "text", content: buttonTitle, sender: "user" });

      if (buttonId === "confirm_publish") {
        setStep("publishing");
      }

      try {
        const res = await chatApi.sendMessage({
          msg_type: "interactive",
          button_id: buttonId,
          session_id: sessionId || undefined,
        });
        processResponses(res.data.messages, res.data.session_id);
      } catch {
        addMessage({
          type: "error",
          content: "Erreur de connexion. Reessaie !",
        });
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, processResponses, addMessage]
  );

  const reset = useCallback(() => {
    setStep("upload");
    setPhotos([]);
    setPhotoUrls([]);
    setMessages([]);
    setCaption("");
    setPlatforms(["instagram"]);
    setIsLoading(false);
    setSessionId(null);
  }, []);

  return {
    step,
    photos,
    photoUrls,
    messages,
    caption,
    platforms,
    setPlatforms,
    isLoading,
    sessionId,
    uploadPhoto,
    sendText,
    clickButton,
    reset,
  };
}
