// PresenceOS Mobile — Video Studio Screen (dark theme, French)

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
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Video, ResizeMode } from "expo-av";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { VideoStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { videoApi } from "@/lib/api";
import { VideoCreditsInfo, VideoGenerationResult } from "@/types";

type Nav = NativeStackNavigationProp<VideoStackParams>;

const DURATIONS = [
  { value: 5, label: "5s", credits: 1 },
  { value: 10, label: "10s", credits: 2 },
  { value: 15, label: "15s", credits: 3 },
];

const STYLES = [
  { key: "cinematic", label: FR.video_style_cinematic, emoji: "🎬" },
  { key: "natural", label: FR.video_style_natural, emoji: "🌿" },
  { key: "vibrant", label: FR.video_style_vibrant, emoji: "✨" },
];

export default function VideoStudioScreen() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(5);
  const [style, setStyle] = useState("cinematic");
  const [loading, setLoading] = useState(false);
  const [credits, setCredits] = useState<VideoCreditsInfo | null>(null);
  const [result, setResult] = useState<VideoGenerationResult | null>(null);
  const [inputFocused, setInputFocused] = useState(false);

  const progressAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;

  // Pulse animation for loading button
  useEffect(() => {
    if (loading) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.05,
            duration: 800,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 800,
            useNativeDriver: true,
          }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [loading, pulseAnim]);

  // Fetch credits on mount
  useEffect(() => {
    if (!brandId) return;
    videoApi.credits(brandId).then((res) => {
      setCredits(res.data);
    }).catch(() => {});
  }, [brandId]);

  const selectedDuration = DURATIONS.find((d) => d.value === duration)!;
  const canGenerate = prompt.trim().length >= 5 && credits && credits.credits_remaining >= selectedDuration.credits;

  const handleGenerate = useCallback(async () => {
    if (!brandId || !canGenerate) return;
    setLoading(true);
    setResult(null);

    // Animate progress bar
    progressAnim.setValue(0);
    Animated.timing(progressAnim, {
      toValue: 0.9,
      duration: 45000,
      useNativeDriver: false,
    }).start();

    try {
      const res = await videoApi.generate(brandId, prompt.trim(), duration, style);
      const data: VideoGenerationResult = res.data;

      progressAnim.setValue(1);
      setResult(data);

      if (data.status === "no_api_key") {
        Alert.alert("⚠️", FR.video_no_api_key);
      } else if (data.status === "failed") {
        Alert.alert("❌", FR.video_error);
      }

      // Update credits
      if (data.credits_remaining !== undefined) {
        setCredits((prev) => prev ? { ...prev, credits_remaining: data.credits_remaining } : prev);
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || FR.error_generic;
      Alert.alert(FR.video_error, detail);
    } finally {
      setLoading(false);
    }
  }, [brandId, prompt, duration, style, canGenerate, progressAnim]);

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
      {/* Header with gradient background */}
      <LinearGradient
        colors={Colors.gradient.hero}
        style={styles.headerGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 0 }}
      >
        <View style={styles.header}>
          <Text style={styles.title}>{FR.video_title}</Text>
          {credits && (
            <TouchableOpacity
              style={styles.creditsBadge}
              onPress={() => nav.navigate("VideoPlans")}
            >
              <Text style={styles.creditsValue}>{credits.credits_remaining}</Text>
              <Text style={styles.creditsLabel}>{FR.video_credits}</Text>
            </TouchableOpacity>
          )}
        </View>
      </LinearGradient>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
      >
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Result view */}
          {result && result.status === "completed" && result.video_url ? (
            <View style={styles.resultSection}>
              <Text style={styles.resultTitle}>{FR.video_result_title}</Text>
              <View style={styles.videoContainer}>
                <Video
                  source={{ uri: result.video_url }}
                  style={styles.videoPlayer}
                  useNativeControls
                  resizeMode={ResizeMode.CONTAIN}
                  isLooping
                  shouldPlay
                />
              </View>

              <View style={styles.resultActions}>
                <TouchableOpacity style={styles.resultBtn}>
                  <LinearGradient
                    colors={Colors.gradient.violet}
                    style={styles.resultBtnGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                  >
                    <Ionicons name="share-outline" size={18} color="#FFF" />
                    <Text style={styles.resultBtnText}>{FR.video_publish}</Text>
                  </LinearGradient>
                </TouchableOpacity>
                <TouchableOpacity style={styles.resultBtnSecondary} onPress={handleReset}>
                  <Ionicons name="add-circle-outline" size={18} color={Colors.text.secondary} />
                  <Text style={styles.resultBtnSecondaryText}>{FR.video_new}</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <>
              {/* No credits banner */}
              {credits && credits.credits_remaining === 0 && (
                <TouchableOpacity
                  style={styles.noCredits}
                  onPress={() => nav.navigate("VideoPlans")}
                >
                  <LinearGradient
                    colors={[...Colors.gradient.hero]}
                    style={styles.noCreditsBg}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                  >
                    <Text style={styles.noCreditsTitle}>{FR.video_no_credits}</Text>
                    <Text style={styles.noCreditsBody}>{FR.video_no_credits_body}</Text>
                    <Text style={styles.noCreditsBtn}>{FR.video_upgrade} →</Text>
                  </LinearGradient>
                </TouchableOpacity>
              )}

              {/* Prompt */}
              <Text style={styles.label}>Décrivez votre vidéo</Text>
              <TextInput
                style={[
                  styles.input,
                  inputFocused && styles.inputFocused,
                ]}
                placeholder={FR.video_prompt_placeholder}
                placeholderTextColor={Colors.text.muted}
                value={prompt}
                onChangeText={setPrompt}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                multiline
                numberOfLines={4}
                textAlignVertical="top"
                editable={!loading}
              />

              {/* Duration */}
              <Text style={styles.label}>{FR.video_duration}</Text>
              <View style={styles.optionRow}>
                {DURATIONS.map((d) => (
                  <TouchableOpacity
                    key={d.value}
                    style={[styles.optionBtn, duration === d.value && styles.optionBtnActive]}
                    onPress={() => setDuration(d.value)}
                    disabled={loading}
                  >
                    {duration === d.value ? (
                      <LinearGradient
                        colors={Colors.gradient.violet}
                        style={styles.optionBtnGradient}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 0 }}
                      >
                        <Text style={[styles.optionText, styles.optionTextActive]}>
                          {d.label}
                        </Text>
                        <Text style={[styles.optionSub, styles.optionSubActive]}>
                          {d.credits} {FR.video_credits}
                        </Text>
                      </LinearGradient>
                    ) : (
                      <>
                        <Text style={styles.optionText}>
                          {d.label}
                        </Text>
                        <Text style={styles.optionSub}>
                          {d.credits} {FR.video_credits}
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                ))}
              </View>

              {/* Style */}
              <Text style={styles.label}>{FR.video_style}</Text>
              <View style={styles.optionRow}>
                {STYLES.map((s) => (
                  <TouchableOpacity
                    key={s.key}
                    style={[styles.optionBtn, style === s.key && styles.optionBtnActive]}
                    onPress={() => setStyle(s.key)}
                    disabled={loading}
                  >
                    {style === s.key ? (
                      <View style={[styles.optionBtnContentActive]}>
                        <Text style={styles.optionEmoji}>{s.emoji}</Text>
                        <Text style={[styles.optionText, styles.optionTextActive]}>
                          {s.label}
                        </Text>
                      </View>
                    ) : (
                      <>
                        <Text style={styles.optionEmoji}>{s.emoji}</Text>
                        <Text style={styles.optionText}>
                          {s.label}
                        </Text>
                      </>
                    )}
                  </TouchableOpacity>
                ))}
              </View>

              {/* Progress bar during generation */}
              {loading && (
                <View style={styles.progressSection}>
                  <View style={styles.progressBar}>
                    <Animated.View style={[styles.progressFill, { width: progressWidth }]} />
                  </View>
                  <Text style={styles.progressText}>{FR.video_generating}</Text>
                </View>
              )}

              {/* Generate button */}
              <Animated.View
                style={[
                  styles.generateBtnWrapper,
                  loading && { transform: [{ scale: pulseAnim }] },
                ]}
              >
                <TouchableOpacity
                  style={[styles.generateBtn, (!canGenerate || loading) && styles.generateBtnDisabled]}
                  onPress={handleGenerate}
                  disabled={!canGenerate || loading}
                >
                  <LinearGradient
                    colors={canGenerate && !loading ? [...Colors.gradient.hero] : ["#E5E7EB", "#D1D5DB"]}
                    style={styles.generateGradient}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                  >
                    {loading ? (
                      <ActivityIndicator color="#FFF" />
                    ) : (
                      <>
                        <Ionicons name="videocam" size={20} color="#FFF" />
                        <Text style={styles.generateText}>
                          {FR.video_generate} — {selectedDuration.credits} {FR.video_credits}
                        </Text>
                      </>
                    )}
                  </LinearGradient>
                </TouchableOpacity>
              </Animated.View>
            </>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  headerGradient: {
    paddingBottom: 12,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 12,
  },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary },
  creditsBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: "rgba(244,162,97,0.15)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: Colors.brand.amber + "40",
  },
  creditsValue: { fontSize: 16, fontWeight: "800", color: Colors.brand.amber },
  creditsLabel: { fontSize: 11, fontWeight: "600", color: Colors.brand.amber },

  scroll: { padding: 20, paddingBottom: 100 },

  label: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.secondary,
    marginBottom: 8,
    marginTop: 16,
  },
  input: {
    backgroundColor: Colors.bg.elevated,
    borderWidth: 1,
    borderColor: Colors.border.default,
    borderRadius: 14,
    padding: 16,
    fontSize: 15,
    color: Colors.text.primary,
    minHeight: 100,
    textAlignVertical: "top",
  },
  inputFocused: {
    borderColor: Colors.brand.primary,
    shadowColor: Colors.brand.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },

  optionRow: { flexDirection: "row", gap: 8 },
  optionBtn: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    paddingHorizontal: 8,
    borderRadius: 14,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    gap: 4,
    overflow: "hidden",
  },
  optionBtnActive: {
    backgroundColor: "transparent",
    borderColor: Colors.brand.primary,
  },
  optionBtnGradient: {
    width: "100%",
    height: "100%",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    paddingHorizontal: 8,
    gap: 4,
  },
  optionBtnContentActive: {
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    backgroundColor: Colors.brand.primary,
    width: "100%",
    height: "100%",
    paddingVertical: 14,
    paddingHorizontal: 8,
  },
  optionEmoji: { fontSize: 20 },
  optionText: { fontSize: 14, fontWeight: "600", color: Colors.text.secondary },
  optionTextActive: { color: "#FFF" },
  optionSub: { fontSize: 10, color: Colors.text.muted },
  optionSubActive: { color: "rgba(255,255,255,0.9)" },

  progressSection: { marginTop: 20 },
  progressBar: {
    height: 6,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 99,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    borderRadius: 99,
    backgroundColor: Colors.brand.primary,
  },
  progressText: {
    fontSize: 13,
    color: Colors.text.secondary,
    textAlign: "center",
    marginTop: 8,
    fontWeight: "500",
  },

  generateBtnWrapper: {
    marginTop: 24,
  },
  generateBtn: {
    borderRadius: 28,
    overflow: "hidden",
  },
  generateBtnDisabled: { opacity: 0.5 },
  generateGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    paddingVertical: 16,
  },
  generateText: { color: "#FFF", fontSize: 16, fontWeight: "700" },

  noCredits: { borderRadius: 16, overflow: "hidden", marginBottom: 8 },
  noCreditsBg: { padding: 20, borderRadius: 16, gap: 6 },
  noCreditsTitle: { fontSize: 16, fontWeight: "700", color: "#FFF" },
  noCreditsBody: { fontSize: 13, color: "rgba(255,255,255,0.8)" },
  noCreditsBtn: { fontSize: 14, fontWeight: "700", color: "#FFF", marginTop: 8 },

  resultSection: { gap: 16 },
  resultTitle: { fontSize: 20, fontWeight: "700", color: Colors.text.primary, textAlign: "center" },
  videoContainer: { borderRadius: 16, overflow: "hidden", backgroundColor: Colors.bg.secondary },
  videoPlayer: { width: "100%", aspectRatio: 9 / 16, maxHeight: 450 },
  resultActions: { gap: 10 },
  resultBtn: {
    borderRadius: 14,
    overflow: "hidden",
  },
  resultBtnGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 16,
  },
  resultBtnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
  resultBtnSecondary: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    paddingVertical: 14,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  resultBtnSecondaryText: { color: Colors.text.secondary, fontSize: 14, fontWeight: "600" },
});
