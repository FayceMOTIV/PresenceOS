// PresenceOS Mobile — Editorial Calendar with swipe approve/reject

import React, { useState, useEffect, useRef, useContext, useCallback } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  PanResponder,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";
import { BrandContext } from "@/contexts/BrandContext";
import { calendarApi } from "@/lib/api";

const PLATFORM_ICONS: Record<string, string> = {
  instagram: "📸",
  facebook: "👤",
  tiktok: "🎵",
  linkedin: "💼",
};

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E1306C",
  facebook: "#1877F2",
  tiktok: "#010101",
  linkedin: "#0A66C2",
};

const STATUS_LABELS: Record<string, string> = {
  pending_approval: "En attente",
  approved: "Approuvé",
  scheduled: "Planifié",
  published: "Publié",
  rejected: "Rejeté",
};

const STATUS_COLORS: Record<string, string> = {
  pending_approval: Colors.status.warning,
  approved: Colors.status.success,
  scheduled: Colors.status.info,
  published: Colors.text.muted,
  rejected: Colors.status.danger,
};

function SwipeablePostCard({
  post,
  onApprove,
  onReject,
}: {
  post: any;
  onApprove: () => void;
  onReject: () => void;
}) {
  const pan = useRef(new Animated.ValueXY()).current;

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 10,
      onPanResponderMove: Animated.event([null, { dx: pan.x }], {
        useNativeDriver: false,
      }),
      onPanResponderRelease: (_, g) => {
        if (g.dx > 80) {
          Animated.timing(pan, {
            toValue: { x: 500, y: 0 },
            duration: 200,
            useNativeDriver: false,
          }).start(onApprove);
        } else if (g.dx < -80) {
          Animated.timing(pan, {
            toValue: { x: -500, y: 0 },
            duration: 200,
            useNativeDriver: false,
          }).start(onReject);
        } else {
          Animated.spring(pan, {
            toValue: { x: 0, y: 0 },
            useNativeDriver: false,
          }).start();
        }
      },
    })
  ).current;

  const borderColor = pan.x.interpolate({
    inputRange: [-150, 0, 150],
    outputRange: [Colors.status.danger, Colors.border.default, Colors.status.success],
    extrapolate: "clamp",
  });

  return (
    <Animated.View
      style={[
        s.postCard,
        {
          borderColor,
          transform: [{ translateX: pan.x }],
        },
      ]}
      {...panResponder.panHandlers}
    >
      <View style={s.postHeader}>
        <Text style={s.platformIcon}>
          {PLATFORM_ICONS[post.platform] || "🌐"}
        </Text>
        <Text
          style={[
            s.platformName,
            { color: PLATFORM_COLORS[post.platform] || Colors.text.primary },
          ]}
        >
          {post.platform} · {post.content_type}
        </Text>
        <View
          style={[
            s.statusBadge,
            { backgroundColor: (STATUS_COLORS[post.status] || Colors.text.muted) + "20" },
          ]}
        >
          <Text
            style={[
              s.statusText,
              { color: STATUS_COLORS[post.status] || Colors.text.muted },
            ]}
          >
            {STATUS_LABELS[post.status] || post.status}
          </Text>
        </View>
      </View>

      {post.scheduled_date && (
        <Text style={s.dateText}>
          📅 {post.scheduled_date}
          {post.scheduled_time ? ` à ${post.scheduled_time}` : ""}
        </Text>
      )}

      <Text style={s.postCaption} numberOfLines={3}>
        {post.caption || "(Pas de caption)"}
      </Text>

      {post.hashtags?.length > 0 && (
        <Text style={s.postHashtags} numberOfLines={1}>
          {post.hashtags.slice(0, 4).join(" ")}
        </Text>
      )}

      {post.visual_description ? (
        <Text style={s.visualDesc} numberOfLines={1}>
          🖼 {post.visual_description}
        </Text>
      ) : null}

      <View style={s.postFooter}>
        <Text style={s.engagementText}>
          Engagement : {post.estimated_engagement || "medium"}
        </Text>
        <Text style={s.swipeHint}>← Rejeter · Approuver →</Text>
      </View>
    </Animated.View>
  );
}

