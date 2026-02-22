// PresenceOS Mobile — Brief du Jour (dark theme, French)

import React, { useContext, useState, useCallback } from "react";
import {
  View, Text, TextInput, StyleSheet, TouchableOpacity, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { briefApi } from "@/lib/api";

export default function BriefDuJourScreen() {
  const nav = useNavigation();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSend = useCallback(async () => {
    if (!brandId || !response.trim()) return;
    setLoading(true);
    try {
      await briefApi.respond(brandId, response.trim());
      setDone(true);
    } catch {
      Alert.alert(FR.error_generic);
    } finally {
      setLoading(false);
    }
  }, [brandId, response]);

  if (done) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.doneContainer}>
          <Text style={styles.doneEmoji}>🎉</Text>
          <Text style={styles.doneTitle}>{FR.brief_done}</Text>
          <Text style={styles.doneBody}>{FR.brief_generating}</Text>
          <TouchableOpacity style={styles.doneBtn} onPress={() => nav.goBack()}>
            <Text style={styles.doneBtnText}>← Retour</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.inner}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        {/* Close button */}
        <TouchableOpacity style={styles.closeBtn} onPress={() => nav.goBack()}>
          <Ionicons name="close" size={24} color={Colors.text.secondary} />
        </TouchableOpacity>

        {/* Header */}
        <Text style={styles.emoji}>☀️</Text>
        <Text style={styles.title}>{FR.brief_title}</Text>
        <Text style={styles.subtitle}>{FR.brief_subtitle}</Text>

        {/* Quick chips */}
        <View style={styles.chips}>
          {FR.brief_chips.map((chip) => (
            <TouchableOpacity
              key={chip}
              style={styles.chip}
              onPress={() => setResponse((prev) => prev ? `${prev}, ${chip.toLowerCase()}` : chip)}
            >
              <Text style={styles.chipText}>{chip}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Text input */}
        <TextInput
          style={styles.input}
          placeholder={FR.brief_placeholder}
          placeholderTextColor={Colors.text.muted}
          value={response}
          onChangeText={setResponse}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
          autoFocus
        />

        {/* Submit */}
        <TouchableOpacity
          style={[styles.submitBtn, (!response.trim() || loading) && styles.submitBtnDisabled]}
          onPress={handleSend}
          disabled={!response.trim() || loading}
        >
          <LinearGradient
            colors={[...Colors.gradient.hero]}
            style={styles.submitGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            {loading ? (
              <ActivityIndicator color="#FFF" />
            ) : (
              <Text style={styles.submitText}>{FR.brief_send}</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  inner: { flex: 1, paddingHorizontal: 24, paddingTop: 16 },
  closeBtn: { alignSelf: "flex-end", padding: 4, marginBottom: 16 },
  emoji: { fontSize: 48, textAlign: "center", marginBottom: 16 },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary, textAlign: "center", marginBottom: 8 },
  subtitle: { fontSize: 14, color: Colors.text.secondary, textAlign: "center", lineHeight: 20, marginBottom: 24 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8, justifyContent: "center", marginBottom: 20 },
  chip: { backgroundColor: Colors.bg.elevated, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1, borderColor: Colors.border.default },
  chipText: { fontSize: 13, color: Colors.text.secondary, fontWeight: "500" },
  input: { backgroundColor: Colors.bg.elevated, borderWidth: 1, borderColor: Colors.border.default, borderRadius: 14, padding: 16, fontSize: 15, color: Colors.text.primary, minHeight: 120, marginBottom: 20, textAlignVertical: "top" },
  submitBtn: { borderRadius: 14, overflow: "hidden" },
  submitBtnDisabled: { opacity: 0.5 },
  submitGradient: { paddingVertical: 16, alignItems: "center" },
  submitText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
  doneContainer: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  doneEmoji: { fontSize: 64, marginBottom: 16 },
  doneTitle: { fontSize: 24, fontWeight: "700", color: Colors.text.primary, marginBottom: 8 },
  doneBody: { fontSize: 14, color: Colors.text.secondary, textAlign: "center", marginBottom: 24 },
  doneBtn: { paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12, backgroundColor: Colors.bg.secondary },
  doneBtnText: { color: Colors.text.primary, fontWeight: "600", fontSize: 15 },
});
