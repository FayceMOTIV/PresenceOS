// PresenceOS Mobile — Dish Form (dark theme, French)

import React, { useContext, useState, useEffect, useCallback } from "react";
import {
  View, Text, TextInput, StyleSheet, TouchableOpacity, ScrollView, Alert, ActivityIndicator, Switch,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation, useRoute, RouteProp } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { BrandContext } from "@/contexts/BrandContext";
import { FilesStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { contentApi } from "@/lib/api";

type Route = RouteProp<FilesStackParams, "DishForm">;

const CATEGORIES = [
  { key: "entrees", label: FR.menu_category_entrees },
  { key: "plats", label: FR.menu_category_plats },
  { key: "desserts", label: FR.menu_category_desserts },
  { key: "boissons", label: FR.menu_category_boissons },
  { key: "autres", label: FR.menu_category_autres },
];

export default function DishFormScreen() {
  const nav = useNavigation();
  const route = useRoute<Route>();
  const dishId = route.params?.dishId;
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [price, setPrice] = useState("");
  const [category, setCategory] = useState("plats");
  const [isFeatured, setIsFeatured] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!dishId || !brandId) return;
    contentApi.listDishes(brandId).then((res) => {
      const list = res.data.dishes || res.data || [];
      const dish = list.find((d: any) => d.id === dishId);
      if (dish) {
        setName(dish.name);
        setDescription(dish.description || "");
        setPrice(dish.price ? String(dish.price) : "");
        setCategory(dish.category || "plats");
        setIsFeatured(dish.is_featured || false);
      }
    }).catch(() => {});
  }, [dishId, brandId]);

  const handleSave = useCallback(async () => {
    if (!brandId || !name.trim()) return;
    setSaving(true);
    try {
      const data = {
        name: name.trim(),
        description: description.trim() || undefined,
        price: price ? parseFloat(price) : undefined,
        category,
        is_featured: isFeatured,
      };
      if (dishId) {
        await contentApi.updateDish(brandId, dishId, data);
      } else {
        await contentApi.createDish(brandId, data);
      }
      nav.goBack();
    } catch {
      Alert.alert(FR.error_generic);
    } finally {
      setSaving(false);
    }
  }, [brandId, dishId, name, description, price, category, isFeatured, nav]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()}>
          <Ionicons name="close" size={24} color={Colors.text.secondary} />
        </TouchableOpacity>
        <Text style={styles.title}>{dishId ? FR.dish_title_edit : FR.dish_title_new}</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.label}>{FR.dish_name}</Text>
        <TextInput style={styles.input} value={name} onChangeText={setName} placeholder="Ex: Couscous Royal" placeholderTextColor={Colors.text.muted} />

        <Text style={styles.label}>{FR.dish_description}</Text>
        <TextInput style={[styles.input, styles.textArea]} value={description} onChangeText={setDescription} placeholder="Description optionnelle..." placeholderTextColor={Colors.text.muted} multiline textAlignVertical="top" />

        <Text style={styles.label}>{FR.dish_price}</Text>
        <TextInput style={styles.input} value={price} onChangeText={setPrice} placeholder="12.50" placeholderTextColor={Colors.text.muted} keyboardType="decimal-pad" />

        <Text style={styles.label}>{FR.dish_category}</Text>
        <View style={styles.categoryRow}>
          {CATEGORIES.map((c) => (
            <TouchableOpacity
              key={c.key}
              style={[styles.catBtn, category === c.key && styles.catBtnActive]}
              onPress={() => setCategory(c.key)}
            >
              <Text style={[styles.catText, category === c.key && styles.catTextActive]}>{c.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>{FR.dish_featured}</Text>
          <Switch
            value={isFeatured}
            onValueChange={setIsFeatured}
            trackColor={{ false: Colors.border.default, true: Colors.brand.primary }}
            thumbColor="#FFF"
          />
        </View>

        <TouchableOpacity
          style={[styles.saveBtn, (!name.trim() || saving) && styles.saveBtnDisabled]}
          onPress={handleSave}
          disabled={!name.trim() || saving}
        >
          {saving ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveBtnText}>{FR.dish_save}</Text>}
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
  label: { fontSize: 14, fontWeight: "600", color: Colors.text.secondary, marginBottom: 6, marginTop: 12 },
  input: { backgroundColor: Colors.bg.elevated, borderWidth: 1, borderColor: Colors.border.default, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 15, color: Colors.text.primary },
  textArea: { minHeight: 80, textAlignVertical: "top" },
  categoryRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 4 },
  catBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: Colors.bg.secondary, borderWidth: 1, borderColor: Colors.border.default },
  catBtnActive: { backgroundColor: Colors.brand.glow, borderColor: Colors.brand.primary },
  catText: { fontSize: 13, fontWeight: "600", color: Colors.text.secondary },
  catTextActive: { color: Colors.brand.primary },
  switchRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: 20, paddingVertical: 8 },
  switchLabel: { fontSize: 15, fontWeight: "600", color: Colors.text.primary },
  saveBtn: { backgroundColor: Colors.brand.primary, borderRadius: 14, paddingVertical: 16, alignItems: "center", marginTop: 24 },
  saveBtnDisabled: { opacity: 0.5 },
  saveBtnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
});