export default function CalendarScreen() {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;
  const brandName = brand?.activeBrand?.name || "Mon business";

  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [postsPerDay, setPostsPerDay] = useState(3);
  const [storiesPerDay, setStoriesPerDay] = useState(2);

  const loadCalendar = useCallback(async () => {
    if (!brandId) return;
    setLoading(true);
    try {
      const res = await calendarApi.getCalendar(brandId);
      setPosts(res.data?.posts || res.data?.posts || []);
    } catch (e) {
      console.error("loadCalendar error", e);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    loadCalendar();
  }, [loadCalendar]);

  const handleGenerate = async () => {
    if (!brandId) return;
    setGenerating(true);
    try {
      const res = await calendarApi.generate(brandId, {
        posts_per_day: postsPerDay,
        stories_per_day: storiesPerDay,
      });
      const total = res.data?.total_posts || 0;
      Alert.alert(
        "Calendrier généré !",
        `${total} posts créés.\nSwipe → pour approuver, ← pour rejeter.`,
        [{ text: "OK", onPress: loadCalendar }]
      );
    } catch {
      Alert.alert("Erreur", "Génération échouée. Réessaie.");
    } finally {
      setGenerating(false);
    }
  };

  const handleApproveAll = () => {
    const pending = posts.filter((p) => p.status === "pending_approval");
    if (pending.length === 0) return;
    Alert.alert(
      "Approuver tout ?",
      `${pending.length} posts seront approuvés.`,
      [
        { text: "Annuler", style: "cancel" },
        {
          text: "Oui, tout approuver",
          onPress: async () => {
            if (!brandId) return;
            await calendarApi.approveAll(brandId);
            await loadCalendar();
          },
        },
      ]
    );
  };

  const handleApprove = async (postId: string) => {
    if (!brandId) return;
    try {
      await calendarApi.approvePost(brandId, postId);
      setPosts((prev) => prev.filter((p) => p.id !== postId));
    } catch {
      Alert.alert("Erreur", "Impossible d'approuver ce post.");
    }
  };

  const handleReject = async (postId: string) => {
    if (!brandId) return;
    try {
      await calendarApi.rejectPost(brandId, postId);
      setPosts((prev) => prev.filter((p) => p.id !== postId));
    } catch {
      Alert.alert("Erreur", "Impossible de rejeter ce post.");
    }
  };

  const pendingPosts = posts.filter((p) => p.status === "pending_approval");
  const pendingCount = pendingPosts.length;

  return (
    <View style={s.container}>
      {/* Header */}
      <View style={s.header}>
        <Text style={s.title}>Calendrier</Text>
        <Text style={s.subtitle}>{brandName}</Text>
      </View>

      {/* Rules */}
      <View style={s.rulesRow}>
        <View style={s.ruleItem}>
          <Text style={s.ruleLabel}>Posts/jour</Text>
          <View style={s.ruleControl}>
            <TouchableOpacity
              onPress={() => setPostsPerDay((v) => Math.max(1, v - 1))}
            >
              <Text style={s.ruleBtn}>−</Text>
            </TouchableOpacity>
            <Text style={s.ruleValue}>{postsPerDay}</Text>
            <TouchableOpacity
              onPress={() => setPostsPerDay((v) => Math.min(10, v + 1))}
            >
              <Text style={s.ruleBtn}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={s.ruleItem}>
          <Text style={s.ruleLabel}>Stories/jour</Text>
          <View style={s.ruleControl}>
            <TouchableOpacity
              onPress={() => setStoriesPerDay((v) => Math.max(0, v - 1))}
            >
              <Text style={s.ruleBtn}>−</Text>
            </TouchableOpacity>
            <Text style={s.ruleValue}>{storiesPerDay}</Text>
            <TouchableOpacity
              onPress={() => setStoriesPerDay((v) => Math.min(5, v + 1))}
            >
              <Text style={s.ruleBtn}>+</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity
          style={[s.generateBtn, generating && s.generateBtnDisabled]}
          onPress={handleGenerate}
          disabled={generating}
        >
          {generating ? (
            <ActivityIndicator color="#FFF" size="small" />
          ) : (
            <LinearGradient
              colors={Colors.gradient.hero}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.generateGradient}
            >
              <Text style={s.generateBtnText}>Générer</Text>
            </LinearGradient>
          )}
        </TouchableOpacity>
      </View>

      {/* Pending bar */}
      {pendingCount > 0 && (
        <View style={s.pendingBar}>
          <Text style={s.pendingText}>
            {pendingCount} post{pendingCount > 1 ? "s" : ""} en attente
          </Text>
          <TouchableOpacity style={s.approveAllBtn} onPress={handleApproveAll}>
            <Text style={s.approveAllText}>Tout approuver</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Content */}
      {loading ? (
        <ActivityIndicator
          color={Colors.brand.primary}
          style={{ marginTop: 40 }}
          size="large"
        />
      ) : pendingPosts.length === 0 ? (
        <View style={s.empty}>
          <Text style={s.emptyEmoji}>{posts.length === 0 ? "📅" : "✅"}</Text>
          <Text style={s.emptyText}>
            {posts.length === 0
              ? "Aucun contenu planifié.\nTape Générer pour créer le calendrier."
              : "Tous les posts sont traités !"}
          </Text>
        </View>
      ) : (
        <ScrollView contentContainerStyle={s.postList}>
          {pendingPosts.map((post) => (
            <SwipeablePostCard
              key={post.id}
              post={post}
              onApprove={() => handleApprove(post.id)}
              onReject={() => handleReject(post.id)}
            />
          ))}
        </ScrollView>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: {
    paddingTop: 60,
    paddingHorizontal: 24,
    paddingBottom: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    color: Colors.text.primary,
  },
  subtitle: {
    fontSize: 14,
    color: Colors.text.secondary,
    marginTop: 2,
  },
  rulesRow: {
    flexDirection: "row",
    paddingHorizontal: 20,
    paddingVertical: 12,
    gap: 12,
    alignItems: "center",
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  ruleItem: { flex: 1 },
  ruleLabel: {
    color: Colors.text.muted,
    fontSize: 11,
    marginBottom: 6,
    fontWeight: "600",
  },
  ruleControl: { flexDirection: "row", alignItems: "center", gap: 10 },
  ruleBtn: {
    color: Colors.brand.primary,
    fontSize: 22,
    fontWeight: "700",
    paddingHorizontal: 4,
  },
  ruleValue: {
    color: Colors.text.primary,
    fontSize: 18,
    fontWeight: "700",
    minWidth: 26,
    textAlign: "center",
  },
  generateBtn: { borderRadius: 12, overflow: "hidden" },
  generateBtnDisabled: { opacity: 0.5 },
  generateGradient: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 12,
  },
  generateBtnText: { color: "#FFF", fontWeight: "800", fontSize: 13 },
  pendingBar: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: Colors.status.warningLight,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  pendingText: {
    color: Colors.status.warning,
    fontWeight: "600",
    fontSize: 13,
  },
  approveAllBtn: {
    backgroundColor: Colors.status.success,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  approveAllText: { color: "#FFF", fontWeight: "700", fontSize: 12 },
  postList: { padding: 16, gap: 12, paddingBottom: 40 },
  postCard: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1.5,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  postHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  platformIcon: { fontSize: 18 },
  platformName: { fontSize: 12, fontWeight: "700", flex: 1 },
  statusBadge: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3 },
  statusText: { fontSize: 10, fontWeight: "700" },
  dateText: {
    color: Colors.text.muted,
    fontSize: 11,
    marginBottom: 6,
  },
  postCaption: {
    color: Colors.text.primary,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 6,
  },
  postHashtags: {
    color: Colors.brand.primary,
    fontSize: 12,
    marginBottom: 6,
  },
  visualDesc: {
    color: Colors.text.muted,
    fontSize: 11,
    marginBottom: 6,
    fontStyle: "italic",
  },
  postFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: 4,
  },
  engagementText: { color: Colors.text.muted, fontSize: 11 },
  swipeHint: {
    color: Colors.text.muted,
    fontSize: 10,
  },
  empty: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 40,
    marginTop: 60,
  },
  emptyEmoji: { fontSize: 48, marginBottom: 16 },
  emptyText: {
    color: Colors.text.secondary,
    textAlign: "center",
    lineHeight: 24,
    fontSize: 15,
  },
});
