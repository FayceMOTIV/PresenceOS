// PresenceOS Mobile — AI Video Generation Screen
// Text-to-video and image-to-video using Kling 2.6 Pro / Wan 2.6

import React, { useContext, useState, useCallback, useEffect, useRef } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Animated,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Video, ResizeMode } from "expo-av";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { aiVideoApi } from "@/lib/api";

const { width: SCREEN_W } = Dimensions.get("window");

const DURATIONS = [
  { value: 5, label: "5s", icon: "flash-outline" as const, desc: "Rapide" },
  { value: 10, label: "10s", icon: "time-outline" as const, desc: "Standard" },
];

const MODELS = [
  { key: "kling", label: "Kling 2.6 Pro", icon: "diamond-outline" as const, desc: "Qualité max" },
  { key: "wan", label: "Wan 2.6", icon: "sparkles-outline" as const, desc: "Budget" },
];

const RATIOS = [
  { key: "9:16", label: "9:16", icon: "phone-portrait-outline" as const, desc: "Reel / Story" },
  { key: "1:1", label: "1:1", icon: "square-outline" as const, desc: "Post carré" },
  { key: "16:9", label: "16:9", icon: "phone-landscape-outline" as const, desc: "Paysage" },
];

interface AIVideoResult {
  url: string;
  model: string;
  duration: number;
  aspect_ratio: string;
  persisted: boolean;
  generated_at: string;
}

