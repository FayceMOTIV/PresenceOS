// PresenceOS Mobile — Onboarding Chat Screen (Sprint 4 + Sprint 6: URL Scrape)
// iMessage-style conversational onboarding with Ilyas
// URL step → Firecrawl pre-fills DNA → Ilyas only asks missing questions

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { onboardingApi } from "@/lib/api";
import { useOnboardingStore } from "@/stores/onboardingStore";

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: number;
}

interface Props {
  brandId: string;
  onComplete: () => void;
}

const TOTAL_STEPS = 8;

export default function OnboardingChatScreen({ brandId, onComplete }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isStarting, setIsStarting] = useState(true);
  const flatListRef = useRef<FlatList>(null);
  const onboardingStore = useOnboardingStore();

  // ── Sprint 6: URL scrape step ──
  const [urlStep, setUrlStep] = useState(true);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [scraping, setScraping] = useState(false);
  const [scrapeMessage, setScrapeMessage] = useState<string | null>(null);

  const handleScrape = useCallback(async () => {
    if (!websiteUrl.trim() || !brandId || scraping) return;
    setScraping(true);
    try {
      const res = await onboardingApi.scrape(brandId, websiteUrl.trim());
      setScrapeMessage(res.data.message || "Analyse terminee !");
      setTimeout(() => {
        setUrlStep(false);
      }, 1500);
    } catch {
      setScrapeMessage("L'analyse du site a échoué. On continue sans.");
      setTimeout(() => setUrlStep(false), 2000);
    } finally {
      setScraping(false);
    }
  }, [websiteUrl, brandId, scraping]);

  // Start onboarding when URL step is done
  useEffect(() => {
    if (!urlStep) {
      startOnboarding();
    }
  }, [urlStep]);

  const startOnboarding = useCallback(async () => {
    try {
      setIsStarting(true);
      const res = await onboardingApi.start(brandId);
      const data = res.data;

      if (data.complete) {
        await onboardingStore.markCompleted();
        onComplete();
        return;
      }

      setCurrentStep(data.step);
      if (data.question) {
        addAssistantMessage(data.question);
      }
    } catch (err) {
      if (__DEV__) console.warn("Onboarding start failed:", err);
      addAssistantMessage(
        "Salut ! Je suis Ilyas, ton CM IA. Comment s'appelle ton commerce ?"
      );
    } finally {
      setIsStarting(false);
    }
  }, [brandId]);

  const addAssistantMessage = useCallback((content: string) => {
    const msg: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: "assistant",
      content,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, msg]);
  }, []);

  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    // Add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await onboardingApi.answer(brandId, currentStep, text);
      const data = res.data;

      if (data.complete) {
        addAssistantMessage(
          "Parfait ! J'ai tout ce qu'il me faut pour devenir ton CM. " +
            "On va faire de grandes choses ensemble ! 🚀"
        );
        setTimeout(async () => {
          await onboardingStore.markCompleted();
          onComplete();
        }, 2000);
        return;
      }

      if (data.next_question) {
        // Small delay for natural feel
        setTimeout(() => {
          setCurrentStep(data.next_step);
          addAssistantMessage(data.next_question);
        }, 500);
      }
    } catch (err) {
      addAssistantMessage(
        "Oups, petit souci technique. Peux-tu reformuler ?"
      );
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, currentStep, brandId]);

  const renderMessage = useCallback(
    ({ item }: { item: ChatMessage }) => {
      const isUser = item.role === "user";
      return (
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.userBubble : styles.assistantBubble,
          ]}
        >
          {!isUser && (
            <View style={styles.avatarSmall}>
              <Text style={styles.avatarText}>{"🤖"}</Text>
            </View>
          )}
          <View
            style={[
              styles.bubbleContent,
              isUser ? styles.userContent : styles.assistantContent,
            ]}
          >
            <Text
              style={[
                styles.messageText,
                isUser ? styles.userText : styles.assistantText,
              ]}
            >
              {item.content}
            </Text>
          </View>
        </View>
      );
    },
    []
  );

  // Auto-scroll on new messages
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length]);

  // ── URL Scrape screen (before chat) ──
  if (urlStep) {
    return (
      <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : "height"}
        >
          <ScrollView
            contentContainerStyle={styles.urlScreen}
            keyboardShouldPersistTaps="handled"
            bounces={false}
          >
            <Text style={styles.urlEmoji}>{"🌐"}</Text>
            <Text style={styles.urlTitle}>Votre site web</Text>
            <Text style={styles.urlSubtitle}>
              Collez votre URL et je recupere automatiquement les infos de votre
              commerce en 30 secondes.
            </Text>
            <TextInput
              style={styles.urlInput}
              value={websiteUrl}
              onChangeText={setWebsiteUrl}
              placeholder="https://votre-restaurant.fr"
              placeholderTextColor={Colors.text.muted}
              autoCapitalize="none"
              keyboardType="url"
              autoCorrect={false}
            />
            <TouchableOpacity
              style={[styles.urlBtn, (scraping || !websiteUrl.trim()) && styles.urlBtnDisabled]}
              onPress={handleScrape}
              disabled={scraping || !websiteUrl.trim()}
            >
              {scraping ? (
                <ActivityIndicator color="#FFF" />
              ) : (
                <Text style={styles.urlBtnText}>Analyser mon site</Text>
              )}
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.urlSkip}
              onPress={() => setUrlStep(false)}
            >
              <Text style={styles.urlSkipText}>
                {"Je n'ai pas de site web →"}
              </Text>
            </TouchableOpacity>
            {scrapeMessage && (
              <View style={[styles.scrapeResultBox, scrapeMessage.includes("échoué") && { backgroundColor: Colors.status.warning + "15" }]}>
                <Ionicons
                  name={scrapeMessage.includes("échoué") ? "warning" : "checkmark-circle"}
                  size={20}
                  color={scrapeMessage.includes("échoué") ? Colors.status.warning : Colors.status.success}
                />
                <Text style={[styles.scrapeResultText, scrapeMessage.includes("échoué") && { color: Colors.status.warning }]}>
                  {scrapeMessage}
                </Text>
              </View>
            )}
          </ScrollView>
        </KeyboardAvoidingView>
      </SafeAreaView>
    );
  }

  if (isStarting) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={Colors.brand.primary} />
        <Text style={styles.loadingText}>Ilyas se prepare...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerAvatar}>
          <Text style={styles.headerAvatarText}>{"🤖"}</Text>
        </View>
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>Ilyas</Text>
          <Text style={styles.headerSubtitle}>
            Étape {Math.min(currentStep + 1, TOTAL_STEPS)}/{TOTAL_STEPS}
          </Text>
        </View>
      </View>

      {/* Progress bar */}
      <View style={styles.progressContainer}>
        <View
          style={[
            styles.progressBar,
            { width: `${((currentStep + 1) / TOTAL_STEPS) * 100}%` },
          ]}
        />
      </View>

      {/* Messages */}
      <KeyboardAvoidingView
        style={styles.chatArea}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderMessage}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messagesList}
          showsVerticalScrollIndicator={false}
        />

        {/* Typing indicator */}
        {isLoading && (
          <View style={[styles.messageBubble, styles.assistantBubble]}>
            <View style={styles.avatarSmall}>
              <Text style={styles.avatarText}>{"🤖"}</Text>
            </View>
            <View style={[styles.bubbleContent, styles.assistantContent]}>
              <ActivityIndicator size="small" color={Colors.brand.primary} />
            </View>
          </View>
        )}

        {/* Input */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Tape ta réponse..."
            placeholderTextColor={Colors.text.muted}
            multiline
            maxLength={2000}
            editable={!isLoading}
            onSubmitEditing={handleSend}
            returnKeyType="send"
          />
          <TouchableOpacity
            onPress={handleSend}
            disabled={!input.trim() || isLoading}
            style={[
              styles.sendBtn,
              (!input.trim() || isLoading) && styles.sendBtnDisabled,
            ]}
          >
            <Ionicons
              name="send"
              size={20}
              color={input.trim() && !isLoading ? "#FFF" : Colors.text.muted}
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: Colors.bg.primary,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.text.secondary,
  },

  // Header
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: Colors.bg.secondary,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  headerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.brand.glow,
    justifyContent: "center",
    alignItems: "center",
  },
  headerAvatarText: { fontSize: 20 },
  headerInfo: { marginLeft: 12 },
  headerTitle: {
    fontSize: 17,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  headerSubtitle: {
    fontSize: 13,
    color: Colors.text.muted,
    marginTop: 1,
  },

  // Progress
  progressContainer: {
    height: 3,
    backgroundColor: Colors.border.default,
  },
  progressBar: {
    height: 3,
    backgroundColor: Colors.brand.primary,
    borderRadius: 2,
  },

  // Chat
  chatArea: { flex: 1 },
  messagesList: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },

  // Messages
  messageBubble: {
    flexDirection: "row",
    alignItems: "flex-end",
    marginBottom: 4,
  },
  userBubble: {
    justifyContent: "flex-end",
  },
  assistantBubble: {
    justifyContent: "flex-start",
  },
  avatarSmall: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.brand.glow,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 8,
  },
  avatarText: { fontSize: 14 },
  bubbleContent: {
    maxWidth: "75%",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
  },
  userContent: {
    backgroundColor: Colors.brand.primary,
    borderBottomRightRadius: 4,
    marginLeft: "auto",
  },
  assistantContent: {
    backgroundColor: Colors.bg.secondary,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: "#FFF",
  },
  assistantText: {
    color: Colors.text.primary,
  },

  // Input
  inputContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: Colors.bg.secondary,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
    gap: 10,
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    backgroundColor: Colors.bg.primary,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: Colors.text.primary,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  sendBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.brand.primary,
    justifyContent: "center",
    alignItems: "center",
  },
  sendBtnDisabled: {
    backgroundColor: Colors.bg.elevated,
  },

  // URL Scrape step (Sprint 6)
  urlScreen: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 32,
    paddingVertical: 40,
  },
  urlEmoji: { fontSize: 48, marginBottom: 20 },
  urlTitle: {
    fontSize: 22,
    fontWeight: "700",
    color: Colors.text.primary,
    marginBottom: 8,
  },
  urlSubtitle: {
    fontSize: 15,
    color: Colors.text.secondary,
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 24,
    maxWidth: 300,
  },
  urlInput: {
    width: "100%",
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
    color: Colors.text.primary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    marginBottom: 16,
  },
  urlBtn: {
    width: "100%",
    backgroundColor: Colors.brand.primary,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
  },
  urlBtnDisabled: { opacity: 0.5 },
  urlBtnText: { color: "#FFF", fontWeight: "700", fontSize: 16 },
  urlSkip: { marginTop: 16 },
  urlSkipText: { color: Colors.text.muted, fontSize: 14 },
  scrapeResultBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 20,
    backgroundColor: Colors.status.success + "15",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
  },
  scrapeResultText: {
    fontSize: 14,
    color: Colors.status.success,
    fontWeight: "500",
    flex: 1,
  },
});
