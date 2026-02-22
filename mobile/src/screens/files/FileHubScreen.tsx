// PresenceOS Mobile — File Hub Screen (dark theme, French)

import React, { useContext, useState, useEffect } from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import KBCompletenessBar from "@/components/KBCompletenessBar";
import MediaLibraryTab from "./tabs/MediaLibraryTab";
import MenuTab from "./tabs/MenuTab";
import RequestsTab from "./tabs/RequestsTab";
import { kbApi } from "@/lib/api";

const TABS = [
  { key: "media", label: FR.files_tab_media },
  { key: "menu", label: FR.files_tab_menu },
  { key: "requests", label: FR.files_tab_requests },
];

export default function FileHubScreen() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;
  const [activeTab, setActiveTab] = useState("media");
  const [kbScore, setKbScore] = useState(0);

  useEffect(() => {
    if (!brandId) return;
    kbApi.completeness(brandId).then((res) => {
      setKbScore(res.data.completeness_score ?? 0);
    }).catch(() => {});
  }, [brandId]);

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <Text style={styles.title}>{FR.files_title}</Text>

      <View style={styles.kbWrap}>
        <KBCompletenessBar score={kbScore} onPress={() => setActiveTab("menu")} />
      </View>

      {/* Tab bar */}
      <View style={styles.tabBar}>
        {TABS.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === tab.key && styles.tabActive]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === tab.key && styles.tabTextActive,
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <View style={styles.content}>
        {activeTab === "media" && <MediaLibraryTab />}
        {activeTab === "menu" && <MenuTab />}
        {activeTab === "requests" && <RequestsTab />}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary, paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12 },
  kbWrap: { paddingHorizontal: 16 },
  tabBar: { flexDirection: "row", paddingHorizontal: 16, gap: 8, marginBottom: 4 },
  tab: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, backgroundColor: Colors.bg.elevated },
  tabActive: { backgroundColor: Colors.brand.primary },
  tabText: { fontSize: 13, fontWeight: "600", color: Colors.text.secondary },
  tabTextActive: { color: "#FFF" },
  content: { flex: 1 },
});
