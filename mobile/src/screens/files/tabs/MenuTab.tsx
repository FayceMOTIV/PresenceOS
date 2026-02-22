// PresenceOS Mobile — Menu Tab (dark theme, French)

import React, { useContext, useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  SectionList,
  StyleSheet,
  TouchableOpacity,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { BrandContext } from "@/contexts/BrandContext";
import { FilesStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { contentApi } from "@/lib/api";
import { Dish } from "@/types";
import DishCard from "@/components/DishCard";
import EmptyStateCard from "@/components/EmptyStateCard";

type Nav = NativeStackNavigationProp<FilesStackParams>;

const CATEGORY_LABELS: Record<string, string> = {
  entrees: FR.menu_category_entrees,
  plats: FR.menu_category_plats,
  desserts: FR.menu_category_desserts,
  boissons: FR.menu_category_boissons,
  autres: FR.menu_category_autres,
};

export default function MenuTab() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [dishes, setDishes] = useState<Dish[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDishes = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await contentApi.listDishes(brandId);
      setDishes(res.data.dishes || res.data || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => { fetchDishes(); }, [fetchDishes]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchDishes();
    setRefreshing(false);
  }, [fetchDishes]);

  const handleDelete = useCallback(async (dishId: string) => {
    if (!brandId) return;
    Alert.alert(FR.confirm_delete, FR.confirm_delete_body, [
      { text: FR.no_cancel, style: "cancel" },
      {
        text: FR.yes_delete,
        style: "destructive",
        onPress: async () => {
          try {
            await contentApi.deleteDish(brandId, dishId);
            setDishes((prev) => prev.filter((d) => d.id !== dishId));
          } catch {
            Alert.alert(FR.error_generic);
          }
        },
      },
    ]);
  }, [brandId]);

  const sections = Object.entries(
    dishes.reduce((acc, dish) => {
      const cat = dish.category || "autres";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(dish);
      return acc;
    }, {} as Record<string, Dish[]>)
  ).map(([key, data]) => ({
    title: CATEGORY_LABELS[key] || key,
    data,
  }));

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.brand.primary} />
      </View>
    );
  }

  if (dishes.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <EmptyStateCard
          emoji="📋"
          title={FR.menu_empty_title}
          body={FR.menu_empty_body}
          ctaLabel={FR.menu_empty_cta}
          onCta={() => nav.navigate("ScanMenu")}
          secondaryLabel={FR.menu_empty_cta2}
          onSecondary={() => nav.navigate("DishForm", {})}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <SectionList
        sections={sections}
        keyExtractor={(item) => item.id}
        renderSectionHeader={({ section: { title } }) => (
          <Text style={styles.sectionTitle}>{title}</Text>
        )}
        renderItem={({ item }) => (
          <DishCard
            dish={item}
            onPress={() => nav.navigate("DishForm", { dishId: item.id })}
            onDelete={() => handleDelete(item.id)}
          />
        )}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.brand.primary} />
        }
        contentContainerStyle={styles.list}
      />

      <View style={styles.bottomBtns}>
        <TouchableOpacity style={styles.scanBtn} onPress={() => nav.navigate("ScanMenu")}>
          <Text style={styles.scanBtnText}>{FR.menu_scan_btn}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  emptyContainer: { flex: 1, backgroundColor: Colors.bg.primary },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.bg.primary },
  sectionTitle: { fontSize: 16, fontWeight: "700", color: Colors.text.primary, paddingHorizontal: 16, paddingTop: 16, paddingBottom: 8 },
  list: { paddingBottom: 100 },
  bottomBtns: { position: "absolute", bottom: 24, left: 16, right: 16 },
  scanBtn: { backgroundColor: Colors.brand.primary, borderRadius: 14, paddingVertical: 16, alignItems: "center" },
  scanBtnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
});
