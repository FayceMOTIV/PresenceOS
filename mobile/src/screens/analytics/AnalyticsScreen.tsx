// PresenceOS Mobile — Analytics Screen
// Shows content performance, AI insights, upcoming events

import React, { useCallback, useContext, useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { BrandContext } from "@/contexts/BrandContext";
import { brainApi } from "@/lib/api";
import type { AnalyticsOverview, CalendarEvent } from "@/types/brain";

export default function AnalyticsScreen() {
  const brandCtx = useContext(BrandContext);
  const activeBrand = brandCtx?.activeBrand ?? null;
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    if (!activeBrand) return;
    try {
      const [analyticsRes, eventsRes] = await Promise.allSettled([
        brainApi.analytics(activeBrand.id),
        brainApi.calendarEvents(activeBrand.id),
      ]);
      if (analyticsRes.status === "fulfilled") setAnalytics(analyticsRes.value.data);
      if (eventsRes.status === "fulfilled") {
        const d = eventsRes.value.data;
        setEvents(d.events ?? d ?? []);
      }
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
    } finally {
      setLoading(false);
    }
  }, [activeBrand]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

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
        <Text style={styles.title}>Analytics</Text>
        <Text style={styles.subtitle}>Performance de votre contenu</Text>

        {/* KPI Cards */}
        {analytics && (
          <>
            <View style={styles.kpiGrid}>
              <View style={styles.kpiCard}>
                <Ionicons name="document-text" size={20} color={Colors.brand.primary} />
                <Text style={styles.kpiValue}>{analytics.total_posts}</Text>
                <Text style={styles.kpiLabel}>Posts</Text>
              </View>
              <View style={styles.kpiCard}>
                <Ionicons name="heart" size={20} color={Colors.status.danger} />
                <Text style={styles.kpiValue}>{analytics.total_engagement}</Text>
                <Text style={styles.kpiLabel}>Engagements</Text>
              </View>
              <View style={styles.kpiCard}>
                <Ionicons name="trending-up" size={20} color={Colors.status.success} />
                <Text style={styles.kpiValue}>{(analytics.avg_engagement_rate ?? 0).toFixed(1)}%</Text>
                <Text style={styles.kpiLabel}>Taux moy.</Text>
              </View>
            </View>

            {/* Best performing info */}
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Ionicons name="trophy" size={20} color={Colors.brand.amber} />
                <Text style={styles.cardTitle}>Meilleure performance</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Type de contenu</Text>
                <Text style={styles.infoValue}>{analytics.best_performing_type}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Meilleur jour</Text>
                <Text style={styles.infoValue}>{analytics.best_day}</Text>
              </View>
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Meilleure heure</Text>
                <Text style={styles.infoValue}>{analytics.best_time}</Text>
              </View>
              <View style={[styles.infoRow, { borderBottomWidth: 0 }]}>
                <Text style={styles.infoLabel}>Tendance</Text>
                <Text
                  style={[
                    styles.infoValue,
                    {
                      color:
                        analytics.growth_trend === "up"
                          ? Colors.status.success
                          : analytics.growth_trend === "down"
                          ? Colors.status.danger
                          : Colors.text.secondary,
                    },
                  ]}
                >
                  {analytics.growth_trend === "up"
                    ? "↑ En hausse"
                    : analytics.growth_trend === "down"
                    ? "↓ En baisse"
                    : "→ Stable"}
                </Text>
              </View>
            </View>

            {/* AI Insights */}
            {analytics.ai_insights.length > 0 && (
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Ionicons name="bulb" size={20} color={Colors.brand.amber} />
                  <Text style={styles.cardTitle}>Insights IA</Text>
                </View>
                {analytics.ai_insights.map((insight, i) => (
                  <View key={i} style={styles.insightRow}>
                    <View style={styles.insightDot} />
                    <Text style={styles.insightText}>{insight}</Text>
                  </View>
                ))}
              </View>
            )}

            {/* Recommendations */}
            {analytics.recommendations.length > 0 && (
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Ionicons name="rocket" size={20} color={Colors.brand.primary} />
                  <Text style={styles.cardTitle}>Recommandations</Text>
                </View>
                {analytics.recommendations.map((rec, i) => (
                  <View key={i} style={styles.insightRow}>
                    <Text style={styles.recNumber}>{i + 1}.</Text>
                    <Text style={styles.insightText}>{rec}</Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}

        {/* Upcoming Calendar Events */}
        {events.length > 0 && (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Ionicons name="calendar" size={20} color={Colors.brand.primary} />
              <Text style={styles.cardTitle}>Événements à venir</Text>
            </View>
            {events.map((event, i) => (
              <View key={i} style={styles.eventItem}>
                <View style={styles.eventDate}>
                  <Text style={styles.eventDay}>
                    {new Date(event.date).getDate()}
                  </Text>
                  <Text style={styles.eventMonth}>
                    {new Date(event.date).toLocaleDateString("fr-FR", { month: "short" })}
                  </Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.eventName}>{event.name}</Text>
                  <View style={styles.eventPriority}>
                    <View
                      style={[
                        styles.priorityDot,
                        {
                          backgroundColor:
                            event.priority === "high"
                              ? Colors.status.danger
                              : event.priority === "medium"
                              ? Colors.status.warning
                              : Colors.status.success,
                        },
                      ]}
                    />
                    <Text style={styles.priorityText}>
                      {event.priority === "high"
                        ? "Haute priorité"
                        : event.priority === "medium"
                        ? "Moyenne"
                        : "Basse"}
                    </Text>
                  </View>
                  {event.content_ideas.length > 0 && (
                    <Text style={styles.eventIdeas} numberOfLines={2}>
                      Idées : {event.content_ideas.join(", ")}
                    </Text>
                  )}
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
  kpiGrid: {
    flexDirection: "row",
    gap: 10,
    marginBottom: 16,
  },
  kpiCard: {
    flex: 1,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    padding: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  kpiValue: {
    fontSize: 22,
    fontWeight: "800",
    color: Colors.text.primary,
    marginTop: 6,
  },
  kpiLabel: {
    fontSize: 11,
    color: Colors.text.muted,
    marginTop: 2,
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
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  infoLabel: {
    fontSize: 14,
    color: Colors.text.secondary,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.primary,
  },
  insightRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 8,
    paddingVertical: 6,
  },
  insightDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.brand.amber,
    marginTop: 6,
  },
  insightText: {
    flex: 1,
    fontSize: 13,
    color: Colors.text.primary,
    lineHeight: 19,
  },
  recNumber: {
    fontSize: 13,
    fontWeight: "700",
    color: Colors.brand.primary,
  },
  eventItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  eventDate: {
    width: 44,
    height: 44,
    borderRadius: 10,
    backgroundColor: Colors.brand.glow,
    alignItems: "center",
    justifyContent: "center",
  },
  eventDay: {
    fontSize: 16,
    fontWeight: "800",
    color: Colors.brand.primary,
    lineHeight: 18,
  },
  eventMonth: {
    fontSize: 10,
    color: Colors.brand.primary,
    textTransform: "uppercase",
  },
  eventName: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.primary,
  },
  eventPriority: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: 2,
  },
  priorityDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  priorityText: {
    fontSize: 11,
    color: Colors.text.muted,
  },
  eventIdeas: {
    fontSize: 12,
    color: Colors.text.secondary,
    marginTop: 4,
    fontStyle: "italic",
  },
});
