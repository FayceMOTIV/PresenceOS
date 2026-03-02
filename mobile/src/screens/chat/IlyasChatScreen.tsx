// PresenceOS Mobile — Ilyas Chat Screen (iMessage-style)

import React, { useState, useEffect, useRef, useCallback, useContext } from "react";
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
  Image,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as ImagePicker from "expo-image-picker";
import { Audio } from "expo-av";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { useIlyasChat } from "@/hooks/useIlyasChat";
import { voiceApi } from "@/lib/api";
import { BrandContext } from "@/contexts/BrandContext";
import type { CMChatMessage, CMChatSession } from "@/types";

// ── Session Drawer ──
function SessionDrawer({
  sessions, activeId, onSelect, onNew, onDelete, onClose,
}: {
  sessions: CMChatSession[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}) {
  return (
    <View style={drawerStyles.overlay}>
      <TouchableOpacity style={drawerStyles.backdrop} onPress={onClose} activeOpacity={1} />
      <View style={drawerStyles.panel}>
        <View style={drawerStyles.header}>
          <Text style={drawerStyles.title}>Conversations</Text>
          <TouchableOpacity onPress={onClose}><Ionicons name="close" size={22} color={Colors.text.secondary} /></TouchableOpacity>
        </View>
        <TouchableOpacity style={drawerStyles.newBtn} onPress={() => { onNew(); onClose(); }}>
          <Ionicons name="add-circle" size={20} color="#FFF" />
          <Text style={drawerStyles.newBtnText}>Nouvelle conversation</Text>
        </TouchableOpacity>
        <FlatList
          data={sessions}
          keyExtractor={(s) => s.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[drawerStyles.sessionItem, item.id === activeId && drawerStyles.sessionActive]}
              onPress={() => { onSelect(item.id); onClose(); }}
              onLongPress={() => Alert.alert(FR.confirm_delete, FR.confirm_delete_body, [
                { text: FR.no_cancel, style: "cancel" },
                { text: FR.yes_delete, style: "destructive", onPress: () => onDelete(item.id) },
              ])}
            >
              <Ionicons name="chatbubble-outline" size={16} color={item.id === activeId ? Colors.brand.primary : Colors.text.muted} />
              <View style={drawerStyles.sessionInfo}>
                <Text style={[drawerStyles.sessionTitle, item.id === activeId && { color: Colors.brand.primary, fontWeight: "600" }]} numberOfLines={1}>{item.title || "Sans titre"}</Text>
                <Text style={drawerStyles.sessionMeta}>{item.message_count} msg</Text>
              </View>
            </TouchableOpacity>
          )}
          ListEmptyComponent={<Text style={drawerStyles.emptyText}>Aucune conversation</Text>}
        />
      </View>
    </View>
  );
}

// ── Proposal Bubble ──
function ProposalBubble({ proposal }: { proposal: Record<string, any> }) {
  return (
    <View style={proposalStyles.card}>
      <View style={proposalStyles.badge}>
        <Ionicons name="sparkles" size={12} color="#FFF" />
        <Text style={proposalStyles.badgeText}>Proposition IA</Text>
      </View>
      {proposal.caption && <Text style={proposalStyles.caption} numberOfLines={4}>{proposal.caption}</Text>}
      {proposal.hashtags && Array.isArray(proposal.hashtags) && <Text style={proposalStyles.hashtags}>{proposal.hashtags.join(" ")}</Text>}
      {proposal.platform && <Text style={proposalStyles.platform}>{proposal.platform}</Text>}
    </View>
  );
}

// ── Message Bubble ──
function MessageBubble({ message }: { message: CMChatMessage }) {
  const isUser = message.role === "user";
  return (
    <View style={[bubbleStyles.row, isUser ? bubbleStyles.rowUser : bubbleStyles.rowAssistant]}>
      {!isUser && (
        <View style={bubbleStyles.avatar}><Text style={{ fontSize: 14 }}>{"👨‍🍳"}</Text></View>
      )}
      <View style={{ maxWidth: "78%", gap: 6 }}>
        <View style={[bubbleStyles.bubble, isUser ? bubbleStyles.bubbleUser : bubbleStyles.bubbleAssistant]}>
          <Text style={[bubbleStyles.text, isUser ? bubbleStyles.textUser : bubbleStyles.textAssistant]}>{message.content}</Text>
        </View>
        {message.proposals && message.proposals.length > 0 && (
          <View style={{ gap: 6 }}>{message.proposals.map((p, i) => <ProposalBubble key={`prop-${i}`} proposal={p} />)}</View>
        )}
        <Text style={[bubbleStyles.time, isUser && { textAlign: "right" }]}>{formatTime(message.created_at)}</Text>
      </View>
    </View>
  );
}

