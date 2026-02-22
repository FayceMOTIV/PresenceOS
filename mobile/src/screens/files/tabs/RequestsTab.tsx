// PresenceOS Mobile — Requests Tab (dark theme, French)

import React, { useContext, useState, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { contentApi } from "@/lib/api";

const CONTENT_TYPES = [
  { key: "reel", label: "Reel" },
  { key: "post", label: "Post" },
  { key: "story", label: "Story" },
];

const PLATFORMS = [
  { key: "instagram", label: "Instagram" },
  { key: "tiktok", label: "TikTok" },
  { key: "facebook", label: "Facebook" },
];

export default function RequestsTab() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [requestText, setRequestText] = useState("");
  const [contentType, setContentType] = useState("post");
  const [platform, setPlatform] = useState("instagram");
  const [loading, setLoading] = useState(false);

  const handleGenerate = useCallback(async () => {
    if (!brandId || !requestText.trim()) return;
    setLoading(true);
    try {
      await contentApi.createRequest(brandId, {
        request_text: requestText.trim(),
        content_type: contentType,
        platform,
      });
      Alert.alert("✨", "Proposition en cours de génération !");
      setRequestText("");
    } catch {
      Alert.alert(FR.error_generic);
    } finally {
      setLoading(false);
    }
  }, [brandId, requestText, contentType, platform]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <Text style={styles.title}>{FR.requests_title}</Text>

        {/* Quick chips */}
        <View style={styles.chips}>
          {FR.requests_chips.map((chip) => (
            <TouchableOpacity
              key={chip}
              style={styles.chip}
              onPress={() => setRequestText((prev) => prev ? `${prev} ${chip}` : chip)}
            >
              <Text style={styles.chipText}>{chip}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Text input */}
        <TextInput
          style={styles.input}
          placeholder={FR.requests_placeholder}
          placeholderTextColor={Colors.text.muted}
          value={requestText}
          onChangeText={setRequestText}
          multiline
          numberOfLines={4}
          textAlignVertical="top"
        />

        {/* Content type */}
        <Text style={styles.label}>{FR.requests_type_label}</Text>
        <View style={styles.optionRow}>
          {CONTENT_TYPES.map((t) => (
            <TouchableOpacity
              key={t.key}
              style={[styles.optionBtn, contentType === t.key && styles.optionBtnActive]}
              onPress={() => setContentType(t.key)}
            >
              <Text style={[styles.optionText, contentType === t.key && styles.optionTextActive]}>
                {t.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Platform */}
        <Text style={styles.label}>Plateforme :</Text>
        <View style={styles.optionRow}>
          {PLATFORMS.map((p) => (
            <TouchableOpacity
              key={p.key}
              style={[styles.optionBtn, platform === p.key && styles.optionBtnActive]}
              onPress={() => setPlatform(p.key)}
            >
              <Text style={[styles.optionText, platform === p.key && styles.optionTextActive]}>
                {p.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Submit */}
        <TouchableOpacity
          style={[styles.submitBtn, (!requestText.trim() || loading) && styles.submitBtnDisabled]}
          onPress={handleGenerate}
          disabled={!requestText.trim() || loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <Text style={styles.submitText}>{FR.requests_generate}</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  scroll: { padding: 20, paddingBottom: 100 },
  title: { fontSize: 20, fontWeight: "700", color: Colors.text.primary, marginBottom: 16 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 16 },
  chip: { backgroundColor: Colors.bg.elevated, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1, borderColor: Colors.border.default },
  chipText: { fontSize: 13, color: Colors.text.secondary, fontWeight: "500" },
  input: { backgroundColor: Colors.bg.elevated, borderWidth: 1, borderColor: Colors.border.default, borderRadius: 14, padding: 16, fontSize: 15, color: Colors.text.primary, minHeight: 100, marginBottom: 20, textAlignVertical: "top" },
  label: { fontSize: 14, fontWeight: "600", color: Colors.text.secondary, marginBottom: 8 },
  optionRow: { flexDirection: "row", gap: 8, marginBottom: 20 },
  optionBtn: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12, backgroundColor: Colors.bg.secondary, borderWidth: 1, borderColor: Colors.border.default },
  optionBtnActive: { backgroundColor: Colors.brand.glow, borderColor: Colors.brand.primary },
  optionText: { fontSize: 14, fontWeight: "600", color: Colors.text.secondary },
  optionTextActive: { color: Colors.brand.primary },
  submitBtn: { backgroundColor: Colors.brand.primary, borderRadius: 14, paddingVertical: 16, alignItems: "center", marginTop: 8 },
  submitBtnDisabled: { opacity: 0.5 },
  submitText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
});
