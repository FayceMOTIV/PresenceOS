// PresenceOS Mobile — Inbox Screen (Sprint 5: Unified Engage Inbox)
// Combines Google reviews (v1 cmApi) + Comments/DMs (v2 engageApi)

import React, { useContext, useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TextInput,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { BrandContext } from "@/contexts/BrandContext";
import { InboxStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { cmApi, engageApi } from "@/lib/api";
import EmptyStateCard from "@/components/EmptyStateCard";

// Unified inbox item (works for both v1 CMInteraction and v2 Comment)
interface InboxItem {
  id: string;
  platform: string;
  author_name: string;
  text: string;
  sentiment: string;
  urgency_score: number;
  suggested_reply: string;
  reply_status: string;
  final_reply: string;
  created_at: string;
  is_dm: boolean;
  source: "engage" | "cm"; // track origin
}

type Nav = NativeStackNavigationProp<InboxStackParams>;
type FilterTab = "all" | "pending" | "urgent" | "done";

const SENTIMENT_EMOJI: Record<string, string> = {
  positive: "😊",
  negative: "😡",
  question: "❓",
  spam: "🚫",
  neutral: "💬",
  urgent: "🚨",
};

const URGENCY_COLOR = (score: number): string => {
  if (score >= 8) return Colors.status.danger;
  if (score >= 5) return Colors.status.warning;
  return Colors.status.success;
};

export default function InboxScreen() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [items, setItems] = useState<InboxItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingReply, setEditingReply] = useState<string>("");
  const [activeTab, setActiveTab] = useState<FilterTab>("all");

  // Fetch both v1 CM interactions + v2 engage inbox
  const fetchAll = useCallback(async () => {
    if (!brandId) return;
    const allItems: InboxItem[] = [];

    // v1 — Google reviews / CM interactions
    try {
      const res = await cmApi.listInteractions(brandId);
      const interactions = res.data.interactions || res.data || [];
      for (const i of interactions) {
        allItems.push({
          id: i.id,
          platform: i.platform || "google",
          author_name: i.commenter_name || "Anonyme",
          text: i.content || "",
          sentiment: "neutral",
          urgency_score: 5,
          suggested_reply: i.ai_response_draft || "",
          reply_status: i.response_status || "pending",
          final_reply: "",
          created_at: i.created_at || "",
          is_dm: false,
          source: "cm",
        });
      }
    } catch {
      // v1 may not be available
    }

    // v2 — Engage inbox (comments + DMs)
    try {
      const res = await engageApi.inbox(brandId);
      const comments = res.data || [];
      for (const c of comments) {
        allItems.push({
          id: c.id,
          platform: c.platform || "instagram",
          author_name: c.author_name || "Anonyme",
          text: c.text || "",
          sentiment: c.sentiment || "neutral",
          urgency_score: c.urgency_score || 0,
          suggested_reply: c.suggested_reply || "",
          reply_status: c.reply_status || "pending",
          final_reply: c.final_reply || "",
          created_at: c.created_at || "",
          is_dm: c.is_dm || false,
          source: "engage",
        });
      }
    } catch {
      // v2 may not be available yet
    }

    // Sort by urgency (high first), then by date (recent first)
    allItems.sort((a, b) => {
      if (b.urgency_score !== a.urgency_score) return b.urgency_score - a.urgency_score;
      return (b.created_at || "").localeCompare(a.created_at || "");
    });

    setItems(allItems);
  }, [brandId]);

  useEffect(() => {
    fetchAll().finally(() => setLoading(false));
  }, [fetchAll]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchAll();
    setRefreshing(false);
  }, [fetchAll]);

  // Scan for new comments
  const handleScan = useCallback(async () => {
    if (!brandId || scanning) return;
    setScanning(true);
    try {
      const res = await engageApi.scan(brandId);
      const data = res.data;
      Alert.alert(
        "Scan termine",
        `${data.fetched} commentaires trouves, ${data.replies_generated} reponses generees.`,
      );
      await fetchAll();
    } catch {
      Alert.alert(FR.error_generic);
    } finally {
      setScanning(false);
    }
  }, [brandId, scanning, fetchAll]);

  // Approve reply
  const handleApprove = useCallback(
    async (item: InboxItem) => {
      if (!brandId) return;
      try {
        if (item.source === "engage") {
          const reply = editingReply || undefined;
          await engageApi.approve(brandId, item.id, reply);
        } else {
          await cmApi.approve(item.id, editingReply || undefined);
        }
        setItems((prev) =>
          prev.map((i) =>
            i.id === item.id ? { ...i, reply_status: "approved" } : i
          ),
        );
        setExpandedId(null);
        setEditingReply("");
      } catch {
        Alert.alert(FR.error_generic);
      }
    },
    [brandId, editingReply],
  );

  // Reject reply
  const handleReject = useCallback(
    async (item: InboxItem) => {
      if (!brandId) return;
      try {
        if (item.source === "engage") {
          await engageApi.reject(brandId, item.id);
        } else {
          await cmApi.reject(item.id);
        }
        setItems((prev) =>
          prev.map((i) =>
            i.id === item.id ? { ...i, reply_status: "rejected" } : i
          ),
        );
      } catch {
        Alert.alert(FR.error_generic);
      }
    },
    [brandId],
  );

  // Filter
  const filteredItems = items.filter((item) => {
    if (activeTab === "pending") return item.reply_status === "pending" || item.reply_status === "classified";
    if (activeTab === "urgent") return item.urgency_score >= 7;
    if (activeTab === "done") return ["approved", "published", "rejected", "skipped"].includes(item.reply_status);
    return true;
  });

  const pendingCount = items.filter((i) => i.reply_status === "pending" || i.reply_status === "classified").length;
  const urgentCount = items.filter((i) => i.urgency_score >= 7).length;

  // Render
  const renderItem = ({ item }: { item: InboxItem }) => {
    const expanded = expandedId === item.id;
    const isPending = item.reply_status === "pending" || item.reply_status === "classified";
    const isDone = ["approved", "published"].includes(item.reply_status);
    const statusColor = isPending ? Colors.status.warning : isDone ? Colors.status.success : Colors.text.muted;

    return (
      <TouchableOpacity
        style={styles.card}
        onPress={() => {
          setExpandedId(expanded ? null : item.id);
          setEditingReply(item.suggested_reply || "");
        }}
        activeOpacity={0.8}
      >
        <View style={styles.cardHeader}>
          <View style={styles.cardLeft}>
            <Text style={styles.sentimentEmoji}>
              {SENTIMENT_EMOJI[item.sentiment] || "💬"}
            </Text>
            <View>
              <Text style={styles.customerName}>{item.author_name}</Text>
              <View style={styles.metaRow}>
                <Text style={styles.platform}>{item.platform}</Text>
                {item.is_dm && (
                  <View style={styles.dmBadge}>
                    <Text style={styles.dmBadgeText}>DM</Text>
                  </View>
                )}
              </View>
            </View>
          </View>
          <View style={styles.rightCol}>
            {item.urgency_score >= 5 && (
              <View
                style={[
                  styles.urgencyBadge,
                  { backgroundColor: URGENCY_COLOR(item.urgency_score) + "20" },
                ]}
              >
                <Text
                  style={[
                    styles.urgencyText,
                    { color: URGENCY_COLOR(item.urgency_score) },
                  ]}
                >
                  {item.urgency_score.toFixed(0)}/10
                </Text>
              </View>
            )}
            <View style={[styles.dot, { backgroundColor: statusColor }]} />
          </View>
        </View>

        <Text style={styles.message} numberOfLines={expanded ? undefined : 2}>
          {item.text}
        </Text>

        {expanded && (
          <View style={styles.expandedSection}>
            {item.suggested_reply ? (
              <>
                <Text style={styles.aiLabel}>{FR.inbox_auto_reply}</Text>
                <TextInput
                  style={styles.replyInput}
                  value={editingReply}
                  onChangeText={setEditingReply}
                  multiline
                  maxLength={2000}
                  placeholder="Modifier la reponse..."
                  placeholderTextColor={Colors.text.muted}
                />
              </>
            ) : (
              <Text style={styles.noReply}>Pas de reponse suggeree</Text>
            )}

            {isPending && (
              <View style={styles.actionRow}>
                <TouchableOpacity
                  style={styles.approveBtn}
                  onPress={() => handleApprove(item)}
                >
                  <Ionicons name="checkmark" size={16} color="#FFF" />
                  <Text style={styles.approveBtnText}>
                    {FR.inbox_approve_reply}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.rejectBtn}
                  onPress={() => handleReject(item)}
                >
                  <Text style={styles.rejectBtnText}>{FR.inbox_ignore}</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderFilterTab = (tab: FilterTab, label: string, count?: number) => (
    <TouchableOpacity
      style={[styles.filterTab, activeTab === tab && styles.filterTabActive]}
      onPress={() => setActiveTab(tab)}
    >
      <Text
        style={[
          styles.filterTabText,
          activeTab === tab && styles.filterTabTextActive,
        ]}
      >
        {label}
        {count !== undefined && count > 0 ? ` (${count})` : ""}
      </Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.headerRow}>
        <Text style={styles.title}>Inbox</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={styles.scanBtn}
            onPress={handleScan}
            disabled={scanning}
            activeOpacity={0.8}
          >
            {scanning ? (
              <ActivityIndicator size="small" color={Colors.brand.primary} />
            ) : (
              <Ionicons name="refresh" size={18} color={Colors.brand.primary} />
            )}
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.chatBtn}
            onPress={() => nav.navigate("CMChat")}
            activeOpacity={0.8}
          >
            <Ionicons name="sparkles" size={14} color={Colors.text.inverted} />
            <Text style={styles.chatBtnText}>{FR.cm_chat_title}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Filter tabs */}
      <View style={styles.filterRow}>
        {renderFilterTab("all", "Tout", items.length)}
        {renderFilterTab("pending", "En attente", pendingCount)}
        {renderFilterTab("urgent", "Urgents", urgentCount)}
        {renderFilterTab("done", "Traites")}
      </View>

      {/* Content */}
      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
        </View>
      ) : filteredItems.length === 0 ? (
        <View style={styles.emptyContainer}>
          <EmptyStateCard
            emoji="💬"
            title="Aucun message"
            body="Scannez vos reseaux pour voir les commentaires et DMs de vos clients."
            ctaLabel="Scanner maintenant"
            onCta={handleScan}
          />
        </View>
      ) : (
        <FlatList
          data={filteredItems}
          keyExtractor={(item) => `${item.source}-${item.id}`}
          renderItem={renderItem}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={Colors.brand.primary}
            />
          }
          contentContainerStyle={styles.list}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  headerRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 12,
  },
  title: { fontSize: 24, fontWeight: "700", color: Colors.text.primary },
  headerActions: { flexDirection: "row", alignItems: "center", gap: 8 },
  scanBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.bg.secondary,
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  chatBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: Colors.brand.primary,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  chatBtnText: {
    color: Colors.text.inverted,
    fontWeight: "600",
    fontSize: 13,
  },

  // Filter tabs
  filterRow: {
    flexDirection: "row",
    paddingHorizontal: 16,
    marginBottom: 12,
    gap: 8,
  },
  filterTab: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  filterTabActive: {
    backgroundColor: Colors.brand.primary,
    borderColor: Colors.brand.primary,
  },
  filterTabText: {
    fontSize: 13,
    fontWeight: "500",
    color: Colors.text.secondary,
  },
  filterTabTextActive: { color: "#FFF" },

  // Content
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyContainer: { flex: 1, justifyContent: "center", paddingHorizontal: 20 },
  list: { paddingHorizontal: 16, paddingBottom: 80, gap: 12 },

  // Cards
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  cardLeft: { flexDirection: "row", alignItems: "center", gap: 10 },
  sentimentEmoji: { fontSize: 20 },
  customerName: { fontSize: 15, fontWeight: "600", color: Colors.text.primary },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 2 },
  platform: { fontSize: 12, color: Colors.text.muted },
  dmBadge: {
    backgroundColor: Colors.status.info + "20",
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  dmBadgeText: { fontSize: 10, fontWeight: "600", color: Colors.status.info },
  rightCol: { flexDirection: "row", alignItems: "center", gap: 8 },
  urgencyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  urgencyText: { fontSize: 11, fontWeight: "700" },
  dot: { width: 8, height: 8, borderRadius: 4 },

  // Message
  message: { fontSize: 14, color: Colors.text.secondary, lineHeight: 20 },

  // Expanded
  expandedSection: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.border.default,
  },
  aiLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: Colors.brand.primary,
    marginBottom: 6,
  },
  replyInput: {
    backgroundColor: Colors.bg.primary,
    borderRadius: 12,
    padding: 12,
    fontSize: 14,
    color: Colors.text.primary,
    lineHeight: 20,
    borderWidth: 1,
    borderColor: Colors.border.default,
    marginBottom: 12,
    minHeight: 60,
    textAlignVertical: "top",
  },
  noReply: {
    fontSize: 13,
    color: Colors.text.muted,
    fontStyle: "italic",
    marginBottom: 12,
  },
  actionRow: { flexDirection: "row", gap: 8 },
  approveBtn: {
    flex: 1,
    flexDirection: "row",
    backgroundColor: Colors.brand.primary,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
  },
  approveBtnText: { color: "#FFF", fontWeight: "600", fontSize: 14 },
  rejectBtn: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: Colors.bg.elevated,
  },
  rejectBtnText: {
    color: Colors.text.secondary,
    fontWeight: "600",
    fontSize: 14,
  },
});
