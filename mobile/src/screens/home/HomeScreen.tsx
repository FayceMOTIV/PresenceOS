// PresenceOS Mobile — HomeScreen (dark theme, French)

import React, { useContext, useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useNavigation } from "@react-navigation/native";
import { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { BrandContext } from "@/contexts/BrandContext";
import { HomeStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import KBCompletenessBar from "@/components/KBCompletenessBar";
import ProposalCard from "@/components/ProposalCard";
import EmptyStateCard from "@/components/EmptyStateCard";
import { kbApi, proposalsApi, briefApi, socialApi, videoApi } from "@/lib/api";
import { AIProposal } from "@/types";

type Nav = NativeStackNavigationProp<HomeStackParams>;

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={[statStyles.card, {
      backgroundColor: color + "12",
      borderColor: color + "30",
      shadowColor: color,
    }]}>
      <Text style={[statStyles.value, { color }]}>{value}</Text>
      <Text style={statStyles.label}>{label}</Text>
    </View>
  );
}

const statStyles = StyleSheet.create({
  card: {
    flex: 1,
    borderRadius: 16,
    padding: 16,
    alignItems: "center",
    borderWidth: 1,
    shadowOpacity: 0.15,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
  value: {
    fontSize: 32,
    fontWeight: "800",
    marginBottom: 4,
  },
  label: {
    fontSize: 11,
    color: Colors.text.secondary,
    fontWeight: "500",
  },
});

export default function HomeScreen() {
  const nav = useNavigation<Nav>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;
  const brandName = brand?.activeBrand?.name || "Mon Restaurant";
  const initial = brandName.charAt(0).toUpperCase();

  const [kbScore, setKbScore] = useState(0);
  const [proposals, setProposals] = useState<AIProposal[]>([]);
  const [briefAnswered, setBriefAnswered] = useState(false);
  const [stats, setStats] = useState({ pending: 0, approved: 0, published: 0 });
  const [refreshing, setRefreshing] = useState(false);
  const [socialConnected, setSocialConnected] = useState<number | null>(null);
  const [videoCredits, setVideoCredits] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    if (!brandId) return;
    try {
      const [kbRes, propRes, briefRes, socialRes, videoRes] = await Promise.allSettled([
        kbApi.completeness(brandId),
        proposalsApi.list(brandId),
        briefApi.getToday(brandId),
        socialApi.accounts(brandId),
        videoApi.credits(brandId),
      ]);
      if (kbRes.status === "fulfilled") {
        setKbScore(kbRes.value.data.completeness_score ?? 0);
      }
      if (propRes.status === "fulfilled") {
        const list = propRes.value.data.proposals || propRes.value.data || [];
        setProposals(list.slice(0, 5));
        setStats({
          pending: list.filter((p: AIProposal) => p.status === "pending").length,
          approved: list.filter((p: AIProposal) => p.status === "approved").length,
          published: list.filter((p: AIProposal) => p.status === "published").length,
        });
      }
      if (briefRes.status === "fulfilled") {
        setBriefAnswered(briefRes.value.data.status === "answered");
      }
      if (socialRes.status === "fulfilled") {
        const accts = socialRes.value.data?.accounts || [];
        setSocialConnected(accts.filter((a: any) => a.connected).length);
      }
      if (videoRes.status === "fulfilled") {
        setVideoCredits(videoRes.value.data.credits_remaining ?? 0);
      }
    } catch {
      // silent
    }
  }, [brandId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, [loadData]);

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.brand.primary} />
        }
      >
        {/* Header gradient */}
        <LinearGradient colors={["#F8F7FF", "#F0EEFF"]} style={styles.header}>
          <View style={styles.headerTop}>
            <View>
              <Text style={styles.greeting}>{FR.home_greeting} 👋</Text>
              <Text style={styles.restaurantName}>{brandName}</Text>
            </View>
            <View style={styles.headerActions}>
              <TouchableOpacity
                style={styles.socialBtn}
                onPress={() => nav.navigate("SocialAccounts")}
                activeOpacity={0.7}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={styles.socialBtnIcon}>🔗</Text>
                {socialConnected === 0 && (
                  <View pointerEvents="none" style={styles.socialBadge} />
                )}
              </TouchableOpacity>
              <View style={styles.avatar}>
                <Text style={styles.avatarInitial}>{initial}</Text>
              </View>
            </View>
          </View>

          <KBCompletenessBar
            score={kbScore}
            onPress={() => nav.getParent()?.navigate("Files" as never)}
          />
        </LinearGradient>

        {/* Stats */}
        <View style={styles.statsRow}>
          <StatCard label={FR.home_stats_pending} value={stats.pending} color={Colors.brand.amber} />
          <StatCard label={FR.home_stats_approved} value={stats.approved} color={Colors.brand.primary} />
          <StatCard label={FR.home_stats_published} value={stats.published} color="#10B981" />
        </View>

        {/* Video IA card */}
        <TouchableOpacity
          style={styles.videoCard}
          onPress={() => nav.getParent()?.navigate("Video" as never)}
          activeOpacity={0.85}
        >
          <LinearGradient
            colors={[Colors.brand.primary, Colors.brand.amber]}
            style={styles.videoGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <View style={styles.videoLeft}>
              <Text style={styles.videoEmoji}>🎬</Text>
              <View>
                <Text style={styles.videoTitle}>{FR.home_video_title}</Text>
                <Text style={styles.videoBody}>{FR.home_video_body}</Text>
              </View>
            </View>
            {videoCredits !== null && (
              <View style={styles.videoCreditsBadge}>
                <Text style={styles.videoCreditsValue}>{videoCredits}</Text>
                <Text style={styles.videoCreditsLabel}>{FR.video_credits}</Text>
              </View>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Brief du matin */}
        {!briefAnswered && (
          <TouchableOpacity
            style={styles.briefCard}
            onPress={() => nav.navigate("Brief")}
            activeOpacity={0.85}
          >
            <LinearGradient
              colors={[...Colors.gradient.hero]}
              style={styles.briefGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Text style={styles.briefEmoji}>☀️</Text>
              <View style={styles.briefTextWrap}>
                <Text style={styles.briefTitle}>{FR.home_brief_title}</Text>
                <Text style={styles.briefSubtitle}>
                  {FR.home_brief_subtitle} — {FR.home_brief_body}
                </Text>
              </View>
              <Text style={styles.briefArrow}>→</Text>
            </LinearGradient>
          </TouchableOpacity>
        )}

        {/* Recent proposals */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>{FR.home_recent_title}</Text>
          {proposals.length > 0 && (
            <TouchableOpacity onPress={() => nav.getParent()?.navigate("Proposals" as never)}>
              <Text style={styles.seeAll}>{FR.home_see_all}</Text>
            </TouchableOpacity>
          )}
        </View>

        {proposals.length === 0 ? (
          <View style={styles.emptyWrap}>
            <EmptyStateCard
              emoji="🤖"
              title={FR.proposals_empty_title}
              body={FR.home_no_proposals}
              ctaLabel={FR.home_no_proposals_cta}
              onCta={() => nav.getParent()?.navigate("Files" as never)}
            />
          </View>
        ) : (
          <View style={styles.proposalList}>
            {proposals.map((p) => (
              <ProposalCard key={p.id} proposal={p} onPress={() => (nav.getParent()?.navigate as any)("Proposals", { screen: "ProposalDetail", params: { proposalId: p.id } })} />
            ))}
          </View>
        )}

        <View style={styles.bottomSpacer} />
      </ScrollView>

      {/* FAB */}
      <TouchableOpacity
        style={styles.fab}
        onPress={() => nav.getParent()?.navigate("Files" as never)}
        activeOpacity={0.8}
      >
        <LinearGradient
          colors={[Colors.brand.primary, "#9D7FD8"]}
          style={styles.fabGradient}
        >
          <Text style={styles.fabIcon}>+</Text>
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bg.primary
  },
  scroll: {
    flex: 1,
    backgroundColor: Colors.bg.primary
  },
  header: {
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 24
  },
  headerTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 20
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10
  },
  socialBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.bg.elevated,
    justifyContent: "center",
    alignItems: "center"
  },
  socialBtnIcon: {
    fontSize: 18
  },
  socialBadge: {
    position: "absolute",
    top: 4,
    right: 4,
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: Colors.brand.primary,
    borderWidth: 2,
    borderColor: Colors.bg.elevated
  },
  greeting: {
    fontSize: 14,
    color: Colors.text.secondary,
    fontWeight: "500"
  },
  restaurantName: {
    fontSize: 32,
    color: Colors.text.primary,
    fontWeight: "800",
    letterSpacing: -0.5,
    marginTop: 4,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.brand.primary,
    justifyContent: "center",
    alignItems: "center"
  },
  avatarInitial: {
    color: "#FFF",
    fontSize: 18,
    fontWeight: "700"
  },
  statsRow: {
    flexDirection: "row",
    gap: 12,
    marginHorizontal: 16,
    marginTop: 20,
    marginBottom: 16
  },
  videoCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    overflow: "hidden",
    shadowColor: Colors.brand.primary,
    shadowOpacity: 0.3,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  videoGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 20
  },
  videoLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    flex: 1
  },
  videoEmoji: {
    fontSize: 32
  },
  videoTitle: {
    fontSize: 17,
    color: "#FFF",
    fontWeight: "700"
  },
  videoBody: {
    fontSize: 12,
    color: "rgba(255,255,255,0.8)",
    marginTop: 2
  },
  videoCreditsBadge: {
    alignItems: "center",
    backgroundColor: "rgba(255,255,255,0.2)",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.3)",
  },
  videoCreditsValue: {
    fontSize: 20,
    fontWeight: "800",
    color: "#FFF"
  },
  videoCreditsLabel: {
    fontSize: 9,
    color: "rgba(255,255,255,0.8)",
    fontWeight: "600",
    textTransform: "uppercase",
  },
  briefCard: {
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    overflow: "hidden",
    shadowColor: Colors.brand.primary,
    shadowOpacity: 0.3,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8
  },
  briefGradient: {
    flexDirection: "row",
    alignItems: "center",
    padding: 20,
    gap: 16
  },
  briefEmoji: {
    fontSize: 28
  },
  briefTextWrap: {
    flex: 1
  },
  briefTitle: {
    fontSize: 18,
    color: "#FFF",
    fontWeight: "700"
  },
  briefSubtitle: {
    fontSize: 13,
    color: "rgba(255,255,255,0.8)",
    marginTop: 2
  },
  briefArrow: {
    fontSize: 24,
    color: "#FFF"
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginHorizontal: 16,
    marginBottom: 12,
    marginTop: 8,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary
  },
  seeAll: {
    fontSize: 13,
    color: Colors.brand.primary,
    fontWeight: "600"
  },
  emptyWrap: {
    marginHorizontal: 16
  },
  proposalList: {
    paddingHorizontal: 16,
    gap: 12
  },
  bottomSpacer: {
    height: 100
  },
  fab: {
    position: "absolute",
    bottom: 24,
    right: 20,
    width: 60,
    height: 60,
    borderRadius: 30,
    shadowColor: Colors.brand.primary,
    shadowOpacity: 0.4,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 4 },
    elevation: 12,
    overflow: "hidden",
  },
  fabGradient: {
    width: 60,
    height: 60,
    borderRadius: 30,
    justifyContent: "center",
    alignItems: "center",
  },
  fabIcon: {
    fontSize: 32,
    color: "#FFF",
    fontWeight: "300",
    lineHeight: 32,
  },
});
