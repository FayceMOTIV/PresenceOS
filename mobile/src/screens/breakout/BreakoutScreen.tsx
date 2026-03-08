// PresenceOS Mobile — Breakout Screen V3
// Photo upload -> rembg -> Remotion template -> MP4

import React, { useContext, useState, useRef, useCallback } from "react";
import {
  View,
  Text,
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

type Step = "input" | "generating" | "preview" | "error";

const PROGRESS_STEPS = [
  { label: "Upload de la photo...", range: [0, 8] },
  { label: "Detourage du sujet...", range: [8, 25] },
  { label: "Preparation de l'animation...", range: [25, 45] },
  { label: "Rendu de la video...", range: [45, 75] },
  { label: "Finalisation du clip...", range: [75, 90] },
  { label: "Presque pret...", range: [90, 100] },
] as const;

function getStepLabel(progress: number): string {
  const step = PROGRESS_STEPS.find(
    (s) => progress >= s.range[0] && progress < s.range[1]
  );
  return step?.label || "Finalisation...";
}

export default function BreakoutScreen() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;
  const brandName = brand?.activeBrand?.name || "Mon Restaurant";

  const [selectedPhoto, setSelectedPhoto] = useState<string | null>(null);
  const [step, setStep] = useState<Step>("input");
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState("Initialisation...");
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const pickPhoto = useCallback(async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
    });
    if (!result.canceled && result.assets.length > 0) {
      setSelectedPhoto(result.assets[0].uri);
    }
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!brandId) {
      Alert.alert("Erreur", "Aucune marque selectionnee");
      return;
    }
    if (!selectedPhoto) {
      Alert.alert("Photo requise", "Selectionne une photo de plat ou produit");
      return;
    }

    setStep("generating");
    setProgress(0);
    setProgressLabel("Upload de la photo...");
    setErrorMsg(null);

    // Simulated progress during the ~45-90s pipeline
    progressTimer.current = setInterval(() => {
      setProgress((prev) => {
        const next = Math.min(prev + 1, 95);
        setProgressLabel(getStepLabel(next));
        return next;
      });
    }, 1200);

    try {
      const formData = new FormData();
      formData.append("photo", {
        uri: selectedPhoto,
        type: "image/jpeg",
        name: "breakout_photo.jpg",
      } as any);
      formData.append("business_name", brandName);
      formData.append("instagram_handle", `@${brandName.toLowerCase().replace(/\s+/g, "")}`);
      formData.append("accent_color", "#F59E0B");

      const res = await breakoutApi.generate(brandId, formData);
      const videoUrl = res.data?.video_url;

      if (progressTimer.current) clearInterval(progressTimer.current);

      if (!videoUrl) {
        throw new Error("Pas de video_url dans la reponse");
      }

      setProgress(100);
      setResultUrl(videoUrl);
      setStep("preview");
    } catch (e: any) {
      if (progressTimer.current) clearInterval(progressTimer.current);
      setStep("error");
      const detail =
        e.response?.data?.detail || e.message || "Generation echouee";
      setErrorMsg(detail);
    }
  }, [brandId, brandName, selectedPhoto]);

  const handleReset = useCallback(() => {
    if (progressTimer.current) clearInterval(progressTimer.current);
    setStep("input");
    setResultUrl(null);
    setSelectedPhoto(null);
    setProgress(0);
    setErrorMsg(null);
  }, []);

  // ── Generating ──────────────────────────────────────────────────────────

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
              style={[
                styles.progressBar,
                { width: `${Math.max(progress, 3)}%` as any },
              ]}
            />
          </View>
          <Text style={styles.progressPercent}>{progress}%</Text>
          <Text style={styles.progressLabel}>{progressLabel}</Text>
          <Text style={styles.progressEta}>~1 minute</Text>
        </View>
      </SafeAreaView>
    );
  }

  // ── Error ───────────────────────────────────────────────────────────────

  if (step === "error") {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.center}>
          <Ionicons
            name="alert-circle"
            size={56}
            color={Colors.status.danger}
          />
          <Text style={styles.errorText}>Generation echouee</Text>
          <Text style={styles.errorDetail}>{errorMsg}</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={handleReset}>
            <Text style={styles.retryBtnText}>Reessayer</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // ── Preview ─────────────────────────────────────────────────────────────

  if (step === "preview" && resultUrl) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <ScrollView
          style={styles.container}
          contentContainerStyle={styles.content}
        >
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
            <TouchableOpacity
              style={[styles.actionBtn, styles.btnRefuse]}
              onPress={handleReset}
            >
              <Ionicons
                name="refresh"
                size={18}
                color="#FFF"
                style={{ marginRight: 6 }}
              />
              <Text style={styles.actionBtnText}>Refaire</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, styles.btnAccept]}
              onPress={handleReset}
            >
              <Ionicons
                name="checkmark"
                size={18}
                color="#FFF"
                style={{ marginRight: 6 }}
              />
              <Text style={styles.actionBtnText}>Sauvegarder</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // ── Input ───────────────────────────────────────────────────────────────

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
      >
        <View style={styles.headerRow}>
          <Ionicons
            name="layers-outline"
            size={28}
            color={Colors.brand.primary}
          />
          <Text style={styles.title}>Breakout</Text>
        </View>
        <Text style={styles.subtitle}>
          Effet 3D viral — ton contenu sort du cadre
        </Text>

        {/* Photo picker */}
        <TouchableOpacity style={styles.photoPickerBtn} onPress={pickPhoto}>
          {selectedPhoto ? (
            <Image
              source={{ uri: selectedPhoto }}
              style={styles.photoPreview}
              resizeMode="cover"
            />
          ) : (
            <View style={styles.photoPlaceholder}>
              <Ionicons
                name="camera-outline"
                size={48}
                color={Colors.text.muted}
              />
              <Text style={styles.photoPlaceholderText}>
                Choisis une photo de plat ou produit
              </Text>
            </View>
          )}
        </TouchableOpacity>

        {selectedPhoto && (
          <TouchableOpacity style={styles.changePhotoBtn} onPress={pickPhoto}>
            <Ionicons
              name="swap-horizontal"
              size={16}
              color={Colors.brand.primary}
            />
            <Text style={styles.changePhotoBtnText}>Changer la photo</Text>
          </TouchableOpacity>
        )}

        {/* Generate button */}
        <TouchableOpacity
          style={[styles.generateBtn, !selectedPhoto && styles.generateBtnDisabled]}
          onPress={handleGenerate}
          disabled={!selectedPhoto}
        >
          <LinearGradient
            colors={
              selectedPhoto ? Colors.gradient.hero : ["#D1D5DB", "#D1D5DB"]
            }
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.generateBtnGradient}
          >
            <Ionicons name="flash" size={20} color="#FFF" />
            <Text style={styles.generateBtnText}>Generer Breakout</Text>
          </LinearGradient>
        </TouchableOpacity>

        <Text style={styles.costHint}>Gratuit · ~1 minute</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────

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
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    marginBottom: 4,
  },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary },
  subtitle: {
    fontSize: 13,
    color: Colors.text.secondary,
    marginBottom: 24,
  },

  // Photo picker
  photoPickerBtn: {
    width: "100%",
    borderRadius: 16,
    overflow: "hidden",
    marginBottom: 12,
    borderWidth: 2,
    borderColor: Colors.border.default,
    borderStyle: "dashed",
  },
  photoPreview: {
    width: "100%",
    height: SCREEN_W * 0.8,
    borderRadius: 14,
  },
  photoPlaceholder: {
    width: "100%",
    height: SCREEN_W * 0.6,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: Colors.bg.secondary,
    gap: 12,
  },
  photoPlaceholderText: {
    color: Colors.text.muted,
    fontSize: 14,
    fontWeight: "500",
  },
  changePhotoBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginBottom: 20,
  },
  changePhotoBtnText: {
    color: Colors.brand.primary,
    fontWeight: "600",
    fontSize: 13,
  },

  // Generate button
  generateBtn: { borderRadius: 14, overflow: "hidden", marginTop: 4 },
  generateBtnDisabled: { opacity: 0.5 },
  generateBtnGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 16,
  },
  generateBtnText: { color: "#FFF", fontWeight: "800", fontSize: 16 },
  costHint: {
    color: Colors.text.muted,
    fontSize: 11,
    textAlign: "center",
    marginTop: 10,
  },

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
  errorText: {
    color: Colors.text.primary,
    fontSize: 18,
    fontWeight: "600",
    marginTop: 16,
  },
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
