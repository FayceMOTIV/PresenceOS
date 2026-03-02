// PresenceOS Mobile — Onboarding: First Message to Ilyas

import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface Props {
  onNext: () => void;
}

const QUICK_CHIPS = [
  "Cree un post pour ce weekend",
  "Idee de Reel pour mon restaurant",
  "Aide-moi avec ma bio Instagram",
  "Quelle strategie social media ?",
];

export default function FirstMessageScreen({ onNext }: Props) {
  const [message, setMessage] = useState("");
  const [sent, setSent] = useState(false);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = useCallback(async () => {
    if (!message.trim()) return;
    setLoading(true);
    setSent(true);
    // Simulate Ilyas response (actual API will be called after onboarding)
    setTimeout(() => {
      setResponse(
        "Super ! Je suis ravi de travailler avec toi. " +
        "Des que ton onboarding sera termine, je pourrai creer " +
        "du contenu personnalise pour ton restaurant. " +
        "On va cartonner ensemble !"
      );
      setLoading(false);
    }, 1500);
  }, [message]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <View style={styles.header}>
        <Text style={styles.step}>Etape 3/4</Text>
        <Text style={styles.title}>Dites bonjour a Ilyas</Text>
        <Text style={styles.subtitle}>
          Envoyez votre premier message a votre CM IA
        </Text>
      </View>

      <View style={styles.chatArea}>
        {!sent ? (
          <View style={styles.chipsWrap}>
            {QUICK_CHIPS.map((chip) => (
              <TouchableOpacity
                key={chip}
                style={styles.chip}
                onPress={() => setMessage(chip)}
              >
                <Text style={styles.chipText}>{chip}</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : (
          <View style={styles.messages}>
            <View style={styles.userBubble}>
              <Text style={styles.userText}>{message}</Text>
            </View>
            {loading ? (
              <View style={styles.loadingRow}>
                <View style={styles.ilyasAvatar}>
                  <Text style={{ fontSize: 14 }}>{"👨‍🍳"}</Text>
                </View>
                <View style={styles.loadingBubble}>
                  <ActivityIndicator size="small" color={Colors.brand.primary} />
                  <Text style={styles.loadingText}>Ilyas reflechit...</Text>
                </View>
              </View>
            ) : response ? (
              <View style={styles.assistantRow}>
                <View style={styles.ilyasAvatar}>
                  <Text style={{ fontSize: 14 }}>{"👨‍🍳"}</Text>
                </View>
                <View style={styles.assistantBubble}>
                  <Text style={styles.assistantText}>{response}</Text>
                </View>
              </View>
            ) : null}
          </View>
        )}
      </View>

      {!sent && (
        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            placeholder="Ecrivez a Ilyas..."
            placeholderTextColor={Colors.text.muted}
            value={message}
            onChangeText={setMessage}
            multiline
          />
          <TouchableOpacity
            onPress={handleSend}
            disabled={!message.trim()}
            style={[styles.sendBtn, !message.trim() && { opacity: 0.4 }]}
          >
            <LinearGradient
              colors={[Colors.brand.primary, Colors.brand.amber]}
              style={styles.sendGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Ionicons name="send" size={18} color="#FFF" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
      )}

      {sent && !loading && (
        <View style={styles.footer}>
          <TouchableOpacity onPress={onNext} activeOpacity={0.8}>
            <LinearGradient
              colors={[Colors.brand.primary, Colors.brand.amber]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.nextBtn}
            >
              <Text style={styles.nextText}>Continuer</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: { paddingTop: 80, paddingHorizontal: 32, marginBottom: 24 },
  step: { fontSize: 13, color: Colors.brand.primary, fontWeight: "600", marginBottom: 8 },
  title: { fontSize: 26, fontWeight: "800", color: Colors.text.primary, marginBottom: 8 },
  subtitle: { fontSize: 15, color: Colors.text.secondary, lineHeight: 22 },
  chatArea: { flex: 1, paddingHorizontal: 16 },
  chipsWrap: { flexDirection: "row", flexWrap: "wrap", gap: 10, padding: 16 },
  chip: {
    backgroundColor: Colors.bg.secondary,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  chipText: { fontSize: 14, color: Colors.brand.primary, fontWeight: "500" },
  messages: { padding: 16, gap: 16 },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: Colors.brand.primary,
    borderRadius: 18,
    borderBottomRightRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 12,
    maxWidth: "80%",
  },
  userText: { color: "#FFF", fontSize: 15, lineHeight: 21 },
  loadingRow: { flexDirection: "row", alignItems: "flex-end", gap: 8 },
  ilyasAvatar: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.brand.glow,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingBubble: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  loadingText: { fontSize: 13, color: Colors.text.muted, fontStyle: "italic" },
  assistantRow: { flexDirection: "row", alignItems: "flex-end", gap: 8 },
  assistantBubble: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 16,
    paddingVertical: 12,
    maxWidth: "80%",
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  assistantText: { color: Colors.text.primary, fontSize: 15, lineHeight: 21 },
  inputBar: {
    flexDirection: "row",
    alignItems: "flex-end",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: Colors.text.primary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    maxHeight: 100,
  },
  sendBtn: { borderRadius: 20, overflow: "hidden" },
  sendGradient: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
  },
  footer: { paddingHorizontal: 32, paddingBottom: 40 },
  nextBtn: { paddingVertical: 18, borderRadius: 16, alignItems: "center" },
  nextText: { fontSize: 17, fontWeight: "700", color: "#FFF" },
});
