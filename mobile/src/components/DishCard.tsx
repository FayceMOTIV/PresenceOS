// PresenceOS Mobile — Dish Card (dark theme, French)

import React from "react";
import { View, Text, Image, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { Dish } from "@/types";

interface Props {
  dish: Dish;
  onPress: () => void;
  onDelete?: () => void;
}

export default function DishCard({ dish, onPress, onDelete }: Props) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      {dish.cover_asset_id && dish.cover_asset_id.startsWith("http") ? (
        <Image source={{ uri: dish.cover_asset_id }} style={styles.image} />
      ) : (
        <View style={styles.noImage}>
          <Ionicons name="restaurant-outline" size={20} color={Colors.text.muted} />
        </View>
      )}
      <View style={styles.info}>
        <View style={styles.nameRow}>
          <Text style={styles.name} numberOfLines={1}>{dish.name}</Text>
          {dish.is_featured && <Text style={styles.featured}>⭐</Text>}
        </View>
        {dish.description ? (
          <Text style={styles.description} numberOfLines={1}>{dish.description}</Text>
        ) : null}
        <Text style={styles.price}>{dish.price ? `${dish.price} €` : ""}</Text>
      </View>
      {onDelete && (
        <TouchableOpacity style={styles.deleteBtn} onPress={onDelete}>
          <Ionicons name="trash-outline" size={18} color={Colors.status.danger} />
        </TouchableOpacity>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: { flexDirection: "row", alignItems: "center", backgroundColor: Colors.bg.secondary, borderRadius: 12, padding: 12, marginHorizontal: 16, marginBottom: 8, borderWidth: 1, borderColor: Colors.border.default },
  image: { width: 52, height: 52, borderRadius: 10, backgroundColor: Colors.bg.elevated },
  noImage: { width: 52, height: 52, borderRadius: 10, backgroundColor: Colors.bg.elevated, justifyContent: "center", alignItems: "center" },
  info: { flex: 1, marginLeft: 12 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  name: { fontSize: 15, fontWeight: "600", color: Colors.text.primary, flex: 1 },
  featured: { fontSize: 14 },
  description: { fontSize: 12, color: Colors.text.secondary, marginTop: 2 },
  price: { fontSize: 13, fontWeight: "600", color: Colors.brand.amber, marginTop: 2 },
  deleteBtn: { padding: 8 },
});