function formatTime(iso: string): string {
  try { return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" }); } catch { return ""; }
}

// ── Main Screen ──
export default function IlyasChatScreen() {
  const {
    sessions, activeSession, messages, isLoading, isSending, error,
    loadSessions, selectSession, sendMessage, newSession, deleteSession,
  } = useIlyasChat();

  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [text, setText] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const flatListRef = useRef<FlatList>(null);

  // Voice recording (Sprint 7)
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  useEffect(() => {
    if (messages.length > 0) setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
  }, [messages.length]);

  const handlePickImage = useCallback(async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.8,
    });
    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0].uri);
    }
  }, []);

  const handleSend = useCallback(() => {
    if (!text.trim() || isSending) return;
    const msg = text.trim();
    const img = selectedImage;
    setText("");
    setSelectedImage(null);
    Keyboard.dismiss();
    sendMessage(msg, img ?? undefined);
  }, [text, isSending, sendMessage, selectedImage]);

  // ── Voice recording handlers (Sprint 7) ──
  const startRecording = useCallback(async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });
      const { recording: rec } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY,
      );
      setRecording(rec);
      setIsRecording(true);
    } catch (err) {
      Alert.alert("Erreur", "Impossible de demarrer l'enregistrement");
    }
  }, []);

  const stopAndTranscribe = useCallback(async () => {
    if (!recording || !brandId) return;
    setIsRecording(false);
    setTranscribing(true);

    try {
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setRecording(null);

      if (!uri) return;

      const formData = new FormData();
      formData.append("audio", {
        uri,
        name: "audio.m4a",
        type: "audio/m4a",
      } as unknown as Blob);
      formData.append("language", "fr");

      const response = await voiceApi.transcribe(brandId, formData);
      if (response.data.success && response.data.text) {
        setText(response.data.text);
      }
    } catch {
      Alert.alert("Erreur", "La transcription a echoue");
    } finally {
      setTranscribing(false);
    }
  }, [recording, brandId]);

  const quickPrompts = [
    "Reel pour ce weekend",
    "Post plat du jour",
    "Story promo",
    "Strategie du mois",
  ];

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerBtn} onPress={() => setDrawerOpen(true)}>
          <Ionicons name="menu" size={22} color={Colors.text.primary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>{activeSession ? activeSession.title : "Ilyas"}</Text>
          {activeSession && <Text style={styles.headerSubtitle}>{activeSession.message_count} messages</Text>}
        </View>
        <TouchableOpacity style={styles.headerBtn} onPress={newSession}>
          <Ionicons name="create-outline" size={22} color={Colors.brand.primary} />
        </TouchableOpacity>
      </View>

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={loadSessions}><Text style={styles.errorRetry}>{FR.retry}</Text></TouchableOpacity>
        </View>
      )}

      <KeyboardAvoidingView style={styles.chatArea} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        {isLoading ? (
          <View style={styles.center}><ActivityIndicator size="large" color={Colors.brand.primary} /></View>
        ) : messages.length === 0 ? (
          <View style={styles.emptyContainer}>
            <View style={styles.emptyIcon}><Text style={{ fontSize: 48 }}>{"👨‍🍳"}</Text></View>
            <Text style={styles.emptyTitle}>{FR.ilyas_title}</Text>
            <Text style={styles.emptyBody}>{FR.ilyas_subtitle}</Text>
            <View style={styles.quickPrompts}>
              {quickPrompts.map((prompt) => (
                <TouchableOpacity key={prompt} style={styles.quickChip} onPress={() => setText(prompt)}>
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
            renderItem={({ item }) => <MessageBubble message={item} />}
            contentContainerStyle={styles.messageList}
            keyboardDismissMode="interactive"
            showsVerticalScrollIndicator={false}
          />
        )}

        {isSending && (
          <View style={styles.typingRow}>
            <View style={bubbleStyles.avatar}><Text style={{ fontSize: 14 }}>{"👨‍🍳"}</Text></View>
            <View style={styles.typingBubble}>
              <ActivityIndicator size="small" color={Colors.brand.primary} />
              <Text style={styles.typingText}>{FR.ilyas_thinking}</Text>
            </View>
          </View>
        )}

        {/* Image preview */}
        {selectedImage && (
          <View style={styles.imagePreview}>
            <Image source={{ uri: selectedImage }} style={styles.previewThumb} />
            <TouchableOpacity onPress={() => setSelectedImage(null)}>
              <Ionicons name="close-circle" size={24} color={Colors.status.danger} />
            </TouchableOpacity>
          </View>
        )}

        {/* Input bar */}
        <View style={styles.inputBar}>
          <TouchableOpacity onPress={handlePickImage} style={styles.cameraBtn}>
            <Ionicons name="camera" size={22} color={Colors.brand.primary} />
          </TouchableOpacity>
          {isRecording ? (
            <TouchableOpacity onPress={stopAndTranscribe} style={styles.micBtnRecording}>
              <Ionicons name="stop" size={20} color={Colors.status.danger} />
            </TouchableOpacity>
          ) : transcribing ? (
            <View style={styles.micBtn}>
              <ActivityIndicator size="small" color={Colors.brand.amber} />
            </View>
          ) : (
            <TouchableOpacity onPress={startRecording} style={styles.micBtn}>
              <Ionicons name="mic" size={22} color={Colors.brand.amber} />
            </TouchableOpacity>
          )}
          <TextInput
            style={styles.input}
            placeholder={FR.ilyas_placeholder}
            placeholderTextColor={Colors.text.muted}
            value={text}
            onChangeText={setText}
            multiline
            maxLength={4000}
          />
          <TouchableOpacity
            style={[styles.sendBtn, (!text.trim() || isSending) && styles.sendBtnDisabled]}
            onPress={handleSend}
            disabled={!text.trim() || isSending}
          >
            <LinearGradient colors={[...Colors.gradient.hero]} style={styles.sendGradient} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}>
              <Ionicons name="send" size={18} color="#FFF" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>

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

// Styles
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: { flexDirection: "row", alignItems: "center", paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: Colors.border.default, backgroundColor: Colors.bg.secondary },
  headerBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.bg.elevated, justifyContent: "center", alignItems: "center" },
  headerCenter: { flex: 1, alignItems: "center" },
  headerTitle: { fontSize: 16, fontWeight: "700", color: Colors.text.primary },
  headerSubtitle: { fontSize: 11, color: Colors.text.muted, marginTop: 1 },
  errorBanner: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", backgroundColor: Colors.status.dangerLight, paddingHorizontal: 16, paddingVertical: 10 },
  errorText: { fontSize: 13, color: Colors.status.danger, flex: 1 },
  errorRetry: { fontSize: 13, fontWeight: "600", color: Colors.brand.primary, marginLeft: 12 },
  chatArea: { flex: 1 },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyContainer: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  emptyIcon: { width: 96, height: 96, borderRadius: 48, backgroundColor: Colors.brand.glow, justifyContent: "center", alignItems: "center", marginBottom: 24 },
  emptyTitle: { fontSize: 20, fontWeight: "700", color: Colors.text.primary, textAlign: "center", marginBottom: 8 },
  emptyBody: { fontSize: 14, color: Colors.text.secondary, textAlign: "center", lineHeight: 20, marginBottom: 24, maxWidth: 300 },
  quickPrompts: { flexDirection: "row", flexWrap: "wrap", gap: 8, justifyContent: "center" },
  quickChip: { backgroundColor: Colors.bg.secondary, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 20, borderWidth: 1, borderColor: Colors.border.default },
  quickChipText: { fontSize: 13, color: Colors.brand.primary, fontWeight: "500" },
  messageList: { paddingHorizontal: 12, paddingTop: 12, paddingBottom: 8 },
  typingRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 12, paddingBottom: 8 },
  typingBubble: { flexDirection: "row", alignItems: "center", gap: 8, backgroundColor: Colors.bg.secondary, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 18, borderWidth: 1, borderColor: Colors.border.default },
  typingText: { fontSize: 13, color: Colors.text.muted, fontStyle: "italic" },
  imagePreview: { flexDirection: "row", alignItems: "center", gap: 8, paddingHorizontal: 16, paddingVertical: 8 },
  previewThumb: { width: 60, height: 60, borderRadius: 10 },
  inputBar: { flexDirection: "row", alignItems: "flex-end", paddingHorizontal: 12, paddingVertical: 10, borderTopWidth: 1, borderTopColor: Colors.border.default, backgroundColor: Colors.bg.secondary, gap: 8 },
  cameraBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.bg.elevated, justifyContent: "center", alignItems: "center" },
  micBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.bg.elevated, justifyContent: "center", alignItems: "center" },
  micBtnRecording: { width: 36, height: 36, borderRadius: 18, backgroundColor: Colors.status.danger + "20", justifyContent: "center", alignItems: "center" },
  input: { flex: 1, backgroundColor: Colors.bg.elevated, borderRadius: 20, paddingHorizontal: 16, paddingTop: 10, paddingBottom: 10, fontSize: 15, color: Colors.text.primary, maxHeight: 100, borderWidth: 1, borderColor: Colors.border.default },
  sendBtn: { borderRadius: 20, overflow: "hidden" },
  sendBtnDisabled: { opacity: 0.4 },
  sendGradient: { width: 40, height: 40, borderRadius: 20, justifyContent: "center", alignItems: "center" },
});

