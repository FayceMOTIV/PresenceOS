// PresenceOS Mobile — Asset Upload Screen (dark theme, French)

import React, { useContext, useState, useCallback, useEffect } from "react";
import {
  View, Text, StyleSheet, TouchableOpacity, Image, TextInput, Alert, ActivityIndicator, ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { assetsApi, contentApi, dishApi } from "@/lib/api";
import { Dish } from "@/types";

export default function AssetUploadScreen() {
  const nav = useNavigation();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [imageUri, setImageUri] = useState<string | null>(null);
  const [label, setLabel] = useState("");
  const [linkedDishId, setLinkedDishId] = useState<string | null>(null);
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [uploading, setUploading] = useState(false);
  const [recognizing, setRecognizing] = useState(false);
  const [recognizedDish, setRecognizedDish] = useState<string | null>(null);

  useEffect(() => {
    if (!brandId) return;
    contentApi.listDishes(brandId).then((res) => {
      setDishes(res.data.dishes || res.data || []);
    }).catch((err) => {
      if (__DEV__) console.warn("Failed to load dishes:", err);
    });
  }, [brandId]);

  const recognizeDish = useCallback(async (uri: string) => {
    setRecognizing(true);
    try {
      const formData = new FormData();
      const filename = uri.split("/").pop() || "photo.jpg";
      formData.append("photo", { uri, name: filename, type: "image/jpeg" } as any);
      const res = await dishApi.recognize(formData);
      const data = res.data;
      if (data?.dish_name && data.dish_name !== "inconnu" && data.confidence > 0.5) {
        setRecognizedDish(data.dish_name);
        if (!label) setLabel(data.dish_name);
        // Auto-select matching dish if found
        const match = dishes.find(
          (d) => d.name.toLowerCase() === data.dish_name.toLowerCase()
        );
        if (match && !linkedDishId) setLinkedDishId(match.id);
      }
    } catch {
      // Silent fail — recognition is optional
    } finally {
      setRecognizing(false);
    }
  }, [dishes, label, linkedDishId]);

  const onImageSelected = useCallback((uri: string) => {
    setImageUri(uri);
    recognizeDish(uri);
  }, [recognizeDish]);

  const pickImage = useCallback(async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ["images", "videos"],
      quality: 0.8,
    });
    if (!result.canceled && result.assets[0]) {
      onImageSelected(result.assets[0].uri);
    }
  }, [onImageSelected]);

  const takePhoto = useCallback(async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission requise", "Autorisez l'accès à la caméra dans les réglages");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.8 });
    if (!result.canceled && result.assets[0]) {
      onImageSelected(result.assets[0].uri);
    }
  }, [onImageSelected]);

  const handleUpload = useCallback(async () => {
    if (!brandId || !imageUri) return;
    setUploading(true);
    try {
      const formData = new FormData();
      const filename = imageUri.split("/").pop() || "photo.jpg";
      const ext = filename.split(".").pop()?.toLowerCase() || "jpeg";
      const mimeType = ext === "jpg" ? "image/jpeg" : `image/${ext}`;
      formData.append("file", { uri: imageUri, name: filename, type: mimeType } as any);
      if (label) formData.append("label", label);
      if (linkedDishId) formData.append("linked_dish_id", linkedDishId);
      await assetsApi.upload(brandId, formData);
      Alert.alert("✅", "Média uploadé avec succès !");
      nav.goBack();
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || FR.error_generic;
      Alert.alert("Erreur upload", detail);
    } finally {
      setUploading(false);
    }
  }, [brandId, imageUri, label, linkedDishId, nav]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()}>
          <Ionicons name="close" size={24} color={Colors.text.secondary} />
        </TouchableOpacity>
        <Text style={styles.title}>{FR.upload_title}</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        {imageUri ? (
          <TouchableOpacity onPress={pickImage}>
            <Image source={{ uri: imageUri }} style={styles.preview} resizeMode="cover" />
          </TouchableOpacity>
        ) : (
          <View style={styles.pickerRow}>
            <TouchableOpacity style={styles.pickerBtn} onPress={pickImage}>
              <Ionicons name="images-outline" size={28} color={Colors.brand.primary} />
              <Text style={styles.pickerText}>{FR.upload_pick_photo}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.pickerBtn} onPress={takePhoto}>
              <Ionicons name="camera-outline" size={28} color={Colors.brand.primary} />
              <Text style={styles.pickerText}>{FR.upload_take_photo}</Text>
            </TouchableOpacity>
          </View>
        )}

        {recognizing && (
          <View style={styles.recognizingRow}>
            <ActivityIndicator size="small" color={Colors.brand.amber} />
            <Text style={styles.recognizingText}>Identification du plat...</Text>
          </View>
        )}
        {recognizedDish && !recognizing && (
          <View style={styles.recognizedRow}>
            <Ionicons name="sparkles" size={16} color={Colors.brand.amber} />
            <Text style={styles.recognizedText}>Plat detecte : {recognizedDish}</Text>
          </View>
        )}

        <TextInput
          style={styles.input}
          placeholder={FR.upload_label_placeholder}
          placeholderTextColor={Colors.text.muted}
          value={label}
          onChangeText={setLabel}
        />

        {dishes.length > 0 && (
          <>
            <Text style={styles.sectionLabel}>{FR.upload_link_dish}</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.dishScroll}>
              {dishes.map((d) => (
                <TouchableOpacity
                  key={d.id}
                  style={[styles.dishChip, linkedDishId === d.id && styles.dishChipActive]}
                  onPress={() => setLinkedDishId(linkedDishId === d.id ? null : d.id)}
                >
                  <Text style={[styles.dishChipText, linkedDishId === d.id && styles.dishChipTextActive]}>
                    {d.name}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </>
        )}

        <TouchableOpacity
          style={[styles.uploadBtn, (!imageUri || uploading) && styles.uploadBtnDisabled]}
          onPress={handleUpload}
          disabled={!imageUri || uploading}
        >
          {uploading ? <ActivityIndicator color="#FFF" /> : <Text style={styles.uploadBtnText}>{FR.upload_submit}</Text>}
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 16, paddingVertical: 12 },
  title: { fontSize: 18, fontWeight: "700", color: Colors.text.primary },
  scroll: { padding: 20, paddingBottom: 40 },
  preview: { width: "100%", aspectRatio: 1, borderRadius: 16, backgroundColor: Colors.bg.secondary, marginBottom: 20 },
  pickerRow: { flexDirection: "row", gap: 12, marginBottom: 20 },
  pickerBtn: { flex: 1, backgroundColor: Colors.bg.secondary, borderRadius: 16, paddingVertical: 32, alignItems: "center", gap: 8, borderWidth: 1, borderColor: Colors.border.default },
  pickerText: { fontSize: 13, color: Colors.text.secondary, fontWeight: "500" },
  input: { backgroundColor: Colors.bg.elevated, borderWidth: 1, borderColor: Colors.border.default, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 15, color: Colors.text.primary, marginBottom: 16 },
  sectionLabel: { fontSize: 14, fontWeight: "600", color: Colors.text.secondary, marginBottom: 8 },
  dishScroll: { marginBottom: 20 },
  dishChip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: Colors.bg.secondary, marginRight: 8, borderWidth: 1, borderColor: Colors.border.default },
  dishChipActive: { backgroundColor: Colors.brand.glow, borderColor: Colors.brand.primary },
  dishChipText: { fontSize: 13, color: Colors.text.secondary, fontWeight: "500" },
  dishChipTextActive: { color: Colors.brand.primary },
  uploadBtn: { backgroundColor: Colors.brand.primary, borderRadius: 14, paddingVertical: 16, alignItems: "center", marginTop: 8 },
  uploadBtnDisabled: { opacity: 0.5 },
  uploadBtnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
  recognizingRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 12 },
  recognizingText: { color: Colors.text.muted, fontSize: 13 },
  recognizedRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 12, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: Colors.brand.glow, borderRadius: 10 },
  recognizedText: { color: Colors.brand.amber, fontSize: 13, fontWeight: "600" },
});
