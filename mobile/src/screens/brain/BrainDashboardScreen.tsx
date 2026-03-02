// PresenceOS Mobile — Brain Dashboard Screen
// Shows BrandBrain + VisualBrain status, memories, and maturity

import React, { useCallback, useContext, useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { BrandContext } from "@/contexts/BrandContext";
import { brainApi } from "@/lib/api";
import type { BrainStatus, VisualBrainStatus, BrainMemory } from "@/types/brain";

export default function BrainDashboardScreen() {
  const brandCtx = useContext(BrandContext);
  const activeBrand = brandCtx?.activeBrand ?? null;
  const [brainStatus, setBrainStatus] = useState<BrainStatus | null>(null);
  const [visualStatus, setVisualStatus] = useState<VisualBrainStatus | null>(null);
  const [recentMemories, setRecentMemories] = useState<BrainMemory[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!activeBrand) return;
    try {
      const [brainRes, visualRes, memoriesRes] = await Promise.allSettled([
        brainApi.status(activeBrand.id),
        brainApi.visualStatus(activeBrand.id),
        brainApi.recall(activeBrand.id, "résumé des souvenirs récents"),
      ]);
      if (brainRes.status === "fulfilled") setBrainStatus(brainRes.value.data);
      if (visualRes.status === "fulfilled") setVisualStatus(visualRes.value.data);
      if (memoriesRes.status === "fulfilled") {
        const d = memoriesRes.value.data;
        setRecentMemories(d.memories ?? d ?? []);
      }
    } catch (err) {
      console.error("Failed to fetch brain data:", err);
    } finally {
      setLoading(false);
    }
  }, [activeBrand]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const maturityColor = (maturity: number) => {
    if (maturity < 20) return Colors.status.danger;
    if (maturity < 40) return Colors.status.warning;
    if (maturity < 60) return Colors.brand.amber;
    if (maturity < 80) return Colors.status.info;
    return Colors.status.success;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <ActivityIndicator size="large" color={Colors.brand.primary} style={{ marginTop: 40 }} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: 100 }}>
        {/* Header */}
        <Text style={styles.title}>Cerveau IA</Text>
        <Text style={styles.subtitle}>Mémoire et apprentissage de votre marque</Text>

        {/* Empty state */}
        {!brainStatus && !visualStatus && recentMemories.length === 0 && (
          <View style={styles.card}>
            <View style={{ alignItems: "center", paddingVertical: 24 }}>
              <Text style={{ fontSize: 40, marginBottom: 12 }}>🧠</Text>
              <Text style={[styles.cardTitle, { textAlign: "center", marginBottom: 8 }]}>
                Cerveau en cours d'initialisation
              </Text>
              <Text style={[styles.maturityLabel, { textAlign: "center", lineHeight: 20 }]}>
                Ajoutez du contenu (photos, plats, brief) pour que l'IA apprenne votre marque.
              </Text>
            </View>
          </View>
        )}

        {/* Brain Maturity Card */}
        {brainStatus && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="bulb-outline" size={20} color={Colors.brand.primary} />
              <Text style={styles.cardTitle}>BrandBrain — Texte</Text>
            </View>

            {/* Maturity bar */}
            <View style={styles.maturityRow}>
              <Text style={styles.maturityLabel}>{brainStatus.maturity_label}</Text>
              <Text style={[styles.maturityPct, { color: maturityColor(brainStatus.maturity) }]}>
                {brainStatus.maturity}%
              </Text>
            </View>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  {
                    width: `${brainStatus.maturity}%`,
                    backgroundColor: maturityColor(brainStatus.maturity),
                  },
                ]}
              />
            </View>

            {/* Memory counts */}
            <View style={styles.statsGrid}>
              {Object.entries(brainStatus.memory_counts).map(([type, count]) => (
                <View key={type} style={styles.statItem}>
                  <Text style={styles.statValue}>{count}</Text>
                  <Text style={styles.statLabel}>
                    {type === "episodic"
                      ? "Épisodiques"
                      : type === "semantic"
                      ? "Sémantiques"
                      : type === "procedural"
                      ? "Procédurales"
                      : "Réflexions"}
                  </Text>
                </View>
              ))}
            </View>

            <Text style={styles.totalMemories}>
              {brainStatus.total_memories} souvenirs au total
            </Text>
          </View>
        )}

        {/* Visual Brain Card */}
        {visualStatus && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="eye" size={20} color={Colors.brand.amber} />
              <Text style={styles.cardTitle}>VisualBrain — Images</Text>
            </View>

            <View style={styles.maturityRow}>
              <Text style={styles.maturityLabel}>Maturité visuelle</Text>
              <Text style={[styles.maturityPct, { color: maturityColor(visualStatus.maturity) }]}>
                {visualStatus.maturity}%
              </Text>
            </View>
            <View style={styles.progressBar}>
              <View
                style={[
                  styles.progressFill,
                  {
                    width: `${visualStatus.maturity}%`,
                    backgroundColor: maturityColor(visualStatus.maturity),
                  },
                ]}
              />
            </View>

            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{visualStatus.total_visuals}</Text>
                <Text style={styles.statLabel}>Visuels</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{visualStatus.scored_visuals}</Text>
                <Text style={styles.statLabel}>Évalués</Text>
              </View>
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{visualStatus.active_templates}</Text>
                <Text style={styles.statLabel}>Templates</Text>
              </View>
            </View>
          </View>
        )}

        {/* Recent Memories */}
        {recentMemories.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="time" size={20} color={Colors.text.secondary} />
              <Text style={styles.cardTitle}>Souvenirs récents</Text>
            </View>

            {recentMemories.slice(0, 5).map((memory) => (
              <View key={memory.id} style={styles.memoryItem}>
                <View style={styles.memoryBadge}>
                  <Text style={styles.memoryBadgeText}>
                    {memory.memory_type === "episodic"
                      ? "É"
                      : memory.memory_type === "semantic"
                      ? "S"
                      : memory.memory_type === "procedural"
                      ? "P"
                      : "R"}
                  </Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.memoryContent} numberOfLines={2}>
                    {memory.content}
                  </Text>
                  <Text style={styles.memoryMeta}>
                    Confiance: {Math.round(memory.confidence * 100)}%
                    {memory.similarity ? ` • Similarité: ${Math.round(memory.similarity * 100)}%` : ""}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary,
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: "800",
    color: Colors.text.primary,
    marginTop: 16,
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
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  maturityRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 6,
  },
  maturityLabel: {
    fontSize: 14,
    color: Colors.text.secondary,
  },
  maturityPct: {
    fontSize: 16,
    fontWeight: "700",
  },
  progressBar: {
    height: 8,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 4,
    marginBottom: 16,
    overflow: "hidden",
  },
  progressFill: {
    height: "100%",
    borderRadius: 4,
  },
  statsGrid: {
    flexDirection: "row",
    gap: 12,
  },
  statItem: {
    flex: 1,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 10,
    padding: 10,
    alignItems: "center",
  },
  statValue: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  statLabel: {
    fontSize: 11,
    color: Colors.text.muted,
    marginTop: 2,
  },
  totalMemories: {
    fontSize: 12,
    color: Colors.text.muted,
    textAlign: "center",
    marginTop: 12,
  },
  memoryItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  memoryBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.brand.glow,
    alignItems: "center",
    justifyContent: "center",
  },
  memoryBadgeText: {
    fontSize: 12,
    fontWeight: "700",
    color: Colors.brand.primary,
  },
  memoryContent: {
    fontSize: 13,
    color: Colors.text.primary,
    lineHeight: 18,
  },
  memoryMeta: {
    fontSize: 11,
    color: Colors.text.muted,
    marginTop: 2,
  },
});
