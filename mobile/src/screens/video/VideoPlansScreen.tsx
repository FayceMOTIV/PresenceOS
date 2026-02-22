// PresenceOS Mobile — Video Plans Screen (dark theme, French)

import React, { useContext, useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { videoApi } from "@/lib/api";

interface PlanOption {
  key: string;
  name: string;
  credits: number;
  videos: string;
  price: string;
  color: string;
  popular?: boolean;
}

const PLANS: PlanOption[] = [
  {
    key: "starter",
    name: FR.plans_starter,
    credits: 5,
    videos: "5 vidéos de 5s",
    price: "4,99€",
    color: Colors.status.info,
  },
  {
    key: "pro",
    name: FR.plans_pro,
    credits: 20,
    videos: "20 vidéos de 5s",
    price: "14,99€",
    color: Colors.brand.primary,
    popular: true,
  },
  {
    key: "studio",
    name: FR.plans_studio,
    credits: 50,
    videos: "50 vidéos de 5s",
    price: "34,99€",
    color: Colors.brand.amber,
  },
];

export default function VideoPlansScreen() {
  const nav = useNavigation();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [currentPlan, setCurrentPlan] = useState<string>("trial");
  const [creditsRemaining, setCreditsRemaining] = useState(0);

  useEffect(() => {
    if (!brandId) return;
    videoApi.credits(brandId).then((res) => {
      setCurrentPlan(res.data.plan);
      setCreditsRemaining(res.data.credits_remaining);
    }).catch(() => {});
  }, [brandId]);

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>{FR.plans_title}</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Current status */}
        <LinearGradient
          colors={["#1A2A4A", "#0F1923"]}
          style={styles.statusCard}
        >
          <Text style={styles.statusEmoji}>🎬</Text>
          <Text style={styles.statusCredits}>{creditsRemaining}</Text>
          <Text style={styles.statusLabel}>{FR.video_credits_remaining}</Text>
          <Text style={styles.statusPlan}>
            {FR.plans_current} : {currentPlan.toUpperCase()}
          </Text>
        </LinearGradient>

        {/* Pricing explanation */}
        <View style={styles.infoRow}>
          <Ionicons name="information-circle" size={18} color={Colors.text.secondary} />
          <Text style={styles.infoText}>{FR.plans_subtitle}</Text>
        </View>

        {/* Plan cards */}
        {PLANS.map((plan) => {
          const isCurrent = currentPlan === plan.key;

          return (
            <View
              key={plan.key}
              style={[
                styles.planCard,
                plan.popular && styles.planCardPopular,
                isCurrent && styles.planCardCurrent,
              ]}
            >
              {plan.popular && (
                <View style={styles.popularBadge}>
                  <Text style={styles.popularText}>POPULAIRE</Text>
                </View>
              )}

              <View style={styles.planHeader}>
                <View style={[styles.planDot, { backgroundColor: plan.color }]} />
                <Text style={styles.planName}>{plan.name}</Text>
              </View>

              <View style={styles.planBody}>
                <Text style={styles.planCredits}>{plan.credits}</Text>
                <Text style={styles.planCreditsLabel}>{FR.video_credits}</Text>
              </View>

              <Text style={styles.planVideos}>{plan.videos}</Text>

              <View style={styles.planFooter}>
                <Text style={styles.planPrice}>
                  {plan.price}
                  <Text style={styles.planPeriod}>{FR.plans_per_month}</Text>
                </Text>

                <TouchableOpacity
                  style={[
                    styles.planBtn,
                    isCurrent && styles.planBtnCurrent,
                  ]}
                  disabled={isCurrent}
                >
                  <Text
                    style={[
                      styles.planBtnText,
                      isCurrent && styles.planBtnTextCurrent,
                    ]}
                  >
                    {isCurrent ? FR.plans_current : FR.plans_choose}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* Fine print */}
        <View style={styles.finePrint}>
          <Text style={styles.finePrintItem}>• 2 crédits = 1 vidéo de 10 secondes</Text>
          <Text style={styles.finePrintItem}>• 3 crédits = 1 vidéo de 15 secondes</Text>
          <Text style={styles.finePrintItem}>• Les crédits se renouvellent chaque mois</Text>
          <Text style={styles.finePrintItem}>• Qualité cinématique IA (Kling 3.0)</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  backBtn: { padding: 8 },
  headerTitle: { fontSize: 18, fontWeight: "700", color: Colors.text.primary },
  scroll: { padding: 20, paddingBottom: 60 },

  statusCard: {
    alignItems: "center",
    borderRadius: 20,
    padding: 28,
    gap: 4,
    marginBottom: 20,
  },
  statusEmoji: { fontSize: 36, marginBottom: 8 },
  statusCredits: { fontSize: 48, fontWeight: "800", color: Colors.text.primary },
  statusLabel: { fontSize: 14, color: Colors.text.secondary, fontWeight: "500" },
  statusPlan: {
    fontSize: 12,
    color: Colors.brand.primary,
    fontWeight: "700",
    marginTop: 8,
    textTransform: "uppercase",
    letterSpacing: 1,
  },

  infoRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 20,
    paddingHorizontal: 4,
  },
  infoText: { fontSize: 13, color: Colors.text.secondary, fontWeight: "500" },

  planCard: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 20,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: Colors.border.default,
    position: "relative",
    overflow: "hidden",
  },
  planCardPopular: {
    borderColor: Colors.brand.primary + "60",
    borderWidth: 2,
  },
  planCardCurrent: {
    borderColor: Colors.status.success + "60",
  },
  popularBadge: {
    position: "absolute",
    top: 12,
    right: 12,
    backgroundColor: Colors.brand.glow,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 12,
  },
  popularText: {
    fontSize: 10,
    fontWeight: "800",
    color: Colors.brand.primary,
    letterSpacing: 0.5,
  },

  planHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  planDot: { width: 10, height: 10, borderRadius: 5 },
  planName: { fontSize: 16, fontWeight: "700", color: Colors.text.primary },

  planBody: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 4,
    marginBottom: 4,
  },
  planCredits: { fontSize: 32, fontWeight: "800", color: Colors.text.primary },
  planCreditsLabel: { fontSize: 14, color: Colors.text.secondary, fontWeight: "500" },
  planVideos: { fontSize: 13, color: Colors.text.muted, marginBottom: 16 },

  planFooter: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  planPrice: { fontSize: 20, fontWeight: "700", color: Colors.text.primary },
  planPeriod: { fontSize: 13, fontWeight: "500", color: Colors.text.secondary },
  planBtn: {
    backgroundColor: Colors.brand.primary,
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 12,
  },
  planBtnCurrent: { backgroundColor: Colors.status.successLight },
  planBtnText: { color: "#FFF", fontWeight: "700", fontSize: 14 },
  planBtnTextCurrent: { color: Colors.status.success },

  finePrint: {
    marginTop: 20,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    padding: 16,
    gap: 6,
  },
  finePrintItem: { fontSize: 13, color: Colors.text.secondary, lineHeight: 18 },
});
