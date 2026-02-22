// PresenceOS Mobile — Asset Card (dark theme)

import React from "react";
import { View, Image, Text, StyleSheet, TouchableOpacity, Dimensions } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { MediaAsset } from "@/types";

const ITEM_SIZE = (Dimensions.get("window").width - 8) / 3;

interface Props {
  asset: MediaAsset;
  onPress: () => void;
}

export default function AssetCard({ asset, onPress }: Props) {
  const url = asset.thumbnail_url || asset.public_url;

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
      <Image source={{ uri: url }} style={styles.image} resizeMode="cover" />

      {/* Video indicator */}
      {asset.media_type === "video" && (
        <View style={styles.videoIcon}>
          <Ionicons name="play" size={14} color="#FFF" />
        </View>
      )}

      {/* Improved badge */}
      {asset.improved_url && (
        <View style={styles.improvedBadge}>
          <Text style={styles.improvedText}>✨</Text>
        </View>
      )}

      {/* Quality indicator */}
      {asset.quality_score != null && asset.quality_score >= 0.8 && (
        <View style={styles.qualityBadge}>
          <Text style={styles.qualityText}>HD</Text>
        </View>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: { width: ITEM_SIZE, height: ITEM_SIZE, padding: 1 },
  image: { width: "100%", height: "100%", backgroundColor: Colors.bg.secondary, borderRadius: 4 },
  videoIcon: { position: "absolute", bottom: 6, left: 6, backgroundColor: "rgba(0,0,0,0.6)", borderRadius: 10, width: 22, height: 22, justifyContent: "center", alignItems: "center" },
  improvedBadge: { position: "absolute", top: 4, right: 4 },
  improvedText: { fontSize: 12 },
  qualityBadge: { position: "absolute", top: 4, left: 4, backgroundColor: Colors.brand.amber, borderRadius: 4, paddingHorizontal: 4, paddingVertical: 1 },
  qualityText: { fontSize: 9, fontWeight: "800", color: Colors.text.inverted },
});
