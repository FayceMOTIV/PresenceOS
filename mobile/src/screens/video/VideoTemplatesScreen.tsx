// PresenceOS Mobile — Video Templates Screen
// Breakout V4 (free) + Cinematic Food ($0.35/5s)

import React, { useContext, useState, useCallback } from "react";
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
import { videoTemplatesApi } from "@/lib/api";

const { width: SCREEN_W } = Dimensions.get("window");

type TemplateId = "breakout" | "cinematic";
type FoodType = "default" | "burger" | "pizza" | "dessert" | "drink";
type Step = "select" | "configure" | "generating" | "preview";

const TEMPLATES: Array<{
  id: TemplateId;
  icon: string;
  title: string;
  subtitle: string;
  cost: string;
  costColor: string;
  duration: string;
  time: string;
}> = [
  {
    id: "breakout",
    icon: "layers-outline",
    title: "Breakout V4",
    subtitle: "Le sujet sort du cadre Instagram",
    cost: "Gratuit",
    costColor: Colors.status.success,
    duration: "3s",
    time: "~35s",
  },
  {
    id: "cinematic",
    icon: "film-outline",
    title: "Cinematic Food",
    subtitle: "Photo animee en video cinematique",
    cost: "$0.35",
    costColor: Colors.brand.amber,
    duration: "5s",
    time: "~90s",
  },
];

const FOOD_TYPES: Array<{ id: FoodType; label: string }> = [
  { id: "default", label: "Auto" },
  { id: "burger", label: "Burger" },
  { id: "pizza", label: "Pizza" },
  { id: "dessert", label: "Dessert" },
  { id: "drink", label: "Boisson" },
];

