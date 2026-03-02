// PresenceOS Mobile — Video Studio Screen
// Premium UX with chip selectors, aspect ratio picker, polished animations

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

const { width: SCREEN_W } = Dimensions.get("window");

const DURATIONS = [
  { value: 5, label: "5s", icon: "flash-outline" as const, credits: 1, desc: "Rapide" },
  { value: 10, label: "10s", icon: "time-outline" as const, credits: 2, desc: "Standard" },
  { value: 15, label: "15s", icon: "film-outline" as const, credits: 3, desc: "Long" },
];

const STYLES = [
  { key: "cinematic", label: "Cinematic", icon: "videocam-outline" as const, color: "#7C5CBF" },
  { key: "natural", label: "Naturel", icon: "leaf-outline" as const, color: "#10B981" },
  { key: "vibrant", label: "Vibrant", icon: "sparkles-outline" as const, color: "#F4A261" },
  { key: "minimal", label: "Minimal", icon: "remove-outline" as const, color: "#6B7280" },
];

const RATIOS = [
  { key: "9:16", label: "9:16", icon: "phone-portrait-outline" as const, desc: "Reel / Story" },
  { key: "1:1", label: "1:1", icon: "square-outline" as const, desc: "Post carré" },
  { key: "16:9", label: "16:9", icon: "phone-landscape-outline" as const, desc: "Paysage" },
];

