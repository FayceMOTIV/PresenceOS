// PresenceOS Mobile — CM Chat Screen (iMessage-style, French)

import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
  Keyboard,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { useCMChat } from "@/hooks/useCMChat";
import type { CMChatMessage, CMChatSession } from "@/types";

// ── Session Drawer ──
function SessionDrawer({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
  onClose,
}: {
  sessions: CMChatSession[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}) {
  const renderSessionItem = useCallback(({ item }: { item: CMChatSession }) => {
    const isActive = item.id === activeId;
    return (
      <TouchableOpacity
        style={[drawerStyles.sessionItem, isActive && drawerStyles.sessionActive]}
        onPress={() => { onSelect(item.id); onClose(); }}
        onLongPress={() => {
          Alert.alert(
            FR.confirm_delete,
            FR.confirm_delete_body,
            [
              { text: FR.no_cancel, style: "cancel" },
              { text: FR.yes_delete, style: "destructive", onPress: () => onDelete(item.id) },
            ]
          );
        }}
      >
        <Ionicons
          name="chatbubble-outline"
          size={16}
          color={isActive ? Colors.brand.primary : Colors.text.muted}
        />
        <View style={drawerStyles.sessionInfo}>
          <Text
            style={[drawerStyles.sessionTitle, isActive && drawerStyles.sessionTitleActive]}
            numberOfLines={1}
          >
            {item.title || "Sans titre"}
          </Text>
          <Text style={drawerStyles.sessionMeta}>
            {item.message_count} msg
          </Text>
        </View>
      </TouchableOpacity>
    );
  }, [activeId, onSelect, onClose, onDelete]);

  return (
    <View style={drawerStyles.overlay}>
      <TouchableOpacity style={drawerStyles.backdrop} onPress={onClose} activeOpacity={1} />
      <View style={drawerStyles.panel}>
        <View style={drawerStyles.header}>
          <Text style={drawerStyles.title}>Conversations</Text>
          <TouchableOpacity onPress={onClose} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
            <Ionicons name="close" size={22} color={Colors.text.secondary} />
          </TouchableOpacity>
        </View>

        <TouchableOpacity style={drawerStyles.newBtn} onPress={() => { onNew(); onClose(); }}>
          <Ionicons name="add-circle" size={20} color={Colors.text.inverted} />
          <Text style={drawerStyles.newBtnText}>Nouvelle conversation</Text>
        </TouchableOpacity>

        <FlatList
          data={sessions}
          keyExtractor={(s) => s.id}
          contentContainerStyle={{ paddingBottom: 40 }}
          renderItem={renderSessionItem}
          ListEmptyComponent={
            <Text style={drawerStyles.emptyText}>Aucune conversation</Text>
          }
        />
      </View>
    </View>
  );
}

// ── Proposal Card (inline) ──
function ProposalBubble({ proposal }: { proposal: Record<string, any> }) {
  return (
    <View style={proposalStyles.card}>
      <View style={proposalStyles.badge}>
        <Ionicons name="sparkles" size={12} color={Colors.text.inverted} />
        <Text style={proposalStyles.badgeText}>Proposition IA</Text>
      </View>
      {proposal.caption && (
        <Text style={proposalStyles.caption} numberOfLines={4}>
          {proposal.caption}
        </Text>
      )}
      {proposal.hashtags && Array.isArray(proposal.hashtags) && (
        <Text style={proposalStyles.hashtags}>
          {proposal.hashtags.join(" ")}
        </Text>
      )}
      {proposal.platform && (
        <Text style={proposalStyles.platform}>{proposal.platform}</Text>
      )}
    </View>
  );
}

// ── Message Bubble ──
function MessageBubble({ message }: { message: CMChatMessage }) {
  const isUser = message.role === "user";

  return (
    <View style={[bubbleStyles.row, isUser ? bubbleStyles.rowUser : bubbleStyles.rowAssistant]}>
      {!isUser && (
        <View style={bubbleStyles.avatar}>
          <Ionicons name="sparkles" size={14} color={Colors.brand.primary} />
        </View>
      )}
      <View style={{ maxWidth: "78%", gap: 6 }}>
        <View
          style={[
            bubbleStyles.bubble,
            isUser ? bubbleStyles.bubbleUser : bubbleStyles.bubbleAssistant,
          ]}
        >
          <Text
            style={[
              bubbleStyles.text,
              isUser ? bubbleStyles.textUser : bubbleStyles.textAssistant,
            ]}
          >
            {message.content}
          </Text>
        </View>

        {/* Render proposals if present */}
        {message.proposals && message.proposals.length > 0 && (
          <View style={{ gap: 6 }}>
            {message.proposals.map((p, i) => (
              <ProposalBubble key={`prop-${i}`} proposal={p} />
            ))}
          </View>
        )}

        <Text style={[bubbleStyles.time, isUser && { textAlign: "right" }]}>
          {formatTime(message.created_at)}
        </Text>
      </View>
    </View>
  );
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

// ── Main Screen ──
export default function CMChatScreen() {
  const {
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
  } = useCMChat();

  const [text, setText] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  // Load sessions on mount
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    if (messages.length > 0) {
      timer = setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [messages.length]);

  const handleSend = useCallback(() => {
    if (!text.trim() || isSending) return;
    const msg = text.trim();
    setText("");
    Keyboard.dismiss();
    sendMessage(msg);
  }, [text, isSending, sendMessage]);

  const renderMessage = useCallback(({ item }: { item: CMChatMessage }) => (
    <MessageBubble message={item} />
  ), []);

  const quickPrompts = [
    "Analyse mes performances",
    "Que poster cette semaine ?",
    "Propose un Reel avec mon menu",
    "Quels comptes connecter ?",
    "Story promo du jour",
    "Idée de vidéo",
  ];

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.headerBtn}
          onPress={() => setDrawerOpen(true)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="menu" size={22} color={Colors.text.primary} />
        </TouchableOpacity>

        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>
            {activeSession ? activeSession.title : "CM Chat IA"}
          </Text>
          {activeSession && (
            <Text style={styles.headerSubtitle}>
              {activeSession.message_count} messages
            </Text>
          )}
        </View>

        <TouchableOpacity
          style={styles.headerBtn}
          onPress={() => { newSession(); }}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <Ionicons name="create-outline" size={22} color={Colors.brand.primary} />
        </TouchableOpacity>
      </View>

      {/* Error banner */}
      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={loadSessions}>
            <Text style={styles.errorRetry}>{FR.retry}</Text>
          </TouchableOpacity>
        </View>
      )}

      <KeyboardAvoidingView
        style={styles.chatArea}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
      >
        {/* Messages list */}
        {isLoading ? (
          <View style={styles.center}>
            <ActivityIndicator size="large" color={Colors.brand.primary} />
          </View>
        ) : messages.length === 0 ? (
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIcon}>
              <Ionicons name="chatbubbles-outline" size={48} color={Colors.brand.primary} />
            </View>
            <Text style={styles.emptyTitle}>Votre Community Manager IA</Text>
            <Text style={styles.emptyBody}>
              Demandez-moi de créer des posts, des Reels, des Stories...
              Je connais votre marque et votre style.
            </Text>

            {/* Quick prompts */}
            <View style={styles.quickPrompts}>
              {quickPrompts.map((prompt) => (
                <TouchableOpacity
                  key={prompt}
                  style={styles.quickChip}
                  onPress={() => {
                    setText(prompt);
                  }}
                >
                  <Text style={styles.quickChipText}>{prompt}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ) : (
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(m) => m.id}
            renderItem={renderMessage}
            contentContainerStyle={styles.messageList}
            keyboardDismissMode="interactive"
            showsVerticalScrollIndicator={false}
          />
        )}

        {/* Typing indicator */}
        {isSending && (
          <View style={styles.typingRow}>
            <View style={bubbleStyles.avatar}>
              <Ionicons name="sparkles" size={14} color={Colors.brand.primary} />
            </View>
            <View style={styles.typingBubble}>
              <ActivityIndicator size="small" color={Colors.brand.primary} />
              <Text style={styles.typingText}>L'IA réfléchit...</Text>
            </View>
          </View>
        )}

        {/* Input bar */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            placeholder="Écrivez votre message..."
            placeholderTextColor={Colors.text.muted}
            value={text}
            onChangeText={setText}
            multiline
            maxLength={2000}
            returnKeyType="default"
          />
          <TouchableOpacity
            style={[styles.sendBtn, (!text.trim() || isSending) && styles.sendBtnDisabled]}
            onPress={handleSend}
            disabled={!text.trim() || isSending}
          >
            <LinearGradient
              colors={[...Colors.gradient.hero]}
              style={styles.sendGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Ionicons name="send" size={18} color="#FFF" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

      {/* Session drawer overlay */}
      {drawerOpen && (
        <SessionDrawer
          sessions={sessions}
          activeId={activeSession?.id ?? null}
          onSelect={selectSession}
          onNew={newSession}
          onDelete={deleteSession}
          onClose={() => setDrawerOpen(false)}
        />
      )}
    </SafeAreaView>
  );
}

// ── Styles ──
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },

  // Header
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
    backgroundColor: Colors.bg.secondary,
  },
  headerBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.bg.elevated,
    justifyContent: "center",
    alignItems: "center",
  },
  headerCenter: { flex: 1, alignItems: "center" },
  headerTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  headerSubtitle: {
    fontSize: 11,
    color: Colors.text.muted,
    marginTop: 1,
  },

  // Error
  errorBanner: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: Colors.status.dangerLight,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  errorText: { fontSize: 13, color: Colors.status.danger, flex: 1 },
  errorRetry: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.brand.primary,
    marginLeft: 12,
  },

  // Chat area
  chatArea: { flex: 1 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },

  // Empty state
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  emptyIcon: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: Colors.brand.glow,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text.primary,
    textAlign: "center",
    marginBottom: 8,
  },
  emptyBody: {
    fontSize: 14,
    color: Colors.text.secondary,
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 24,
    maxWidth: 300,
  },
  quickPrompts: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    justifyContent: "center",
  },
  quickChip: {
    backgroundColor: Colors.bg.secondary,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  quickChipText: {
    fontSize: 13,
    color: Colors.brand.primary,
    fontWeight: "500",
  },

  // Messages list
  messageList: {
    paddingHorizontal: 12,
    paddingTop: 12,
    paddingBottom: 8,
  },

  // Typing indicator
  typingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingBottom: 8,
  },
  typingBubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.bg.secondary,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  typingText: {
    fontSize: 13,
    color: Colors.text.muted,
    fontStyle: "italic",
  },

  // Input bar
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
    backgroundColor: Colors.bg.secondary,
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingTop: 10,
    paddingBottom: 10,
    fontSize: 15,
    color: Colors.text.primary,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  sendBtn: {
    borderRadius: 20,
    overflow: "hidden",
  },
  sendBtnDisabled: { opacity: 0.4 },
  sendGradient: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
  },
});

