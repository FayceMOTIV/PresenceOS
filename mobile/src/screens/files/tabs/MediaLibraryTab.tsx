// PresenceOS Mobile — Media Library Tab (dark theme, French)

import React, { useContext, useState, useEffect, useCallback } from "react";
import { View, FlatList, StyleSheet, RefreshControl, ActivityIndicator } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { BrandContext } from "@/contexts/BrandContext";
import { FilesStackParams } from "@/navigation/TabNavigator";
import { assetsApi } from "@/lib/api";
import { MediaAsset } from "@/types";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import AssetCard from "@/components/AssetCard";
import AssetDetailSheet from "@/components/AssetDetailSheet";
import FAB from "@/components/FAB";
import EmptyStateCard from "@/components/EmptyStateCard";

type Nav = NativeStackNavigationProp<FilesStackParams>;

export default function MediaLibraryTab() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [assets, setAssets] = useState<MediaAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<MediaAsset | null>(null);

  const fetchAssets = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await assetsApi.list(brandId);
      setAssets(res.data.assets || res.data || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => { fetchAssets(); }, [fetchAssets]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchAssets();
    setRefreshing(false);
  }, [fetchAssets]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={Colors.brand.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {assets.length === 0 ? (
        <EmptyStateCard
          emoji="📸"
          title={FR.media_empty_title}
          body={FR.media_empty_body}
          ctaLabel={FR.media_empty_cta}
          onCta={() => nav.navigate("AssetUpload")}
        />
      ) : (
        <FlatList
          data={assets}
          keyExtractor={(item) => item.id}
          numColumns={3}
          renderItem={({ item }) => (
            <AssetCard asset={item} onPress={() => setSelectedAsset(item)} />
          )}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.brand.primary} />
          }
          contentContainerStyle={styles.grid}
        />
      )}

      <FAB icon="camera" onPress={() => nav.navigate("AssetUpload")} />

      <AssetDetailSheet
        asset={selectedAsset}
        visible={selectedAsset !== null}
        onDismiss={() => setSelectedAsset(null)}
        onImproved={fetchAssets}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.bg.primary },
  grid: { paddingBottom: 80 },
});