export default function VideoTemplatesScreen({ navigation }: any) {
  const brandCtx = useContext(BrandContext);
  const brandId = brandCtx?.activeBrand?.id ?? null;
  const brandName = brandCtx?.activeBrand?.name ?? null;
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateId | null>(null);
  const [selectedImage, setSelectedImage] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [foodType, setFoodType] = useState<FoodType>("default");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<Step>("select");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progressText, setProgressText] = useState("");

  const pickImage = useCallback(async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission requise", "Acces a la galerie necessaire.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images"],
      quality: 0.9,
      allowsEditing: true,
      aspect: [4, 5],
    });
    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0]);
      setStep("configure");
    }
  }, []);

  const takePhoto = useCallback(async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission requise", "Acces a la camera necessaire.");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      quality: 0.9,
      allowsEditing: true,
      aspect: [4, 5],
    });
    if (!result.canceled && result.assets[0]) {
      setSelectedImage(result.assets[0]);
      setStep("configure");
    }
  }, []);

  const handleGenerate = useCallback(async () => {
    if (!selectedImage || !selectedTemplate || !brandId) return;

    setLoading(true);
    setStep("generating");
    setVideoUrl(null);

    try {
      const formData = new FormData();
      formData.append("photo", {
        uri: selectedImage.uri,
        type: selectedImage.mimeType || "image/jpeg",
        name: "photo.jpg",
      } as any);

      let resultUrl: string;

      if (selectedTemplate === "breakout") {
        setProgressText("Detourage du sujet...");
        formData.append("business_name", brandName || "Mon Restaurant");
        formData.append("instagram_handle", "@" + (brandName || "restaurant").toLowerCase().replace(/\s+/g, ""));

        const res = await videoTemplatesApi.generateBreakoutV4(brandId, formData);
        resultUrl = res.data.video_url;
      } else {
        setProgressText("Generation IA en cours...");
        formData.append("food_type", foodType);
        formData.append("duration", "5");
        formData.append("aspect_ratio", "9:16");

        const res = await videoTemplatesApi.generateCinematic(brandId, formData);
        resultUrl = res.data.video_url;
      }

      setVideoUrl(resultUrl);
      setStep("preview");
    } catch (e: any) {
      const detail = e?.response?.data?.detail || e?.message || "Generation echouee";
      Alert.alert("Erreur", detail);
      setStep("configure");
    } finally {
      setLoading(false);
      setProgressText("");
    }
  }, [selectedImage, selectedTemplate, brandId, brandName, foodType]);

  const handleReset = useCallback(() => {
    setStep("select");
    setSelectedTemplate(null);
    setSelectedImage(null);
    setVideoUrl(null);
    setFoodType("default");
  }, []);

  return (
    <SafeAreaView style={s.safeArea}>
      <ScrollView style={s.container} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={s.header}>
          <Text style={s.title}>Templates Video</Text>
          <Text style={s.subtitle}>Cree des videos virales a partir d'une photo</Text>
        </View>

        {/* Template Cards */}
        {TEMPLATES.map((t) => (
          <TouchableOpacity
            key={t.id}
            style={[s.card, selectedTemplate === t.id && s.cardActive]}
            onPress={() => {
              setSelectedTemplate(t.id);
              if (!selectedImage) setStep("select");
            }}
            activeOpacity={0.7}
          >
            <View style={[s.cardIconWrap, selectedTemplate === t.id && s.cardIconWrapActive]}>
              <Ionicons name={t.icon as any} size={24} color={selectedTemplate === t.id ? Colors.brand.primary : Colors.text.secondary} />
            </View>
            <View style={s.cardContent}>
              <Text style={s.cardTitle}>{t.title}</Text>
              <Text style={s.cardSubtitle}>{t.subtitle}</Text>
              <View style={s.cardMeta}>
                <Text style={[s.cardCost, { color: t.costColor }]}>{t.cost}</Text>
                <Text style={s.cardDot}> · </Text>
                <Text style={s.cardDuration}>{t.duration}</Text>
                <Text style={s.cardDot}> · </Text>
                <Text style={s.cardDuration}>{t.time}</Text>
              </View>
            </View>
            {selectedTemplate === t.id && (
              <Ionicons name="checkmark-circle" size={24} color={Colors.brand.primary} />
            )}
          </TouchableOpacity>
        ))}

        {/* Image Picker */}
        {selectedTemplate && step !== "generating" && step !== "preview" && (
          <View style={s.section}>
            {selectedImage ? (
              <View style={s.previewWrap}>
                <Image source={{ uri: selectedImage.uri }} style={s.previewImage} />
                <View style={s.previewActions}>
                  <TouchableOpacity style={s.changeBtn} onPress={pickImage}>
                    <Ionicons name="images-outline" size={16} color={Colors.brand.primary} />
                    <Text style={s.changeBtnText}>Changer</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={s.changeBtn} onPress={takePhoto}>
                    <Ionicons name="camera-outline" size={16} color={Colors.brand.primary} />
                    <Text style={s.changeBtnText}>Camera</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              <View style={s.uploadRow}>
                <TouchableOpacity style={s.uploadBtn} onPress={pickImage}>
                  <Ionicons name="images-outline" size={28} color={Colors.brand.primary} />
                  <Text style={s.uploadBtnText}>Galerie</Text>
                </TouchableOpacity>
                <TouchableOpacity style={s.uploadBtn} onPress={takePhoto}>
                  <Ionicons name="camera-outline" size={28} color={Colors.brand.primary} />
                  <Text style={s.uploadBtnText}>Camera</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}

        {/* Food Type Selector (Cinematic only) */}
        {selectedTemplate === "cinematic" && selectedImage && step === "configure" && (
          <View style={s.section}>
            <Text style={s.sectionLabel}>Type de plat</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.chipRow}>
              {FOOD_TYPES.map((ft) => (
                <TouchableOpacity
                  key={ft.id}
                  style={[s.chip, foodType === ft.id && s.chipActive]}
                  onPress={() => setFoodType(ft.id)}
                >
                  <Text style={[s.chipText, foodType === ft.id && s.chipTextActive]}>{ft.label}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Generate Button */}
        {selectedImage && step === "configure" && (
          <TouchableOpacity
            style={s.generateBtn}
            onPress={handleGenerate}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={[Colors.brand.primary, Colors.brand.amber]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.generateBtnGradient}
            >
              <Ionicons name="sparkles" size={20} color="#FFF" />
              <Text style={s.generateBtnText}>Generer la video</Text>
            </LinearGradient>
          </TouchableOpacity>
        )}

        {/* Generating State */}
        {step === "generating" && (
          <View style={s.generatingWrap}>
            <ActivityIndicator size="large" color={Colors.brand.primary} />
            <Text style={s.generatingText}>{progressText || "Generation en cours..."}</Text>
            <Text style={s.generatingHint}>
              {selectedTemplate === "breakout" ? "~35 secondes" : "~90 secondes"}
            </Text>
          </View>
        )}

        {/* Video Preview */}
        {step === "preview" && videoUrl && (
          <View style={s.section}>
            <Text style={s.sectionLabel}>Resultat</Text>
            <View style={s.videoWrap}>
              <Video
                source={{ uri: videoUrl }}
                style={s.video}
                resizeMode={ResizeMode.CONTAIN}
                shouldPlay
                isLooping
                useNativeControls
              />
            </View>
            <View style={s.previewActionsRow}>
              <TouchableOpacity style={s.actionBtn} onPress={handleReset}>
                <Ionicons name="refresh-outline" size={18} color={Colors.brand.primary} />
                <Text style={s.actionBtnText}>Recommencer</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

        <View style={{ height: 60 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: Colors.bg.primary },
  container: { flex: 1, paddingHorizontal: 16 },
  header: { marginTop: 12, marginBottom: 20 },
  title: { fontSize: 24, fontWeight: "800", color: Colors.text.primary, marginBottom: 4 },
  subtitle: { fontSize: 14, color: Colors.text.secondary },

  // Template cards
  card: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 16,
    marginBottom: 10,
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: Colors.border.default,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  cardActive: { borderColor: Colors.brand.primary, backgroundColor: "#F5F0FF" },
  cardIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.bg.elevated,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  cardIconWrapActive: { backgroundColor: "#EDE5FF" },
  cardContent: { flex: 1 },
  cardTitle: { fontSize: 15, fontWeight: "700", color: Colors.text.primary, marginBottom: 2 },
  cardSubtitle: { fontSize: 12, color: Colors.text.secondary, marginBottom: 4 },
  cardMeta: { flexDirection: "row", alignItems: "center" },
  cardCost: { fontSize: 12, fontWeight: "700" },
  cardDot: { color: Colors.text.muted, fontSize: 12 },
  cardDuration: { fontSize: 12, color: Colors.text.muted },

  // Sections
  section: { marginTop: 16 },
  sectionLabel: { fontSize: 13, fontWeight: "600", color: Colors.text.secondary, marginBottom: 10 },

  // Image upload
  uploadRow: { flexDirection: "row", gap: 12 },
  uploadBtn: {
    flex: 1,
    backgroundColor: "#FFF",
    borderRadius: 14,
    paddingVertical: 24,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: Colors.brand.primary,
    borderStyle: "dashed",
  },
  uploadBtnText: { color: Colors.brand.primary, fontWeight: "600", fontSize: 13, marginTop: 6 },

  // Image preview
  previewWrap: { alignItems: "center" },
  previewImage: {
    width: SCREEN_W - 32,
    height: (SCREEN_W - 32) * 1.1,
    borderRadius: 14,
    backgroundColor: Colors.bg.elevated,
  },
  previewActions: { flexDirection: "row", gap: 12, marginTop: 10 },
  changeBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#F5F0FF",
  },
  changeBtnText: { fontSize: 13, fontWeight: "600", color: Colors.brand.primary },

  // Food type chips
  chipRow: { marginBottom: 8 },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#F3F2F7",
    marginRight: 8,
  },
  chipActive: { backgroundColor: Colors.brand.primary },
  chipText: { fontSize: 13, fontWeight: "600", color: Colors.text.secondary },
  chipTextActive: { color: "#FFF" },

  // Generate button
  generateBtn: { marginTop: 20, borderRadius: 14, overflow: "hidden" },
  generateBtnGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 16,
    gap: 8,
  },
  generateBtnText: { color: "#FFF", fontWeight: "800", fontSize: 16 },

  // Generating state
  generatingWrap: { alignItems: "center", marginTop: 40, paddingVertical: 30 },
  generatingText: { fontSize: 16, fontWeight: "600", color: Colors.text.primary, marginTop: 16 },
  generatingHint: { fontSize: 13, color: Colors.text.muted, marginTop: 6 },

  // Video preview
  videoWrap: {
    width: SCREEN_W - 32,
    height: (SCREEN_W - 32) * 1.6,
    borderRadius: 14,
    overflow: "hidden",
    backgroundColor: "#000",
  },
  video: { width: "100%", height: "100%" },
  previewActionsRow: { flexDirection: "row", justifyContent: "center", gap: 12, marginTop: 14 },
  actionBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: "#F5F0FF",
  },
  actionBtnText: { fontSize: 13, fontWeight: "600", color: Colors.brand.primary },
});
