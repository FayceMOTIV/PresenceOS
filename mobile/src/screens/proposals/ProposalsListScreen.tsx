// PresenceOS Mobile — Proposals List (premium violet/amber theme)

import React, { useContext, useState, useEffect, useCallback } from "react";
import { View, FlatList, StyleSheet, TouchableOpacity, Text, RefreshControl, ActivityIndicator } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { SafeAreaView } from "react-native-safe-area-context";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { ProposalsStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { proposalsApi } from "@/lib/api";
import { AIProposal } from "@/types";
import ProposalCard from "@/components/ProposalCard";
import EmptyStateCard from "@/components/EmptyStateCard";

type Nav = NativeStackNavigationProp<ProposalsStackParams>;

const FILTERS = [
  { key: "all", label: FR.proposals_filter_all },
  { key: "pending", label: FR.proposals_filter_pending },
  { key: "approved", label: FR.proposals_filter_approved },
  { key: "published", label: FR.proposals_filter_published },
  { key: "rejected", label: FR.proposals_filter_rejected },
];

export default function ProposalsListScreen() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [proposals, setProposals] = useState<AIProposal[]>([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchProposals = useCallback(async () => {
    if (!brandId) return;
    try {
      const params = filter !== "all" ? { status: filter } : undefined;
      const res = await proposalsApi.list(brandId, params);
      setProposals(res.data.proposals || res.data || []);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [brandId, filter]);

  useEffect(() => { fetchProposals(); }, [fetchProposals]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchProposals();
    setRefreshing(false);
  }, [fetchProposals]);

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      <Text style={styles.title}>{FR.proposals_title}</Text>

      {/* Filters */}
      <View style={styles.filters}>
        {FILTERS.map((f) => {
          const isActive = filter === f.key;
          return (
            <TouchableOpacity
              key={f.key}
              style={[styles.filterBtn, isActive && styles.filterBtnActive]}
              onPress={() => setFilter(f.key)}
              activeOpacity={0.8}
            >
              {isActive ? (
                <LinearGradient
                  colors={[...Colors.gradient.hero]}
                  style={styles.filterGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                >
                  <Text style={styles.filterTextActive}>{f.label}</Text>
                </LinearGradient>
              ) : (
                <Text style={styles.filterText}>{f.label}</Text>
              )}
            </TouchableOpacity>
          );
        })}
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
        </View>
      ) : proposals.length === 0 ? (
        <EmptyStateCard
          emoji="🤖"
          title={FR.proposals_empty_title}
          body={FR.proposals_empty_body}
          ctaLabel={FR.proposals_empty_cta}
          onCta={() => nav.getParent()?.navigate("Files" as never)}
        />
      ) : (
        <FlatList
          data={proposals}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <ProposalCard
              proposal={item}
              onPress={() => nav.navigate("ProposalDetail", { proposalId: item.id })}
            />
          )}
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
  filters: { flexDirection: "row", paddingHorizontal: 16, gap: 8, marginBottom: 12, flexWrap: "wrap" },
  filterBtn: {
    borderRadius: 20,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
    overflow: "hidden",
  },
  filterBtnActive: {
    borderColor: "transparent",
    borderWidth: 0,
  },
  filterGradient: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  filterText: { fontSize: 13, fontWeight: "600", color: Colors.text.secondary, paddingHorizontal: 14, paddingVertical: 8 },
  filterTextActive: { fontSize: 13, fontWeight: "600", color: "#FFF" },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  list: { paddingHorizontal: 16, paddingBottom: 80, gap: 12 },
});
