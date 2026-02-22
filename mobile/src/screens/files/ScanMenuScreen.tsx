// PresenceOS Mobile — Scan Menu Screen (dark theme, French)

import React, { useContext, useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
  FlatList,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { SafeAreaView } from "react-native-safe-area-context";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { menuApi } from "@/lib/api";

interface ScannedDish {
  name: string;
  category: string;
  price: number | null;
  description: string;
  selected: boolean;
}

export default function ScanMenuScreen() {
  const nav = useNavigation();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [step, setStep] = useState<"pick" | "scanning" | "review" | "importing">("pick");
  const [dishes, setDishes] = useState<ScannedDish[]>([]);

  const handlePick = useCallback(
    async (fromCamera: boolean) => {
      const method = fromCamera
        ? ImagePicker.launchCameraAsync
        : ImagePicker.launchImageLibraryAsync;

      const result = await method({
        mediaTypes: "images",
        quality: 0.9,
      });

      if (result.canceled || !result.assets[0] || !brandId) return;

      setStep("scanning");

      const uri = result.assets[0].uri;
      const filename = uri.split("/").pop() || "menu.jpg";
      const match = /\.(\w+)$/.exec(filename);
      const ext = match ? match[1].toLowerCase() : "jpeg";
      const mimeType = ext === "jpg" ? "image/jpeg" : `image/${ext}`;

      const formData = new FormData();
      formData.append("file", { uri, name: filename, type: mimeType } as any);

      try {
        const res = await menuApi.scan(brandId, formData);
        const scanned = (res.data.dishes || res.data || []).map((d: any) => ({
          ...d,
          selected: true,
        }));
        setDishes(scanned);
        setStep("review");
      } catch {
        Alert.alert("Erreur", "Échec de la numérisation du menu. Essayez une photo plus claire.");
        setStep("pick");
      }
    },
    [brandId]
  );

  const toggleDish = (index: number) => {
    setDishes((prev) =>
      prev.map((d, i) => (i === index ? { ...d, selected: !d.selected } : d))
    );
  };

  const updateDish = (index: number, field: keyof ScannedDish, value: any) => {
    setDishes((prev) =>
      prev.map((d, i) => (i === index ? { ...d, [field]: value } : d))
    );
  };

  const handleImport = useCallback(async () => {
    if (!brandId) return;
    const selected = dishes
      .filter((d) => d.selected)
      .map(({ selected: _, ...d }) => d);

    if (selected.length === 0) {
      Alert.alert("Aucun plat sélectionné", "Sélectionnez au moins un plat à importer.");
      return;
    }

    setStep("importing");
    try {
      await menuApi.importDishes(brandId, selected);
      Alert.alert(
        "Importé !",
        `${selected.length} plat${selected.length !== 1 ? "s" : ""} ajouté${selected.length !== 1 ? "s" : ""} à votre menu.`
      );
      nav.goBack();
    } catch {
      Alert.alert("Erreur", "Échec de l'importation");
      setStep("review");
    }
  }, [brandId, dishes, nav]);

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()}>
          <Ionicons name="close" size={24} color={Colors.text.muted} />
        </TouchableOpacity>
        <Text style={styles.title}>Scanner le menu</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Step: Pick image */}
      {step === "pick" && (
        <View style={styles.pickContainer}>
          <Ionicons name="scan-outline" size={64} color={Colors.brand.primary} />
          <Text style={styles.pickTitle}>Scannez votre menu</Text>
          <Text style={styles.pickSub}>
            Prenez une photo ou téléchargez une image de votre menu.{"\n"}
            L'IA extraira tous les plats automatiquement.
          </Text>

          <View style={styles.pickActions}>
            <TouchableOpacity
              style={styles.pickBtn}
              onPress={() => handlePick(true)}
            >
              <Ionicons name="camera" size={24} color={Colors.brand.primary} />
              <Text style={styles.pickBtnText}>Caméra</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.pickBtn}
              onPress={() => handlePick(false)}
            >
              <Ionicons name="images" size={24} color={Colors.brand.primary} />
              <Text style={styles.pickBtnText}>Galerie</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Step: Scanning */}
      {step === "scanning" && (
        <View style={styles.pickContainer}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
          <Text style={styles.scanningText}>Numérisation de votre menu...</Text>
          <Text style={styles.pickSub}>
            L'IA lit les plats, les prix et les catégories
          </Text>
        </View>
      )}

      {/* Step: Review */}
      {step === "review" && (
        <View style={styles.reviewContainer}>
          <View style={styles.reviewHeader}>
            <Text style={styles.reviewTitle}>
              {dishes.length} plat{dishes.length !== 1 ? "s" : ""} trouvé{dishes.length !== 1 ? "s" : ""}
            </Text>
            <Text style={styles.reviewSub}>
              {dishes.filter((d) => d.selected).length} sélectionné{dishes.filter((d) => d.selected).length !== 1 ? "s" : ""}
            </Text>
          </View>

          <FlatList
            data={dishes}
            keyExtractor={(_, i) => String(i)}
            renderItem={({ item, index }) => (
              <View style={[styles.dishRow, !item.selected && styles.dishRowOff]}>
                <TouchableOpacity
                  onPress={() => toggleDish(index)}
                  style={styles.checkbox}
                >
                  <Ionicons
                    name={item.selected ? "checkbox" : "square-outline"}
                    size={22}
                    color={item.selected ? Colors.brand.primary : Colors.text.muted}
                  />
                </TouchableOpacity>
                <View style={styles.dishFields}>
                  <TextInput
                    style={styles.dishName}
                    value={item.name}
                    onChangeText={(v) => updateDish(index, "name", v)}
                    placeholder="Nom du plat"
                    placeholderTextColor={Colors.text.secondary}
                  />
                  <View style={styles.dishMeta}>
                    <Text style={styles.dishCategory}>{item.category}</Text>
                    {item.price != null && (
                      <TextInput
                        style={styles.dishPrice}
                        value={String(item.price)}
                        onChangeText={(v) =>
                          updateDish(index, "price", parseFloat(v) || null)
                        }
                        keyboardType="decimal-pad"
                      />
                    )}
                  </View>
                </View>
              </View>
            )}
            contentContainerStyle={styles.reviewList}
          />

          <View style={styles.importBar}>
            <TouchableOpacity style={styles.importBtn} onPress={handleImport}>
              <Ionicons name="download-outline" size={18} color="#FFF" />
              <Text style={styles.importText}>
                Importer {dishes.filter((d) => d.selected).length} plat{dishes.filter((d) => d.selected).length !== 1 ? "s" : ""}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Step: Importing */}
      {step === "importing" && (
        <View style={styles.pickContainer}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
          <Text style={styles.scanningText}>Importation des plats...</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  title: {
    fontSize: 17,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  pickContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 40,
    gap: 12,
  },
  pickTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  pickSub: {
    fontSize: 14,
    color: Colors.text.muted,
    textAlign: "center",
    lineHeight: 20,
  },
  pickActions: {
    flexDirection: "row",
    gap: 16,
    marginTop: 24,
  },
  pickBtn: {
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    paddingVertical: 24,
    paddingHorizontal: 32,
    borderWidth: 2,
    borderColor: Colors.border.default,
    borderStyle: "dashed",
  },
  pickBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.brand.primary,
  },
  scanningText: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.text.primary,
    marginTop: 8,
  },
  reviewContainer: {
    flex: 1,
  },
  reviewHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
  },
  reviewTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  reviewSub: {
    fontSize: 13,
    color: Colors.brand.primary,
    fontWeight: "600",
  },
  reviewList: {
    paddingHorizontal: 20,
    paddingBottom: 80,
  },
  dishRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.bg.secondary,
    borderRadius: 10,
    padding: 12,
    marginBottom: 6,
  },
  dishRowOff: {
    opacity: 0.5,
  },
  checkbox: {
    marginRight: 10,
  },
  dishFields: {
    flex: 1,
  },
  dishName: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text.primary,
    paddingVertical: 2,
  },
  dishMeta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    marginTop: 2,
  },
  dishCategory: {
    fontSize: 12,
    color: Colors.text.muted,
    textTransform: "capitalize",
  },
  dishPrice: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.brand.primary,
    minWidth: 50,
  },
  importBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: Colors.bg.primary,
  },
  importBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: Colors.brand.primary,
    borderRadius: 12,
    paddingVertical: 14,
  },
  importText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "600",
  },
});