export default function AIVideoScreen() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(5);
  const [model, setModel] = useState("kling");
  const [ratio, setRatio] = useState("9:16");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AIVideoResult | null>(null);
  const [inputFocused, setInputFocused] = useState(false);

  const progressAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: true,
    }).start();
  }, [fadeAnim]);

  const canGenerate = prompt.trim().length >= 5 && !loading;

  const handleGenerate = useCallback(async () => {
    if (!brandId || !canGenerate) return;
    setLoading(true);
    setResult(null);

    progressAnim.setValue(0);
    Animated.timing(progressAnim, {
      toValue: 0.9,
      duration: duration === 10 ? 90_000 : 60_000,
      useNativeDriver: false,
    }).start();

    try {
      const res = await aiVideoApi.textToVideo(brandId, prompt.trim(), duration, ratio, model);
      progressAnim.setValue(1);
      setResult(res.data);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || "La génération vidéo a échoué.";
      Alert.alert("Erreur", detail);
    } finally {
      setLoading(false);
    }
  }, [brandId, prompt, duration, model, ratio, canGenerate, progressAnim]);

  const handleReset = () => {
    setResult(null);
    setPrompt("");
    progressAnim.setValue(0);
  };

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>AI Vidéo</Text>
        <Text style={styles.subtitle}>Kling 2.6 Pro · Wan 2.6</Text>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View style={{ opacity: fadeAnim }}>
            {/* Result View */}
            {result ? (
              <View style={styles.resultSection}>
                <View style={styles.resultBadge}>
                  <Ionicons name="checkmark-circle" size={20} color={Colors.status.success} />
                  <Text style={styles.resultBadgeText}>Vidéo prête !</Text>
                </View>

                <View style={styles.videoContainer}>
                  <Video
                    source={{ uri: result.url }}
                    style={styles.videoPlayer}
                    useNativeControls
                    resizeMode={ResizeMode.CONTAIN}
                    isLooping
                    shouldPlay
                  />
                </View>

                <Text style={styles.resultMeta}>
                  {result.model.split("/").pop()} · {result.duration}s · {result.aspect_ratio}
                </Text>

                <TouchableOpacity
                  style={styles.resetBtn}
                  onPress={handleReset}
                  activeOpacity={0.7}
                >
                  <Ionicons name="refresh-outline" size={16} color={Colors.text.muted} />
                  <Text style={styles.resetBtnText}>Nouvelle vidéo</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <>
                {/* Prompt Input */}
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="create-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.sectionTitle}>Description</Text>
                  </View>
                  <TextInput
                    style={[styles.input, inputFocused && styles.inputFocused]}
                    placeholder="Un plat de pâtes fumant sur une table en bois, lumière chaude du soir..."
                    placeholderTextColor={Colors.text.muted}
                    value={prompt}
                    onChangeText={setPrompt}
                    onFocus={() => setInputFocused(true)}
                    onBlur={() => setInputFocused(false)}
                    multiline
                    numberOfLines={3}
                    textAlignVertical="top"
                    editable={!loading}
                  />
                  {prompt.length > 0 && prompt.length < 5 && (
                    <Text style={styles.inputHint}>Minimum 5 caractères</Text>
                  )}
                </View>

                {/* Model Selection */}
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="hardware-chip-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.sectionTitle}>Modèle</Text>
                  </View>
                  <View style={styles.chipRow}>
                    {MODELS.map((m) => {
                      const active = model === m.key;
                      return (
                        <TouchableOpacity
                          key={m.key}
                          style={[styles.chip, active && styles.chipActive]}
                          onPress={() => setModel(m.key)}
                          disabled={loading}
                          activeOpacity={0.7}
                        >
                          <View style={styles.chipContent}>
                            <Ionicons
                              name={m.icon}
                              size={16}
                              color={active ? Colors.brand.primary : Colors.text.secondary}
                            />
                            <View>
                              <Text style={[styles.chipLabel, active && styles.chipLabelActive]}>
                                {m.label}
                              </Text>
                              <Text style={styles.chipDesc}>{m.desc}</Text>
                            </View>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* Duration Chips */}
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="timer-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.sectionTitle}>Durée</Text>
                  </View>
                  <View style={styles.chipRow}>
                    {DURATIONS.map((d) => {
                      const active = duration === d.value;
                      return (
                        <TouchableOpacity
                          key={d.value}
                          style={[styles.chip, active && styles.chipActive]}
                          onPress={() => setDuration(d.value)}
                          disabled={loading}
                          activeOpacity={0.7}
                        >
                          <View style={styles.chipContent}>
                            <Ionicons
                              name={d.icon}
                              size={16}
                              color={active ? Colors.brand.primary : Colors.text.secondary}
                            />
                            <Text style={[styles.chipLabel, active && styles.chipLabelActive]}>
                              {d.label}
                            </Text>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* Aspect Ratio Chips */}
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="resize-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.sectionTitle}>Format</Text>
                  </View>
                  <View style={styles.chipRow}>
                    {RATIOS.map((r) => {
                      const active = ratio === r.key;
                      return (
                        <TouchableOpacity
                          key={r.key}
                          style={[styles.ratioChip, active && styles.ratioChipActive]}
                          onPress={() => setRatio(r.key)}
                          disabled={loading}
                          activeOpacity={0.7}
                        >
                          <Ionicons
                            name={r.icon}
                            size={18}
                            color={active ? Colors.brand.primary : Colors.text.muted}
                          />
                          <View>
                            <Text style={[styles.ratioLabel, active && styles.ratioLabelActive]}>
                              {r.label}
                            </Text>
                            <Text style={styles.ratioDesc}>{r.desc}</Text>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* Progress */}
                {loading && (
                  <View style={styles.progressSection}>
                    <View style={styles.progressHeader}>
                      <ActivityIndicator size="small" color={Colors.brand.primary} />
                      <Text style={styles.progressLabel}>Génération en cours...</Text>
                    </View>
                    <View style={styles.progressBar}>
                      <Animated.View style={[styles.progressFill, { width: progressWidth }]}>
                        <LinearGradient
                          colors={Colors.gradient.violet}
                          style={StyleSheet.absoluteFill}
                          start={{ x: 0, y: 0 }}
                          end={{ x: 1, y: 0 }}
                        />
                      </Animated.View>
                    </View>
                    <Text style={styles.progressHint}>
                      Environ {duration === 10 ? "90" : "60"} secondes
                    </Text>
                  </View>
                )}
              </>
            )}
          </Animated.View>
        </ScrollView>

        {/* Sticky Generate Button */}
        {!result && (
          <View style={styles.stickyFooter}>
            <TouchableOpacity
              style={[styles.generateBtn, (!canGenerate || loading) && styles.generateBtnDisabled]}
              onPress={handleGenerate}
              disabled={!canGenerate || loading}
              activeOpacity={0.85}
            >
              <LinearGradient
                colors={
                  canGenerate && !loading
                    ? [...Colors.gradient.hero]
                    : (["#D1D5DB", "#9CA3AF"] as const)
                }
                style={styles.generateGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              >
                {loading ? (
                  <ActivityIndicator color="#FFF" size="small" />
                ) : (
                  <>
                    <Ionicons name="videocam" size={20} color="#FFF" />
                    <Text style={styles.generateText}>Générer la vidéo</Text>
                  </>
                )}
              </LinearGradient>
            </TouchableOpacity>

            {!loading && canGenerate && (
              <Text style={styles.footerHint}>
                {duration}s · {MODELS.find((m) => m.key === model)?.label} · {ratio}
              </Text>
            )}
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },

  header: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
    color: Colors.text.primary,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 13,
    color: Colors.text.muted,
    marginTop: 2,
  },

  scroll: { paddingHorizontal: 20, paddingBottom: 120 },

  section: { marginTop: 20 },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: 10,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.text.primary,
  },

  input: {
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1.5,
    borderColor: Colors.border.default,
    borderRadius: 16,
    padding: 16,
    fontSize: 15,
    color: Colors.text.primary,
    minHeight: 88,
    lineHeight: 22,
  },
  inputFocused: {
    borderColor: Colors.brand.primary,
    shadowColor: Colors.brand.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 4,
  },
  inputHint: {
    fontSize: 12,
    color: Colors.status.warning,
    marginTop: 6,
    marginLeft: 4,
  },

  chipRow: { flexDirection: "row", gap: 8 },
  chip: {
    flex: 1,
    borderRadius: 14,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1.5,
    borderColor: Colors.border.default,
  },
  chipActive: {
    borderColor: Colors.brand.primary,
    backgroundColor: Colors.brand.primary + "08",
  },
  chipContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 12,
  },
  chipLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.secondary,
  },
  chipLabelActive: {
    color: Colors.brand.primary,
    fontWeight: "700",
  },
  chipDesc: {
    fontSize: 10,
    color: Colors.text.muted,
    marginTop: 1,
  },

  ratioChip: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 14,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1.5,
    borderColor: Colors.border.default,
  },
  ratioChipActive: {
    borderColor: Colors.brand.primary,
    backgroundColor: Colors.brand.primary + "08",
  },
  ratioLabel: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.text.secondary,
  },
  ratioLabelActive: {
    color: Colors.brand.primary,
  },
  ratioDesc: {
    fontSize: 10,
    color: Colors.text.muted,
    marginTop: 1,
  },

  progressSection: {
    marginTop: 24,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 20,
    gap: 12,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  progressHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  progressLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.primary,
  },
  progressBar: {
    height: 8,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 99,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    borderRadius: 99,
    overflow: "hidden",
  },
  progressHint: {
    fontSize: 12,
    color: Colors.text.muted,
    textAlign: "center",
  },

  stickyFooter: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 20,
    backgroundColor: Colors.bg.primary,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
  },
  generateBtn: {
    borderRadius: 16,
    overflow: "hidden",
  },
  generateBtnDisabled: { opacity: 0.45 },
  generateGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    paddingVertical: 16,
  },
  generateText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "700",
  },
  footerHint: {
    fontSize: 12,
    color: Colors.text.muted,
    textAlign: "center",
    marginTop: 8,
  },

  resultSection: { gap: 16, paddingTop: 8 },
  resultBadge: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 10,
    backgroundColor: Colors.status.successLight,
    borderRadius: 12,
  },
  resultBadgeText: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.status.success,
  },
  videoContainer: {
    borderRadius: 20,
    overflow: "hidden",
    backgroundColor: "#000",
  },
  videoPlayer: {
    width: "100%",
    aspectRatio: 9 / 16,
    maxHeight: 450,
  },
  resultMeta: {
    fontSize: 12,
    color: Colors.text.muted,
    textAlign: "center",
  },
  resetBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
  },
  resetBtnText: {
    color: Colors.text.muted,
    fontSize: 13,
    fontWeight: "500",
  },
});