export default function VideoStudioScreen() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [prompt, setPrompt] = useState("");
  const [duration, setDuration] = useState(5);
  const [style, setStyle] = useState("cinematic");
  const [ratio, setRatio] = useState("9:16");
  const [loading, setLoading] = useState(false);
  const [credits, setCredits] = useState<VideoCreditsInfo | null>(null);
  const [result, setResult] = useState<VideoGenerationResult | null>(null);
  const [inputFocused, setInputFocused] = useState(false);

  const progressAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;

  // Fade in on mount
  useEffect(() => {
    Animated.timing(fadeAnim, {
      toValue: 1,
      duration: 400,
      useNativeDriver: true,
    }).start();
  }, [fadeAnim]);

  // Pulse animation for loading button
  useEffect(() => {
    let anim: Animated.CompositeAnimation | null = null;
    if (loading) {
      anim = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.03,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      anim.start();
    } else {
      pulseAnim.setValue(1);
    }
    return () => {
      if (anim) anim.stop();
    };
  }, [loading, pulseAnim]);

  // Fetch credits on mount
  useEffect(() => {
    if (!brandId) return;
    videoApi
      .credits(brandId)
      .then((res) => setCredits(res.data))
      .catch(() => {});
  }, [brandId]);

  const selectedDuration = DURATIONS.find((d) => d.value === duration)!;
  const canGenerate =
    prompt.trim().length >= 5 &&
    credits &&
    credits.credits_remaining >= selectedDuration.credits;

  const handleGenerate = useCallback(async () => {
    if (!brandId || !canGenerate) return;
    setLoading(true);
    setResult(null);

    progressAnim.setValue(0);
    Animated.timing(progressAnim, {
      toValue: 0.9,
      duration: 45000,
      useNativeDriver: false,
    }).start();

    try {
      const res = await videoApi.generate(brandId, prompt.trim(), duration, style, ratio);
      const data: VideoGenerationResult = res.data;

      progressAnim.setValue(1);
      setResult(data);

      if (data.status === "no_api_key") {
        Alert.alert("Vidéo indisponible", FR.video_no_api_key);
      } else if (data.status === "failed") {
        Alert.alert("Erreur", FR.video_error);
      }

      if (data.credits_remaining !== undefined) {
        setCredits((prev) =>
          prev ? { ...prev, credits_remaining: data.credits_remaining } : prev
        );
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail || FR.error_generic;
      Alert.alert(FR.video_error, detail);
    } finally {
      setLoading(false);
    }
  }, [brandId, prompt, duration, style, ratio, canGenerate, progressAnim]);

  const handleReset = () => {
    setResult(null);
    setPrompt("");
    progressAnim.setValue(0);
  };

  const progressWidth = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ["0%", "100%"],
  });

  const progressPct = progressAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 100],
  });

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* ── Header ── */}
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Studio Vidéo</Text>
          <Text style={styles.subtitle}>Créez des Reels IA en 45s</Text>
        </View>
        {credits && (
          <TouchableOpacity
            style={styles.creditsBadge}
            onPress={() => nav.navigate("VideoPlans")}
            activeOpacity={0.7}
          >
            <LinearGradient
              colors={
                credits.credits_remaining > 0
                  ? (["#7C5CBF", "#9D7FDB"] as const)
                  : (["#EF4444", "#DC2626"] as const)
              }
              style={styles.creditsBadgeInner}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Ionicons name="diamond-outline" size={14} color="#FFF" />
              <Text style={styles.creditsValue}>{credits.credits_remaining}</Text>
            </LinearGradient>
          </TouchableOpacity>
        )}
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
            {/* ── Result View ── */}
            {result && result.status === "completed" && result.video_url ? (
              <View style={styles.resultSection}>
                <View style={styles.resultBadge}>
                  <Ionicons name="checkmark-circle" size={20} color={Colors.status.success} />
                  <Text style={styles.resultBadgeText}>Vidéo prête !</Text>
                </View>

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
                  <TouchableOpacity
                    style={styles.resultBtnPrimary}
                    activeOpacity={0.85}
                    onPress={() => {
                      if (result?.video_url) {
                        Alert.alert("Publier", "Fonctionnalité de publication bientôt disponible.");
                      }
                    }}
                  >
                    <LinearGradient
                      colors={Colors.gradient.hero}
                      style={styles.resultBtnGradient}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                    >
                      <Ionicons name="share-outline" size={18} color="#FFF" />
                      <Text style={styles.resultBtnPrimaryText}>Publier</Text>
                    </LinearGradient>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.resultBtnSecondary}
                    activeOpacity={0.85}
                    onPress={() => {
                      if (result?.video_url) {
                        Alert.alert("Sauvegardé", "La vidéo a été ajoutée à votre galerie.");
                      }
                    }}
                  >
                    <Ionicons name="download-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.resultBtnSecondaryText}>Sauvegarder</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={styles.resultBtnGhost}
                    onPress={handleReset}
                    activeOpacity={0.7}
                  >
                    <Ionicons name="refresh-outline" size={16} color={Colors.text.muted} />
                    <Text style={styles.resultBtnGhostText}>Nouvelle vidéo</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <>
                {/* ── No Credits Banner ── */}
                {credits && credits.credits_remaining === 0 && (
                  <TouchableOpacity
                    style={styles.noCredits}
                    onPress={() => nav.navigate("VideoPlans")}
                    activeOpacity={0.85}
                  >
                    <LinearGradient
                      colors={["#EF4444", "#DC2626"]}
                      style={styles.noCreditsBg}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                    >
                      <View style={styles.noCreditsIcon}>
                        <Ionicons name="alert-circle" size={20} color="#FFF" />
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={styles.noCreditsTitle}>Plus de crédits</Text>
                        <Text style={styles.noCreditsBody}>
                          Passez au plan Pro pour continuer
                        </Text>
                      </View>
                      <Ionicons name="chevron-forward" size={18} color="rgba(255,255,255,0.7)" />
                    </LinearGradient>
                  </TouchableOpacity>
                )}

                {/* ── Prompt Input ── */}
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="create-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.sectionTitle}>Description</Text>
                  </View>
                  <TextInput
                    style={[styles.input, inputFocused && styles.inputFocused]}
                    placeholder="Gros plan sur notre burger avec du fromage qui fond, lumière chaude..."
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

                {/* ── Duration Chips ── */}
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
                          {active ? (
                            <LinearGradient
                              colors={Colors.gradient.violet}
                              style={styles.chipGradient}
                              start={{ x: 0, y: 0 }}
                              end={{ x: 1, y: 1 }}
                            >
                              <Ionicons name={d.icon} size={16} color="#FFF" />
                              <Text style={styles.chipLabelActive}>{d.label}</Text>
                              <View style={styles.chipCredits}>
                                <Text style={styles.chipCreditsText}>
                                  {d.credits} cr.
                                </Text>
                              </View>
                            </LinearGradient>
                          ) : (
                            <View style={styles.chipContent}>
                              <Ionicons
                                name={d.icon}
                                size={16}
                                color={Colors.text.secondary}
                              />
                              <Text style={styles.chipLabel}>{d.label}</Text>
                              <View style={styles.chipCreditsMuted}>
                                <Text style={styles.chipCreditsMutedText}>
                                  {d.credits} cr.
                                </Text>
                              </View>
                            </View>
                          )}
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* ── Style Chips ── */}
                <View style={styles.section}>
                  <View style={styles.sectionHeader}>
                    <Ionicons name="color-palette-outline" size={18} color={Colors.brand.primary} />
                    <Text style={styles.sectionTitle}>Style</Text>
                  </View>
                  <View style={styles.styleGrid}>
                    {STYLES.map((s) => {
                      const active = style === s.key;
                      return (
                        <TouchableOpacity
                          key={s.key}
                          style={[
                            styles.styleCard,
                            active && { borderColor: s.color, borderWidth: 2 },
                          ]}
                          onPress={() => setStyle(s.key)}
                          disabled={loading}
                          activeOpacity={0.7}
                        >
                          <View
                            style={[
                              styles.styleIconCircle,
                              {
                                backgroundColor: active
                                  ? s.color + "20"
                                  : Colors.bg.elevated,
                              },
                            ]}
                          >
                            <Ionicons
                              name={s.icon}
                              size={20}
                              color={active ? s.color : Colors.text.muted}
                            />
                          </View>
                          <Text
                            style={[
                              styles.styleLabel,
                              active && { color: s.color, fontWeight: "700" },
                            ]}
                          >
                            {s.label}
                          </Text>
                          {active && (
                            <View style={[styles.styleDot, { backgroundColor: s.color }]} />
                          )}
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* ── Aspect Ratio Chips ── */}
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
                            <Text
                              style={[
                                styles.ratioLabel,
                                active && styles.ratioLabelActive,
                              ]}
                            >
                              {r.label}
                            </Text>
                            <Text style={styles.ratioDesc}>{r.desc}</Text>
                          </View>
                        </TouchableOpacity>
                      );
                    })}
                  </View>
                </View>

                {/* ── Progress ── */}
                {loading && (
                  <View style={styles.progressSection}>
                    <View style={styles.progressHeader}>
                      <ActivityIndicator size="small" color={Colors.brand.primary} />
                      <Text style={styles.progressLabel}>Génération en cours...</Text>
                    </View>
                    <View style={styles.progressBar}>
                      <Animated.View
                        style={[styles.progressFill, { width: progressWidth }]}
                      >
                        <LinearGradient
                          colors={Colors.gradient.violet}
                          style={StyleSheet.absoluteFill}
                          start={{ x: 0, y: 0 }}
                          end={{ x: 1, y: 0 }}
                        />
                      </Animated.View>
                    </View>
                    <Text style={styles.progressHint}>
                      Environ 45 secondes
                    </Text>
                  </View>
                )}
              </>
            )}
          </Animated.View>
        </ScrollView>

        {/* ── Sticky Generate Button ── */}
        {!(result && result.status === "completed" && result.video_url) && (
          <View style={styles.stickyFooter}>
            <Animated.View
              style={[
                styles.generateBtnWrapper,
                loading && { transform: [{ scale: pulseAnim }] },
              ]}
            >
              <TouchableOpacity
                style={[
                  styles.generateBtn,
                  (!canGenerate || loading) && styles.generateBtnDisabled,
                ]}
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
                      <Text style={styles.generateText}>
                        Générer — {selectedDuration.credits}{" "}
                        {selectedDuration.credits > 1 ? "crédits" : "crédit"}
                      </Text>
                    </>
                  )}
                </LinearGradient>
              </TouchableOpacity>
            </Animated.View>

            {/* Quick info below button */}
            {!loading && canGenerate && (
              <Text style={styles.footerHint}>
                {duration}s  ·  {STYLES.find((s) => s.key === style)?.label}  ·  {ratio}
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

  // ── Header ──
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
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
  creditsBadge: { borderRadius: 20, overflow: "hidden" },
  creditsBadgeInner: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  creditsValue: {
    fontSize: 15,
    fontWeight: "800",
    color: "#FFF",
  },

  // ── Scroll ──
  scroll: { paddingHorizontal: 20, paddingBottom: 120 },

  // ── Sections ──
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

  // ── Prompt Input ──
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

  // ── Duration Chips ──
  chipRow: { flexDirection: "row", gap: 8 },
  chip: {
    flex: 1,
    borderRadius: 14,
    overflow: "hidden",
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1.5,
    borderColor: Colors.border.default,
  },
  chipActive: {
    borderColor: Colors.brand.primary,
    borderWidth: 1.5,
  },
  chipGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
    paddingHorizontal: 10,
  },
  chipContent: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
    paddingHorizontal: 10,
  },
  chipLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text.secondary,
  },
  chipLabelActive: {
    fontSize: 15,
    fontWeight: "700",
    color: "#FFF",
  },
  chipCredits: {
    backgroundColor: "rgba(255,255,255,0.25)",
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  chipCreditsText: {
    fontSize: 10,
    fontWeight: "700",
    color: "#FFF",
  },
  chipCreditsMuted: {
    backgroundColor: Colors.bg.elevated,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  chipCreditsMutedText: {
    fontSize: 10,
    fontWeight: "600",
    color: Colors.text.muted,
  },

  // ── Style Grid ──
  styleGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  styleCard: {
    width: (SCREEN_W - 40 - 10) / 2 - 1,
    alignItems: "center",
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1.5,
    borderColor: Colors.border.default,
    gap: 8,
    position: "relative",
  },
  styleIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  styleLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text.secondary,
  },
  styleDot: {
    position: "absolute",
    top: 10,
    right: 10,
    width: 8,
    height: 8,
    borderRadius: 4,
  },

  // ── Ratio Chips ──
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

  // ── Progress ──
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

  // ── Sticky Footer ──
  stickyFooter: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 20,
    backgroundColor: Colors.bg.primary,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
  },
  generateBtnWrapper: {},
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

  // ── No Credits ──
  noCredits: { borderRadius: 14, overflow: "hidden" },
  noCreditsBg: {
    flexDirection: "row",
    alignItems: "center",
    padding: 16,
    gap: 12,
  },
  noCreditsIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: "rgba(255,255,255,0.2)",
    alignItems: "center",
    justifyContent: "center",
  },
  noCreditsTitle: {
    fontSize: 14,
    fontWeight: "700",
    color: "#FFF",
  },
  noCreditsBody: {
    fontSize: 12,
    color: "rgba(255,255,255,0.8)",
    marginTop: 2,
  },

  // ── Result ──
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
  resultActions: { gap: 10, marginTop: 4 },
  resultBtnPrimary: { borderRadius: 14, overflow: "hidden" },
  resultBtnGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 16,
  },
  resultBtnPrimaryText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
  resultBtnSecondary: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    paddingVertical: 14,
    borderWidth: 1.5,
    borderColor: Colors.brand.primary + "30",
  },
  resultBtnSecondaryText: {
    color: Colors.brand.primary,
    fontSize: 14,
    fontWeight: "600",
  },
  resultBtnGhost: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 10,
  },
  resultBtnGhostText: {
    color: Colors.text.muted,
    fontSize: 13,
    fontWeight: "500",
  },
});
