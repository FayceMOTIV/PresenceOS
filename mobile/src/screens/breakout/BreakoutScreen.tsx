// PresenceOS Mobile — Breakout Screen
// "Tim Gray" 3D frame-break video effect generator

import React, { useContext, useState, useEffect, useRef, useCallback } from "react";
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Image,
  Dimensions,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import * as ImagePicker from "expo-image-picker";
import { Video, ResizeMode } from "expo-av";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { breakoutApi } from "@/lib/api";

const { width: SCREEN_W } = Dimensions.get("window");

type SourceMode = "ai_prompt" | "image" | "video";
type Step = "input" | "generating" | "preview" | "error";

const POLL_INTERVAL_MS = 3000;

const PROGRESS_STEPS = [
  { label: "Génération vidéo source", threshold: 15 },
  { label: "Détection du sujet", threshold: 35 },
  { label: "Segmentation SAM2", threshold: 60 },
  { label: "Compositing Breakout", threshold: 85 },
  { label: "Finalisation", threshold: 100 },
];

export default function BreakoutScreen() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [mode, setMode] = useState<SourceMode>("ai_prompt");
  const [prompt, setPrompt] = useState("");
  const [sourceUri, setSourceUri] = useState<string | null>(null);
  const [step, setStep] = useState<Step>("input");
  const [jobId, setJobId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState("Initialisation...");
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const pollTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    return () => {
      if (pollTimer.current) clearInterval(pollTimer.current);
    };
  }, []);

  // ── Sélection média ────────────────────────────────────────────────────

  const pickMedia = useCallback(async (type: "image" | "video") => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes:
        type === "image"
          ? ImagePicker.MediaTypeOptions.Images
          : ImagePicker.MediaTypeOptions.Videos,
      quality: 0.9,
    });
    if (!result.canceled && result.assets.length > 0) {
      setSourceUri(result.assets[0].uri);
      setMode(type);
    }
  }, []);

  // ── Lancer la génération ───────────────────────────────────────────────

  const handleGenerate = useCallback(async () => {
    if (!brandId) {
      Alert.alert("Erreur", "Aucune marque sélectionnée");
      return;
    }
    if (mode === "ai_prompt" && !prompt.trim()) {
      Alert.alert("Prompt requis", "Entre une description pour la génération IA");
      return;
    }
    if ((mode === "image" || mode === "video") && !sourceUri) {
      Alert.alert("Fichier requis", "Sélectionne une photo ou vidéo");
      return;
    }

    setStep("generating");
    setProgress(0);
    setProgressLabel("Démarrage...");
    setErrorMsg(null);

    try {
      const res = await breakoutApi.generate(brandId, {
        source_type: mode,
        source_url: mode !== "ai_prompt" ? sourceUri : undefined,
        ai_prompt: mode === "ai_prompt" ? prompt : undefined,
      });

      const newJobId = res.data?.job_id;
      if (!newJobId) throw new Error("Pas de job_id dans la réponse");

      setJobId(newJobId);
      pollTimer.current = setInterval(() => pollStatus(newJobId), POLL_INTERVAL_MS);
    } catch (e: any) {
      setStep("error");
      setErrorMsg(e.message || "Erreur lors du lancement");
    }
  }, [brandId, mode, prompt, sourceUri]);

  // ── Polling statut ─────────────────────────────────────────────────────

  const pollStatus = useCallback(
    async (id: string) => {
      if (!brandId) return;
      try {
        const res = await breakoutApi.getStatus(brandId, id);
        const data = res.data;
        const p = data?.progress || 0;
        setProgress(p);

        const currentStep = PROGRESS_STEPS.find((s) => p <= s.threshold);
        setProgressLabel(currentStep?.label || "Traitement...");

        if (data?.status === "SUCCESS" && data?.video_url) {
          if (pollTimer.current) clearInterval(pollTimer.current);
          setResultUrl(data.video_url);
          setStep("preview");
        } else if (data?.status === "FAILURE") {
          if (pollTimer.current) clearInterval(pollTimer.current);
          setStep("error");
          setErrorMsg(data?.error || "Génération échouée");
        }
      } catch {
        // Silent — continue polling
      }
    },
    [brandId]
  );

  // ── Reset ──────────────────────────────────────────────────────────────

  const handleReset = useCallback(() => {
    setStep("input");
    setResultUrl(null);
    setSourceUri(null);
    setPrompt("");
    setJobId(null);
    setProgress(0);
  }, []);

  // ── RENDER ─────────────────────────────────────────────────────────────

  if (step === "generating") {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.brand.amber} />
          <View style={styles.progressBarContainer}>
            <LinearGradient
              colors={Colors.gradient.hero}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[styles.progressBar, { width: `${Math.max(progress, 3)}%` as any }]}
            />
          </View>
          <Text style={styles.progressPercent}>{progress}%</Text>
          <Text style={styles.progressLabel}>{progressLabel}</Text>
          <Text style={styles.progressEta}>~60-90 secondes</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (step === "error") {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.center}>
          <Ionicons name="alert-circle" size={56} color={Colors.status.danger} />
          <Text style={styles.errorText}>Génération échouée</Text>
          <Text style={styles.errorDetail}>{errorMsg}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={handleReset}>
            <Text style={styles.retryBtnText}>Réessayer</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  if (step === "preview" && resultUrl) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ScrollView style={styles.container} contentContainerStyle={styles.content}>
          <Text style={styles.title}>Preview Breakout</Text>
          <Video
            source={{ uri: resultUrl }}
            style={styles.videoPreview}
            useNativeControls
            resizeMode={ResizeMode.CONTAIN}
            isLooping
            shouldPlay
          />
          <View style={styles.actionsRow}>
            <TouchableOpacity style={[styles.actionBtn, styles.btnRefuse]} onPress={handleReset}>
              <Ionicons name="refresh" size={18} color="#FFF" style={{ marginRight: 6 }} />
              <Text style={styles.actionBtnText}>Refaire</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, styles.btnAccept]} onPress={handleReset}>
              <Ionicons name="checkmark" size={18} color="#FFF" style={{ marginRight: 6 }} />
              <Text style={styles.actionBtnText}>Sauvegarder</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ── Écran input ────────────────────────────────────────────────────────
  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.container} contentContainerStyle={styles.content}>
        <View style={styles.headerRow}>
          <Ionicons name="layers-outline" size={28} color={Colors.brand.primary} />
          <Text style={styles.title}>Breakout</Text>
        </View>
        <Text style={styles.subtitle}>Ton contenu sort du cadre — effet viral</Text>

        {/* Sélecteur de mode */}
        <View style={styles.modeRow}>
          {(
            [
              { key: "ai_prompt" as SourceMode, label: "IA", icon: "sparkles" as const },
              { key: "image" as SourceMode, label: "Photo", icon: "camera" as const },
              { key: "video" as SourceMode, label: "Vidéo", icon: "videocam" as const },
            ] as const
          ).map((m) => (
            <TouchableOpacity
              key={m.key}
              style={[styles.modeBtn, mode === m.key && styles.modeBtnActive]}
              onPress={() => {
                if (m.key === "image") pickMedia("image");
                else if (m.key === "video") pickMedia("video");
                else {
                  setMode("ai_prompt");
                  setSourceUri(null);
                }
              }}
            >
              <Ionicons
                name={m.icon}
                size={20}
                color={mode === m.key ? Colors.brand.primary : Colors.text.muted}
              />
              <Text style={[styles.modeBtnText, mode === m.key && styles.modeBtnTextActive]}>
                {m.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Prompt IA */}
        {mode === "ai_prompt" && (
          <TextInput
            style={styles.input}
            placeholder="Ex: burger qui déborde de sa boîte, slow-motion..."
            placeholderTextColor={Colors.text.muted}
            value={prompt}
            onChangeText={setPrompt}
            multiline
            numberOfLines={3}
          />
        )}

        {/* Preview source sélectionnée */}
        {sourceUri && mode === "image" && (
          <Image source={{ uri: sourceUri }} style={styles.sourcePreview} resizeMode="cover" />
        )}
        {sourceUri && mode === "video" && (
          <Video
            source={{ uri: sourceUri }}
            style={styles.sourcePreview}
            useNativeControls
            resizeMode={ResizeMode.COVER}
          />
        )}

        {/* Bouton génération */}
        <TouchableOpacity style={styles.generateBtn} onPress={handleGenerate}>
          <LinearGradient
            colors={Colors.gradient.hero}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.generateBtnGradient}
          >
            <Ionicons name="flash" size={20} color="#FFF" />
            <Text style={styles.generateBtnText}>Générer Breakout</Text>
          </LinearGradient>
        </TouchableOpacity>

        <Text style={styles.costHint}>~0.01€ par vidéo · 60-90 secondes</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Styles — Light theme RS3 ─────────────────────────────────────────────

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.bg.primary },
  container: { flex: 1 },
  content: { padding: 20, paddingBottom: 50 },
  center: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.bg.primary,
    padding: 24,
  },
  headerRow: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 4 },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary },
  subtitle: { fontSize: 13, color: Colors.text.secondary, marginBottom: 24 },

  // Mode selector
  modeRow: { flexDirection: "row", gap: 10, marginBottom: 20 },
  modeBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  modeBtnActive: {
    borderColor: Colors.brand.primary,
    backgroundColor: Colors.bg.elevated,
  },
  modeBtnText: { color: Colors.text.muted, fontWeight: "600", fontSize: 13 },
  modeBtnTextActive: { color: Colors.brand.primary },

  // Input
  input: {
    backgroundColor: Colors.bg.secondary,
    color: Colors.text.primary,
    borderRadius: 12,
    padding: 16,
    fontSize: 14,
    borderWidth: 1,
    borderColor: Colors.border.default,
    minHeight: 80,
    textAlignVertical: "top",
    marginBottom: 20,
  },
  sourcePreview: { width: "100%", height: 200, borderRadius: 12, marginBottom: 20 },

  // Generate button
  generateBtn: { borderRadius: 14, overflow: "hidden", marginTop: 4 },
  generateBtnGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 16,
  },
  generateBtnText: { color: "#FFF", fontWeight: "800", fontSize: 15 },
  costHint: { color: Colors.text.muted, fontSize: 11, textAlign: "center", marginTop: 10 },

  // Progress
  progressBarContainer: {
    width: "100%",
    height: 6,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 3,
    marginTop: 24,
    overflow: "hidden",
  },
  progressBar: { height: 6, borderRadius: 3 },
  progressPercent: {
    color: Colors.brand.amber,
    fontSize: 20,
    fontWeight: "700",
    marginTop: 12,
  },
  progressLabel: {
    color: Colors.text.primary,
    fontSize: 15,
    fontWeight: "600",
    marginTop: 8,
    textAlign: "center",
  },
  progressEta: { color: Colors.text.muted, fontSize: 12, marginTop: 8 },

  // Preview
  videoPreview: {
    width: "100%",
    height: SCREEN_W * (16 / 9),
    borderRadius: 12,
    marginVertical: 16,
    backgroundColor: Colors.bg.elevated,
  },
  actionsRow: { flexDirection: "row", gap: 12 },
  actionBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 14,
    borderRadius: 12,
  },
  btnAccept: { backgroundColor: Colors.status.success },
  btnRefuse: { backgroundColor: Colors.text.secondary },
  actionBtnText: { color: "#FFF", fontWeight: "700", fontSize: 14 },

  // Error
  errorText: { color: Colors.text.primary, fontSize: 18, fontWeight: "600", marginTop: 16 },
  errorDetail: {
    color: Colors.text.secondary,
    fontSize: 13,
    textAlign: "center",
    marginTop: 8,
    marginBottom: 24,
  },
  retryBtn: {
    backgroundColor: Colors.brand.amber,
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  retryBtnText: { color: "#FFF", fontWeight: "700", fontSize: 14 },
});
