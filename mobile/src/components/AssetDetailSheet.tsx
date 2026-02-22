// PresenceOS Mobile — Asset Detail Sheet (dark theme, French)

import React, { useCallback, useState, useContext } from "react";
import {
  View, Text, Image, StyleSheet, TouchableOpacity, Dimensions, Alert, ActivityIndicator, Modal, ScrollView, SafeAreaView,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { MediaAsset } from "@/types";
import { assetsApi } from "@/lib/api";
import { BrandContext } from "@/contexts/BrandContext";

interface Props {
  asset: MediaAsset | null;
  visible: boolean;
  onDismiss: () => void;
  onImproved?: () => void;
}

const { width: SCREEN_WIDTH } = Dimensions.get("window");

export default function AssetDetailSheet({ asset, visible, onDismiss, onImproved }: Props) {
  const brand = useContext(BrandContext);
  const [showImproved, setShowImproved] = useState(false);
  const [improving, setImproving] = useState(false);

  const handleImprove = useCallback(async () => {
    if (!asset || !brand?.activeBrand) return;
    setImproving(true);
    try {
      await assetsApi.improve(brand.activeBrand.id, asset.id);
      Alert.alert("✨", FR.media_improving);
      onImproved?.();
    } catch {
      Alert.alert(FR.error_generic);
    } finally {
      setImproving(false);
    }
  }, [asset, brand, onImproved]);

  const handleGeneratePost = useCallback(async () => {
    if (!asset || !brand?.activeBrand) return;
    try {
      await assetsApi.generatePost(brand.activeBrand.id, asset.id);
      Alert.alert("✨", "Proposition en cours de génération...");
    } catch {
      Alert.alert(FR.error_generic);
    }
  }, [asset, brand]);

  if (!asset) return null;

  const displayUrl = showImproved && asset.improved_url ? asset.improved_url : asset.public_url;

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onDismiss}>
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <View style={styles.indicator} />
          <TouchableOpacity style={styles.closeBtn} onPress={onDismiss}>
            <Ionicons name="close" size={24} color={Colors.text.secondary} />
          </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <Image source={{ uri: displayUrl }} style={styles.image} resizeMode="cover" />

          {asset.improved_url && (
            <View style={styles.toggleRow}>
              <TouchableOpacity style={[styles.toggleBtn, !showImproved && styles.toggleActive]} onPress={() => setShowImproved(false)}>
                <Text style={[styles.toggleText, !showImproved && styles.toggleTextActive]}>{FR.asset_original}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.toggleBtn, showImproved && styles.toggleActive]} onPress={() => setShowImproved(true)}>
                <Text style={[styles.toggleText, showImproved && styles.toggleTextActive]}>{FR.asset_improved}</Text>
              </TouchableOpacity>
            </View>
          )}

          <View style={styles.infoSection}>
            {asset.asset_label && <Text style={styles.label}>{asset.asset_label}</Text>}
            {asset.ai_description && <Text style={styles.description}>{asset.ai_description}</Text>}

            <View style={styles.metaRow}>
              <Text style={styles.metaItem}>{asset.media_type === "video" ? "Vidéo" : "Photo"}</Text>
              {asset.quality_score != null && (
                <Text style={styles.metaItem}>{FR.asset_quality} : {Math.round(asset.quality_score * 100)}%</Text>
              )}
              <Text style={styles.metaItem}>
                {FR.asset_used_in} {asset.used_in_posts} {asset.used_in_posts !== 1 ? FR.asset_posts_plural : FR.asset_posts}
              </Text>
            </View>
          </View>

          <View style={styles.actions}>
            {!asset.improved_url && asset.media_type === "image" && (
              <TouchableOpacity style={styles.actionBtn} onPress={handleImprove} disabled={improving}>
                {improving ? <ActivityIndicator size="small" color={Colors.brand.primary} /> : <Ionicons name="sparkles" size={18} color={Colors.brand.primary} />}
                <Text style={styles.actionText}>{FR.asset_enhance}</Text>
              </TouchableOpacity>
            )}
            <TouchableOpacity style={styles.actionBtn} onPress={handleGeneratePost}>
              <Ionicons name="create-outline" size={18} color={Colors.brand.primary} />
              <Text style={styles.actionText}>{FR.asset_generate_post}</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: { alignItems: "center", paddingTop: 8, paddingBottom: 4, position: "relative" },
  indicator: { width: 40, height: 4, borderRadius: 2, backgroundColor: Colors.border.strong },
  closeBtn: { position: "absolute", right: 16, top: 8, padding: 4 },
  content: { paddingBottom: 40 },
  image: { width: SCREEN_WIDTH, height: SCREEN_WIDTH, backgroundColor: Colors.bg.secondary },
  toggleRow: { flexDirection: "row", justifyContent: "center", paddingVertical: 12, gap: 8 },
  toggleBtn: { paddingHorizontal: 16, paddingVertical: 6, borderRadius: 16, backgroundColor: Colors.bg.secondary },
  toggleActive: { backgroundColor: Colors.brand.glow },
  toggleText: { fontSize: 13, fontWeight: "500", color: Colors.text.secondary },
  toggleTextActive: { color: Colors.brand.primary },
  infoSection: { paddingHorizontal: 20, paddingTop: 8 },
  label: { fontSize: 18, fontWeight: "700", color: Colors.text.primary, marginBottom: 4 },
  description: { fontSize: 14, color: Colors.text.secondary, lineHeight: 20, marginBottom: 8 },
  metaRow: { flexDirection: "row", gap: 16, paddingVertical: 8 },
  metaItem: { fontSize: 12, color: Colors.text.muted },
  actions: { paddingHorizontal: 20, paddingTop: 16, gap: 10 },
  actionBtn: { flexDirection: "row", alignItems: "center", gap: 10, backgroundColor: Colors.bg.secondary, borderRadius: 10, paddingVertical: 14, paddingHorizontal: 16, borderWidth: 1, borderColor: Colors.border.default },
  actionText: { fontSize: 14, fontWeight: "600", color: Colors.brand.primary },
});
