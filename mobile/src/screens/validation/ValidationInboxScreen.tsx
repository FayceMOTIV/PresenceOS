// PresenceOS Mobile — Validation Inbox Screen
// Shows pending autopilot content for approval/rejection

import React, { useCallback, useContext, useEffect, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  Image,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { BrandContext } from "@/contexts/BrandContext";
import { proposalsApi } from "@/lib/api";
import type { AIProposal } from "@/types";

export default function ValidationInboxScreen() {
  const brandCtx = useContext(BrandContext);
  const activeBrand = brandCtx?.activeBrand ?? null;
  const [proposals, setProposals] = useState<AIProposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchPending = useCallback(async () => {
    if (!activeBrand) return;
    try {
      const res = await proposalsApi.list(activeBrand.id, { status: "pending" });
      setProposals(res.data.proposals ?? res.data ?? []);
    } catch (err) {
      console.error("Failed to fetch pending proposals:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeBrand]);

  useEffect(() => {
    fetchPending();
  }, [fetchPending]);

  const handleApprove = async (proposal: AIProposal) => {
    if (!activeBrand) return;
    try {
      await proposalsApi.approve(activeBrand.id, proposal.id);
      setProposals((prev) => prev.filter((p) => p.id !== proposal.id));
    } catch (err) {
      Alert.alert("Erreur", "Impossible d'approuver ce post");
    }
  };

  const handleReject = (proposal: AIProposal) => {
    if (!activeBrand) return;
    Alert.alert("Rejeter ce post ?", "Cette action est irréversible.", [
      { text: "Annuler", style: "cancel" },
      {
        text: "Rejeter",
        style: "destructive",
        onPress: async () => {
          try {
            await proposalsApi.reject(activeBrand.id, proposal.id);
            setProposals((prev) => prev.filter((p) => p.id !== proposal.id));
          } catch {
            Alert.alert("Erreur", "Impossible de rejeter ce post");
          }
        },
      },
    ]);
  };

  const handleSchedule = async (proposal: AIProposal) => {
    if (!activeBrand) return;
    // Schedule for next optimal slot (default: tomorrow 12:00)
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(12, 0, 0, 0);

    try {
      await proposalsApi.approve(activeBrand.id, proposal.id, tomorrow.toISOString());
      setProposals((prev) => prev.filter((p) => p.id !== proposal.id));
      Alert.alert("Planifié !", `Post programmé pour ${tomorrow.toLocaleDateString("fr-FR")}`);
    } catch {
      Alert.alert("Erreur", "Impossible de planifier ce post");
    }
  };

  const renderItem = ({ item }: { item: AIProposal }) => (
    <View style={styles.card}>
      {/* Image preview */}
      {item.image_url && (
        <Image source={{ uri: item.image_url }} style={styles.image} resizeMode="cover" />
      )}

      {/* Type badge */}
      <View style={styles.typeBadge}>
        <Text style={styles.typeBadgeText}>
          {item.proposal_type === "post" ? "Post" : item.proposal_type === "reel" ? "Reel" : "Story"}
        </Text>
        <Text style={styles.platformText}>{item.platform}</Text>
      </View>

      {/* Caption */}
      <Text style={styles.caption} numberOfLines={4}>
        {item.caption || "Pas de légende"}
      </Text>

      {/* Hashtags */}
      {item.hashtags && item.hashtags.length > 0 && (
        <Text style={styles.hashtags} numberOfLines={2}>
          {item.hashtags.join(" ")}
        </Text>
      )}

      {/* Confidence score */}
      <View style={styles.scoreRow}>
        <Ionicons name="sparkles" size={14} color={Colors.brand.amber} />
        <Text style={styles.scoreText}>Score IA : {Math.round((item.confidence_score ?? 0) * 100)}%</Text>
      </View>

      {/* Action buttons */}
      <View style={styles.actions}>
        <TouchableOpacity
          style={[styles.actionBtn, styles.rejectBtn]}
          onPress={() => handleReject(item)}
        >
          <Ionicons name="close" size={18} color={Colors.status.danger} />
          <Text style={[styles.actionText, { color: Colors.status.danger }]}>Rejeter</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionBtn, styles.scheduleBtn]}
          onPress={() => handleSchedule(item)}
        >
          <Ionicons name="calendar-outline" size={18} color={Colors.brand.primary} />
          <Text style={[styles.actionText, { color: Colors.brand.primary }]}>Planifier</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.actionBtn, styles.approveBtn]}
          onPress={() => handleApprove(item)}
        >
          <Ionicons name="checkmark" size={18} color="#FFFFFF" />
          <Text style={[styles.actionText, { color: "#FFFFFF" }]}>Publier</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color={Colors.brand.primary} style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Validation</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{proposals.length}</Text>
        </View>
      </View>
      <Text style={styles.subtitle}>Contenus générés par l'IA en attente de validation</Text>

      {proposals.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="checkmark-circle" size={64} color={Colors.status.success} />
          <Text style={styles.emptyTitle}>Tout est validé !</Text>
          <Text style={styles.emptyBody}>
            Aucun contenu en attente. L'AutoPilot vous notifiera quand de nouveaux posts seront prêts.
          </Text>
        </View>
      ) : (
        <FlatList
          data={proposals}
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 100 }}
          showsVerticalScrollIndicator={false}
          refreshing={refreshing}
          onRefresh={() => {
            setRefreshing(true);
            fetchPending();
          }}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 16,
    gap: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    color: Colors.text.primary,
  },
  badge: {
    backgroundColor: Colors.brand.primary,
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 3,
  },
  badgeText: {
    color: "#FFFFFF",
    fontSize: 13,
    fontWeight: "700",
  },
  subtitle: {
    fontSize: 14,
    color: Colors.text.secondary,
    marginTop: 4,
    marginBottom: 20,
  },
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  image: {
    width: "100%",
    height: 200,
    borderRadius: 12,
    marginBottom: 12,
  },
  typeBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 8,
  },
  typeBadgeText: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.brand.primary,
    backgroundColor: Colors.brand.glow,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    overflow: "hidden",
  },
  platformText: {
    fontSize: 12,
    color: Colors.text.muted,
  },
  caption: {
    fontSize: 15,
    color: Colors.text.primary,
    lineHeight: 22,
    marginBottom: 8,
  },
  hashtags: {
    fontSize: 13,
    color: Colors.brand.primary,
    marginBottom: 8,
  },
  scoreRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginBottom: 12,
  },
  scoreText: {
    fontSize: 12,
    color: Colors.text.secondary,
  },
  actions: {
    flexDirection: "row",
    gap: 8,
  },
  actionBtn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    paddingVertical: 10,
    borderRadius: 10,
  },
  rejectBtn: {
    backgroundColor: Colors.status.dangerLight,
  },
  scheduleBtn: {
    backgroundColor: Colors.brand.glow,
  },
  approveBtn: {
    backgroundColor: Colors.brand.primary,
  },
  actionText: {
    fontSize: 13,
    fontWeight: "600",
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.text.primary,
    marginTop: 16,
    marginBottom: 8,
  },
  emptyBody: {
    fontSize: 14,
    color: Colors.text.secondary,
    textAlign: "center",
    lineHeight: 20,
  },
});
