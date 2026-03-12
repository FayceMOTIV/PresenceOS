// PresenceOS Mobile — Video Templates Screen
// 5 templates: Breakout V4, Cinematic Food, Promo Flash, Restaurant Showcase, Daily Story

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
  TextInput,
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

type TemplateId = "breakout" | "cinematic" | "promo" | "showcase" | "story";
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
  photos: number;
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
    photos: 1,
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
    photos: 1,
  },
  {
    id: "promo",
    icon: "megaphone-outline",
    title: "Promo Flash",
    subtitle: "Video promo animee avec texte",
    cost: "Gratuit",
    costColor: Colors.status.success,
    duration: "8s",
    time: "~40s",
    photos: 1,
  },
  {
    id: "showcase",
    icon: "restaurant-outline",
    title: "Showcase Plats",
    subtitle: "Presentez 3 plats en video",
    cost: "Gratuit",
    costColor: Colors.status.success,
    duration: "8s",
    time: "~50s",
    photos: 3,
  },
  {
    id: "story",
    icon: "phone-portrait-outline",
    title: "Story Instagram",
    subtitle: "Story animee avec 3 slides",
    cost: "Gratuit",
    costColor: Colors.status.success,
    duration: "7s",
    time: "~50s",
    photos: 3,
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
  const [multiImages, setMultiImages] = useState<(ImagePicker.ImagePickerAsset | null)[]>([null, null, null]);
  const [foodType, setFoodType] = useState<FoodType>("default");
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<Step>("select");
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progressText, setProgressText] = useState("");

  // Promo Flash fields
  const [promoHeadline, setPromoHeadline] = useState("OFFRE SPECIALE");
  const [promoDiscount, setPromoDiscount] = useState("-20%");
  const [promoCode, setPromoCode] = useState("");
  const [promoCta, setPromoCta] = useState("Reservez maintenant!");

  // Showcase fields
  const [dishNames, setDishNames] = useState(["", "", ""]);
  const [dishDescs, setDishDescs] = useState(["", "", ""]);
  const [showcaseTagline, setShowcaseTagline] = useState("Nos specialites");

  // Story fields
  const [storyTexts, setStoryTexts] = useState([
    "Decouvrez notre carte!",
    "Prepare avec amour",
    "Reservez votre table!",
  ]);

  const templateConfig = TEMPLATES.find((t) => t.id === selectedTemplate);
  const needsMultiPhotos = templateConfig && templateConfig.photos > 1;

  const pickImage = useCallback(async (index?: number) => {
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
      if (index !== undefined) {
        setMultiImages((prev) => {
          const next = [...prev];
          next[index] = result.assets[0];
          return next;
        });
      } else {
        setSelectedImage(result.assets[0]);
      }
      setStep("configure");
    }
  }, []);

  const takePhoto = useCallback(async (index?: number) => {
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
      if (index !== undefined) {
        setMultiImages((prev) => {
          const next = [...prev];
          next[index] = result.assets[0];
          return next;
        });
      } else {
        setSelectedImage(result.assets[0]);
      }
      setStep("configure");
    }
  }, []);

  const canGenerate = useCallback(() => {
    if (!selectedTemplate || !brandId) return false;
    if (needsMultiPhotos) {
      return multiImages.every((img) => img !== null);
    }
    return selectedImage !== null;
  }, [selectedTemplate, brandId, needsMultiPhotos, multiImages, selectedImage]);

  const handleGenerate = useCallback(async () => {
    if (!canGenerate()) return;

    setLoading(true);
    setStep("generating");
    setVideoUrl(null);

    try {
      let resultUrl: string;

      if (selectedTemplate === "breakout") {
        setProgressText("Detourage du sujet...");
        const formData = new FormData();
        formData.append("photo", {
          uri: selectedImage!.uri,
          type: selectedImage!.mimeType || "image/jpeg",
          name: "photo.jpg",
        } as any);
        formData.append("business_name", brandName || "Mon Restaurant");
        formData.append("instagram_handle", "@" + (brandName || "restaurant").toLowerCase().replace(/\s+/g, ""));
        const res = await videoTemplatesApi.generateBreakoutV4(brandId!, formData);
        resultUrl = res.data.video_url;

      } else if (selectedTemplate === "cinematic") {
        setProgressText("Generation IA en cours...");
        const formData = new FormData();
        formData.append("photo", {
          uri: selectedImage!.uri,
          type: selectedImage!.mimeType || "image/jpeg",
          name: "photo.jpg",
        } as any);
        formData.append("food_type", foodType);
        formData.append("duration", "5");
        formData.append("aspect_ratio", "9:16");
        const res = await videoTemplatesApi.generateCinematic(brandId!, formData);
        resultUrl = res.data.video_url;

      } else if (selectedTemplate === "promo") {
        setProgressText("Creation de la promo...");
        const formData = new FormData();
        formData.append("photo", {
          uri: selectedImage!.uri,
          type: selectedImage!.mimeType || "image/jpeg",
          name: "photo.jpg",
        } as any);
        formData.append("headline", promoHeadline);
        formData.append("discount", promoDiscount);
        formData.append("promo_code", promoCode);
        formData.append("cta_text", promoCta);
        formData.append("brand_name", brandName || "");
        const res = await videoTemplatesApi.generatePromoFlash(brandId!, formData);
        resultUrl = res.data.video_url;

      } else if (selectedTemplate === "showcase") {
        setProgressText("Creation du showcase...");
        const formData = new FormData();
        multiImages.forEach((img, i) => {
          formData.append(`photo${i + 1}`, {
            uri: img!.uri,
            type: img!.mimeType || "image/jpeg",
            name: `photo${i + 1}.jpg`,
          } as any);
        });
        formData.append("dish_name_1", dishNames[0] || "Specialite 1");
        formData.append("dish_name_2", dishNames[1] || "Specialite 2");
        formData.append("dish_name_3", dishNames[2] || "Specialite 3");
        formData.append("dish_desc_1", dishDescs[0]);
        formData.append("dish_desc_2", dishDescs[1]);
        formData.append("dish_desc_3", dishDescs[2]);
        formData.append("brand_name", brandName || "Mon Restaurant");
        formData.append("tagline", showcaseTagline);
        const res = await videoTemplatesApi.generateShowcase(brandId!, formData);
        resultUrl = res.data.video_url;

      } else {
        // story
        setProgressText("Creation de la story...");
        const formData = new FormData();
        multiImages.forEach((img, i) => {
          formData.append(`photo${i + 1}`, {
            uri: img!.uri,
            type: img!.mimeType || "image/jpeg",
            name: `photo${i + 1}.jpg`,
          } as any);
        });
        formData.append("text_1", storyTexts[0]);
        formData.append("text_2", storyTexts[1]);
        formData.append("text_3", storyTexts[2]);
        formData.append("brand_name", brandName || "Mon Restaurant");
        const res = await videoTemplatesApi.generateStory(brandId!, formData);
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
  }, [
    selectedTemplate, selectedImage, multiImages, brandId, brandName,
    foodType, promoHeadline, promoDiscount, promoCode, promoCta,
    dishNames, dishDescs, showcaseTagline, storyTexts, canGenerate,
  ]);

  const handleReset = useCallback(() => {
    setStep("select");
    setSelectedTemplate(null);
    setSelectedImage(null);
    setMultiImages([null, null, null]);
    setVideoUrl(null);
    setFoodType("default");
    setPromoHeadline("OFFRE SPECIALE");
    setPromoDiscount("-20%");
    setPromoCode("");
    setPromoCta("Reservez maintenant!");
    setDishNames(["", "", ""]);
    setDishDescs(["", "", ""]);
    setShowcaseTagline("Nos specialites");
    setStoryTexts(["Decouvrez notre carte!", "Prepare avec amour", "Reservez votre table!"]);
  }, []);

  const updateDishName = (index: number, value: string) => {
    setDishNames((prev) => { const next = [...prev]; next[index] = value; return next; });
  };
  const updateDishDesc = (index: number, value: string) => {
    setDishDescs((prev) => { const next = [...prev]; next[index] = value; return next; });
  };
  const updateStoryText = (index: number, value: string) => {
    setStoryTexts((prev) => { const next = [...prev]; next[index] = value; return next; });
  };

  // ── Render ──────────────────────────────────────────────

  const renderSinglePhotoPicker = () => (
    <View style={s.section}>
      {selectedImage ? (
        <View style={s.previewWrap}>
          <Image source={{ uri: selectedImage.uri }} style={s.previewImage} />
          <View style={s.previewActions}>
            <TouchableOpacity style={s.changeBtn} onPress={() => pickImage()}>
              <Ionicons name="images-outline" size={16} color={Colors.brand.primary} />
              <Text style={s.changeBtnText}>Changer</Text>
            </TouchableOpacity>
            <TouchableOpacity style={s.changeBtn} onPress={() => takePhoto()}>
              <Ionicons name="camera-outline" size={16} color={Colors.brand.primary} />
              <Text style={s.changeBtnText}>Camera</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <View style={s.uploadRow}>
          <TouchableOpacity style={s.uploadBtn} onPress={() => pickImage()}>
            <Ionicons name="images-outline" size={28} color={Colors.brand.primary} />
            <Text style={s.uploadBtnText}>Galerie</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.uploadBtn} onPress={() => takePhoto()}>
            <Ionicons name="camera-outline" size={28} color={Colors.brand.primary} />
            <Text style={s.uploadBtnText}>Camera</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );

  const renderMultiPhotoPicker = () => (
    <View style={s.section}>
      <Text style={s.sectionLabel}>3 photos requises</Text>
      <View style={s.multiPhotoRow}>
        {[0, 1, 2].map((i) => (
          <TouchableOpacity
            key={i}
            style={s.multiPhotoSlot}
            onPress={() => pickImage(i)}
            activeOpacity={0.7}
          >
            {multiImages[i] ? (
              <Image source={{ uri: multiImages[i]!.uri }} style={s.multiPhotoImg} />
            ) : (
              <View style={s.multiPhotoEmpty}>
                <Ionicons name="add-circle-outline" size={28} color={Colors.brand.primary} />
                <Text style={s.multiPhotoLabel}>Photo {i + 1}</Text>
              </View>
            )}
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );

  const renderPromoForm = () => (
    <View style={s.section}>
      <Text style={s.sectionLabel}>Personnaliser la promo</Text>
      <TextInput
        style={s.textInput}
        value={promoHeadline}
        onChangeText={setPromoHeadline}
        placeholder="Titre (ex: OFFRE SPECIALE)"
        placeholderTextColor={Colors.text.muted}
        maxLength={40}
      />
      <TextInput
        style={s.textInput}
        value={promoDiscount}
        onChangeText={setPromoDiscount}
        placeholder="Reduction (ex: -20%)"
        placeholderTextColor={Colors.text.muted}
        maxLength={20}
      />
      <TextInput
        style={s.textInput}
        value={promoCode}
        onChangeText={setPromoCode}
        placeholder="Code promo (optionnel)"
        placeholderTextColor={Colors.text.muted}
        maxLength={20}
      />
      <TextInput
        style={s.textInput}
        value={promoCta}
        onChangeText={setPromoCta}
        placeholder="Bouton (ex: Reservez!)"
        placeholderTextColor={Colors.text.muted}
        maxLength={30}
      />
    </View>
  );

  const renderShowcaseForm = () => (
    <View style={s.section}>
      <Text style={s.sectionLabel}>Noms des plats</Text>
      <TextInput
        style={s.textInput}
        value={showcaseTagline}
        onChangeText={setShowcaseTagline}
        placeholder="Slogan (ex: Nos specialites)"
        placeholderTextColor={Colors.text.muted}
        maxLength={50}
      />
      {[0, 1, 2].map((i) => (
        <View key={i}>
          <TextInput
            style={s.textInput}
            value={dishNames[i]}
            onChangeText={(v) => updateDishName(i, v)}
            placeholder={`Nom du plat ${i + 1}`}
            placeholderTextColor={Colors.text.muted}
            maxLength={40}
          />
          <TextInput
            style={[s.textInput, { marginTop: -4 }]}
            value={dishDescs[i]}
            onChangeText={(v) => updateDishDesc(i, v)}
            placeholder={`Description ${i + 1} (optionnel)`}
            placeholderTextColor={Colors.text.muted}
            maxLength={60}
          />
        </View>
      ))}
    </View>
  );

  const renderStoryForm = () => (
    <View style={s.section}>
      <Text style={s.sectionLabel}>Textes des slides</Text>
      {[0, 1, 2].map((i) => (
        <TextInput
          key={i}
          style={s.textInput}
          value={storyTexts[i]}
          onChangeText={(v) => updateStoryText(i, v)}
          placeholder={`Texte slide ${i + 1}`}
          placeholderTextColor={Colors.text.muted}
          maxLength={80}
        />
      ))}
    </View>
  );

  return (
    <SafeAreaView style={s.safeArea}>
      <ScrollView style={s.container} showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
        {/* Header */}
        <View style={s.header}>
          <Text style={s.title}>Templates Video</Text>
          <Text style={s.subtitle}>Cree des videos virales a partir de photos</Text>
        </View>

        {/* Template Cards */}
        {step !== "generating" && step !== "preview" && TEMPLATES.map((t) => (
          <TouchableOpacity
            key={t.id}
            style={[s.card, selectedTemplate === t.id && s.cardActive]}
            onPress={() => {
              setSelectedTemplate(t.id);
              setSelectedImage(null);
              setMultiImages([null, null, null]);
              setStep("select");
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
                {t.photos > 1 && (
                  <>
                    <Text style={s.cardDot}> · </Text>
                    <Text style={s.cardDuration}>{t.photos} photos</Text>
                  </>
                )}
              </View>
            </View>
            {selectedTemplate === t.id && (
              <Ionicons name="checkmark-circle" size={24} color={Colors.brand.primary} />
            )}
          </TouchableOpacity>
        ))}

        {/* Photo Picker */}
        {selectedTemplate && step !== "generating" && step !== "preview" && (
          needsMultiPhotos ? renderMultiPhotoPicker() : renderSinglePhotoPicker()
        )}

        {/* Template-specific forms */}
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

        {selectedTemplate === "promo" && selectedImage && step === "configure" && renderPromoForm()}
        {selectedTemplate === "showcase" && step === "configure" && renderShowcaseForm()}
        {selectedTemplate === "story" && step === "configure" && renderStoryForm()}

        {/* Generate Button */}
        {step === "configure" && canGenerate() && (
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
              {templateConfig ? `~${templateConfig.time.replace("~", "")}` : "Patience..."}
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

  // Single image upload
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

  // Multi-photo picker
  multiPhotoRow: { flexDirection: "row", gap: 8 },
  multiPhotoSlot: {
    flex: 1,
    aspectRatio: 0.75,
    borderRadius: 12,
    overflow: "hidden",
    borderWidth: 1.5,
    borderColor: Colors.brand.primary,
    borderStyle: "dashed",
    backgroundColor: "#FFF",
  },
  multiPhotoImg: { width: "100%", height: "100%", borderRadius: 10 },
  multiPhotoEmpty: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  multiPhotoLabel: { fontSize: 11, fontWeight: "600", color: Colors.brand.primary },

  // Text inputs
  textInput: {
    backgroundColor: "#FFF",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 14,
    color: Colors.text.primary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    marginBottom: 8,
  },

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