const bubbleStyles = StyleSheet.create({
  row: { flexDirection: "row", marginBottom: 12, alignItems: "flex-end", gap: 8 },
  rowUser: { justifyContent: "flex-end" },
  rowAssistant: { justifyContent: "flex-start" },
  avatar: { width: 28, height: 28, borderRadius: 14, backgroundColor: Colors.brand.glow, justifyContent: "center", alignItems: "center" },
  bubble: { borderRadius: 18, paddingHorizontal: 14, paddingVertical: 10, maxWidth: "100%" },
  bubbleUser: { backgroundColor: Colors.brand.primary, borderBottomRightRadius: 4 },
  bubbleAssistant: { backgroundColor: Colors.bg.secondary, borderBottomLeftRadius: 4, borderWidth: 1, borderColor: Colors.border.default },
  text: { fontSize: 15, lineHeight: 21 },
  textUser: { color: Colors.text.inverted },
  textAssistant: { color: Colors.text.primary },
  time: { fontSize: 10, color: Colors.text.muted, marginTop: 2, paddingHorizontal: 4 },
});

const drawerStyles = StyleSheet.create({
  overlay: { ...StyleSheet.absoluteFillObject, flexDirection: "row", zIndex: 100 },
  backdrop: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.35)" },
  panel: { width: 280, backgroundColor: Colors.bg.secondary, borderRightWidth: 1, borderRightColor: Colors.border.default, paddingTop: 60, paddingHorizontal: 16, shadowColor: "#000", shadowOpacity: 0.1, shadowRadius: 10, elevation: 5 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 20 },
  title: { fontSize: 18, fontWeight: "700", color: Colors.text.primary },
  newBtn: { flexDirection: "row", alignItems: "center", gap: 8, backgroundColor: Colors.brand.primary, borderRadius: 12, paddingVertical: 12, paddingHorizontal: 16, marginBottom: 16 },
  newBtnText: { color: "#FFF", fontWeight: "600", fontSize: 14 },
  sessionItem: { flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 12, paddingHorizontal: 12, borderRadius: 10, marginBottom: 4 },
  sessionActive: { backgroundColor: Colors.brand.glow },
  sessionInfo: { flex: 1 },
  sessionTitle: { fontSize: 14, fontWeight: "500", color: Colors.text.primary },
  sessionMeta: { fontSize: 11, color: Colors.text.muted, marginTop: 2 },
  emptyText: { fontSize: 13, color: Colors.text.muted, textAlign: "center", marginTop: 20 },
});

const proposalStyles = StyleSheet.create({
  card: { backgroundColor: Colors.bg.elevated, borderRadius: 14, padding: 12, borderWidth: 1, borderColor: Colors.brand.amber + "40" },
  badge: { flexDirection: "row", alignItems: "center", gap: 4, backgroundColor: Colors.brand.amber, alignSelf: "flex-start", paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8, marginBottom: 8 },
  badgeText: { fontSize: 11, fontWeight: "600", color: "#FFF" },
  caption: { fontSize: 13, color: Colors.text.primary, lineHeight: 19, marginBottom: 6 },
  hashtags: { fontSize: 12, color: Colors.brand.primary, marginBottom: 4 },
  platform: { fontSize: 11, color: Colors.text.muted, fontWeight: "500" },
});