// ── Bubble styles ──
const bubbleStyles = StyleSheet.create({
  row: {
    flexDirection: "row",
    marginBottom: 12,
    alignItems: "flex-end",
    gap: 8,
  },
  rowUser: { justifyContent: "flex-end" },
  rowAssistant: { justifyContent: "flex-start" },

  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.brand.glow,
    justifyContent: "center",
    alignItems: "center",
  },

  bubble: {
    borderRadius: 18,
    paddingHorizontal: 14,
    paddingVertical: 10,
    maxWidth: "100%",
  },
  bubbleUser: {
    backgroundColor: Colors.brand.primary,
    borderBottomRightRadius: 4,
  },
  bubbleAssistant: {
    backgroundColor: Colors.bg.secondary,
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },

  text: {
    fontSize: 15,
    lineHeight: 21,
  },
  textUser: { color: Colors.text.inverted },
  textAssistant: { color: Colors.text.primary },

  time: {
    fontSize: 10,
    color: Colors.text.muted,
    marginTop: 2,
    paddingHorizontal: 4,
  },
});

// ── Drawer styles ──
const drawerStyles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    flexDirection: "row",
    zIndex: 100,
  },
  backdrop: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0,0,0,0.35)",
  },
  panel: {
    width: 280,
    backgroundColor: Colors.bg.secondary,
    borderRightWidth: 1,
    borderRightColor: Colors.border.default,
    paddingTop: 60,
    paddingHorizontal: 16,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowRadius: 10,
    elevation: 5,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  newBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.brand.primary,
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  newBtnText: {
    color: Colors.text.inverted,
    fontWeight: "600",
    fontSize: 14,
  },
  sessionItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    marginBottom: 4,
  },
  sessionActive: {
    backgroundColor: Colors.brand.glow,
  },
  sessionInfo: { flex: 1 },
  sessionTitle: {
    fontSize: 14,
    fontWeight: "500",
    color: Colors.text.primary,
  },
  sessionTitleActive: {
    color: Colors.brand.primary,
    fontWeight: "600",
  },
  sessionMeta: {
    fontSize: 11,
    color: Colors.text.muted,
    marginTop: 2,
  },
  emptyText: {
    fontSize: 13,
    color: Colors.text.muted,
    textAlign: "center",
    marginTop: 20,
  },
});

// ── Proposal card styles ──
const proposalStyles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.elevated,
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: Colors.brand.amber + "40",
  },
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.brand.amber,
    alignSelf: "flex-start",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    marginBottom: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "600",
    color: Colors.text.inverted,
  },
  caption: {
    fontSize: 13,
    color: Colors.text.primary,
    lineHeight: 19,
    marginBottom: 6,
  },
  hashtags: {
    fontSize: 12,
    color: Colors.brand.primary,
    marginBottom: 4,
  },
  platform: {
    fontSize: 11,
    color: Colors.text.muted,
    fontWeight: "500",
  },
});
