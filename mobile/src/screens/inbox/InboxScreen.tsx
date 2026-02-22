// PresenceOS Mobile — Inbox Screen (dark theme, French)

import React, { useContext, useState, useEffect, useCallback } from "react";
import {
  View, Text, FlatList, StyleSheet, TouchableOpacity, RefreshControl, ActivityIndicator, Alert,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { cmApi } from "@/lib/api";
import EmptyStateCard from "@/components/EmptyStateCard";

interface Interaction {
  id: string;
  platform: string;
  commenter_name: string;
  content: string;
  ai_response_draft: string | null;
  response_status: string;
  created_at: string;
}

export default function InboxScreen() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const fetchInteractions = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await cmApi.listInteractions(brandId);
      setInteractions(res.data.interactions || res.data || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => { fetchInteractions(); }, [fetchInteractions]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchInteractions();
    setRefreshing(false);
  }, [fetchInteractions]);

  const handleApprove = async (id: string) => {
    try {
      await cmApi.approve(id);
      setInteractions((prev) => prev.map((i) => i.id === id ? { ...i, response_status: "approved" } : i));
    } catch { Alert.alert(FR.error_generic); }
  };

  const handleReject = async (id: string) => {
    try {
      await cmApi.reject(id);
      setInteractions((prev) => prev.map((i) => i.id === id ? { ...i, response_status: "rejected" } : i));
    } catch { Alert.alert(FR.error_generic); }
  };

  const pendingCount = interactions.filter((i) => i.response_status === "pending").length;
  const repliedCount = interactions.filter((i) => ["approved", "edited", "auto_published"].includes(i.response_status)).length;

  const renderItem = ({ item }: { item: Interaction }) => {
    const expanded = expandedId === item.id;
    const statusColor = item.response_status === "pending" ? Colors.status.warning : ["approved", "edited", "auto_published"].includes(item.response_status) ? Colors.status.success : Colors.text.muted;

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => setExpandedId(expanded ? null : item.id)}
        activeOpacity={0.8}
      >
        <View style={styles.cardHeader}>
          <View style={styles.cardLeft}>
            <Text style={styles.customerName}>{item.commenter_name}</Text>
            <Text style={styles.platform}>{item.platform}</Text>
          </View>
          <View style={[styles.dot, { backgroundColor: statusColor }]} />
        </View>
        <Text style={styles.message} numberOfLines={expanded ? undefined : 2}>{item.content}</Text>

        {expanded && (
          <View style={styles.expandedSection}>
            <Text style={styles.aiLabel}>{FR.inbox_auto_reply}</Text>
            <Text style={styles.aiResponse}>{item.ai_response_draft || "—"}</Text>

            {item.response_status === "pending" && (
              <View style={styles.actionRow}>
                <TouchableOpacity style={styles.approveBtn} onPress={() => handleApprove(item.id)}>
                  <Text style={styles.approveBtnText}>{FR.inbox_approve_reply}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.rejectBtn} onPress={() => handleReject(item.id)}>
                  <Text style={styles.rejectBtnText}>{FR.inbox_ignore}</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <Text style={styles.title}>{FR.inbox_title}</Text>

      {/* Stats row */}
      {interactions.length > 0 && (
        <View style={styles.statsRow}>
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: Colors.status.warning }]}>{pendingCount}</Text>
            <Text style={styles.statLabel}>{FR.inbox_stats_pending}</Text>
          </View>
          <View style={styles.stat}>
            <Text style={[styles.statValue, { color: Colors.status.success }]}>{repliedCount}</Text>
            <Text style={styles.statLabel}>{FR.inbox_stats_replied}</Text>
          </View>
        </View>
      )}

      {loading ? (
        <View style={styles.center}><ActivityIndicator size="large" color={Colors.brand.primary} /></View>
      ) : interactions.length === 0 ? (
        <LinearGradient colors={["#1A2A4A", "#0F1923"]} style={styles.emptyGradient}>
          <EmptyStateCard
            emoji="⭐"
            title={FR.inbox_empty_title}
            body={FR.inbox_empty_body}
            ctaLabel={FR.inbox_empty_cta}
          />
        </LinearGradient>
      ) : (
        <FlatList
          data={interactions}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.brand.primary} />
          }
          contentContainerStyle={styles.list}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary, paddingHorizontal: 20, paddingTop: 8, paddingBottom: 12 },
  statsRow: { flexDirection: "row", gap: 12, paddingHorizontal: 16, marginBottom: 16 },
  stat: { flex: 1, backgroundColor: Colors.bg.secondary, borderRadius: 14, padding: 16, alignItems: "center", borderWidth: 1, borderColor: Colors.border.default },
  statValue: { fontSize: 24, fontWeight: "800", marginBottom: 2 },
  statLabel: { fontSize: 11, color: Colors.text.secondary, fontWeight: "500" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyGradient: { flex: 1, justifyContent: "center" },
  list: { paddingHorizontal: 16, paddingBottom: 80, gap: 12 },
  card: { backgroundColor: Colors.bg.secondary, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: Colors.border.default },
  cardHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  cardLeft: { flexDirection: "row", alignItems: "center", gap: 8 },
  customerName: { fontSize: 15, fontWeight: "600", color: Colors.text.primary },
  platform: { fontSize: 12, color: Colors.text.muted },
  dot: { width: 8, height: 8, borderRadius: 4 },
  message: { fontSize: 14, color: Colors.text.secondary, lineHeight: 20 },
  expandedSection: { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: Colors.border.default },
  aiLabel: { fontSize: 12, fontWeight: "600", color: Colors.brand.primary, marginBottom: 4 },
  aiResponse: { fontSize: 14, color: Colors.text.primary, lineHeight: 20, marginBottom: 12 },
  actionRow: { flexDirection: "row", gap: 8 },
  approveBtn: { flex: 1, backgroundColor: Colors.brand.primary, borderRadius: 10, paddingVertical: 12, alignItems: "center" },
  approveBtnText: { color: "#FFF", fontWeight: "600", fontSize: 14 },
  rejectBtn: { paddingHorizontal: 16, paddingVertical: 12, borderRadius: 10, backgroundColor: Colors.bg.elevated },
  rejectBtnText: { color: Colors.text.secondary, fontWeight: "600", fontSize: 14 },
});
