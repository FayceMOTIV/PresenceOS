// PresenceOS Mobile — Connect Socials Screen (Headless Postiz OAuth)
// The user sees ONLY native Meta/TikTok/LinkedIn popups — never Postiz.

import React, { useState, useEffect, useCallback, useContext, useRef } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  Alert,
  StyleSheet,
  RefreshControl,
  AppState,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import type { HomeStackParams } from "@/navigation/TabNavigator";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { postizApi } from "@/lib/api";
import { openOAuthSession, buildRedirectUrl } from "@/lib/deepLinking";

interface PostizIntegration {
  id: string;
  name: string;
  identifier: string;
  picture?: string;
  disabled?: boolean;
}

const PLATFORMS = [
  {
    key: "instagram",
    label: "Instagram",
    icon: "logo-instagram" as const,
    color: "#E1306C",
    gradient: ["#E1306C", "#F77737"] as [string, string],
  },
  {
    key: "facebook",
    label: "Facebook",
    icon: "logo-facebook" as const,
    color: "#1877F2",
    gradient: ["#1877F2", "#4267B2"] as [string, string],
  },
  {
    key: "tiktok",
    label: "TikTok",
    icon: "logo-tiktok" as const,
    color: "#010101",
    gradient: ["#25F4EE", "#FE2C55"] as [string, string],
  },
  {
    key: "linkedin",
    label: "LinkedIn",
    icon: "logo-linkedin" as const,
    color: "#0A66C2",
    gradient: ["#0A66C2", "#0077B5"] as [string, string],
  },
  {
    key: "x",
    label: "X (Twitter)",
    icon: "logo-twitter" as const,
    color: "#1DA1F2",
    gradient: ["#1DA1F2", "#0D8BD9"] as [string, string],
  },
  {
    key: "youtube",
    label: "YouTube",
    icon: "logo-youtube" as const,
    color: "#FF0000",
    gradient: ["#FF0000", "#CC0000"] as [string, string],
  },
];

export default function ConnectSocialsScreen() {
  const nav = useNavigation<NativeStackNavigationProp<HomeStackParams>>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [integrations, setIntegrations] = useState<PostizIntegration[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null);
  const appState = useRef(AppState.currentState);

  const fetchIntegrations = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await postizApi.integrations(brandId);
      const list: PostizIntegration[] = Array.isArray(res.data) ? res.data : [];
      setIntegrations(list.filter((i) => !i.disabled));
    } catch {
      setIntegrations([]);
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchIntegrations();
  }, [fetchIntegrations]);

  // Auto-refresh when app returns to foreground (after OAuth flow)
  useEffect(() => {
    const sub = AppState.addEventListener("change", (nextState) => {
      if (appState.current.match(/inactive|background/) && nextState === "active") {
        fetchIntegrations();
      }
      appState.current = nextState;
    });
    return () => sub.remove();
  }, [fetchIntegrations]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchIntegrations();
    setRefreshing(false);
  }, [fetchIntegrations]);

  const handleConnect = async (platform: string) => {
    if (!brandId) return;
    setConnectingPlatform(platform);
    try {
      const res = await postizApi.getConnectUrl(brandId, platform);
      const connectUrl = res.data?.connect_url;
      if (!connectUrl) {
        Alert.alert("Erreur", "Impossible de générer le lien de connexion.");
        return;
      }

      // Opens native OAuth popup via expo-web-browser (user never sees Postiz)
      const redirectUrl = buildRedirectUrl("social-callback");
      const result = await openOAuthSession(connectUrl, redirectUrl);

      if (result.success) {
        // Give Postiz a moment to sync
        await new Promise((r) => setTimeout(r, 2000));
        await fetchIntegrations();
      }
    } catch (err: any) {
      Alert.alert(
        "Erreur",
        err?.response?.data?.detail || "Connexion impossible. Réessaie."
      );
    } finally {
      setConnectingPlatform(null);
    }
  };

  const handleDisconnect = (integrationId: string, platformLabel: string) => {
    Alert.alert(
      "Déconnecter",
      `Veux-tu déconnecter ${platformLabel} ?`,
      [
        { text: "Annuler", style: "cancel" },
        {
          text: "Déconnecter",
          style: "destructive",
          onPress: async () => {
            if (!brandId) return;
            try {
              await postizApi.disconnect(brandId, integrationId);
              await fetchIntegrations();
            } catch {
              Alert.alert("Erreur", "Impossible de déconnecter ce compte.");
            }
          },
        },
      ]
    );
  };

  const getConnectedIntegration = (platformKey: string): PostizIntegration | undefined =>
    integrations.find((i) => i.identifier?.toLowerCase() === platformKey);

  const connectedCount = PLATFORMS.filter((p) => getConnectedIntegration(p.key)).length;

  const renderPlatform = ({ item }: { item: (typeof PLATFORMS)[0] }) => {
    const integration = getConnectedIntegration(item.key);
    const connected = !!integration;
    const isConnecting = connectingPlatform === item.key;
    const isTikTok = item.key === "tiktok";

    return (
      <View style={styles.platformCard}>
        <LinearGradient
          colors={item.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.iconWrap}
        >
          <Ionicons
            name={item.icon}
            size={26}
            color={isTikTok ? "#000" : "#FFF"}
          />
        </LinearGradient>

        <View style={styles.platformInfo}>
          <Text style={styles.platformName}>{item.label}</Text>
          {connected && integration?.name ? (
            <Text style={[styles.accountName, { color: item.color }]}>
              {integration.name}
            </Text>
          ) : (
            <Text style={styles.disconnectedLabel}>Non connecté</Text>
          )}
        </View>

        {connected ? (
          <View style={styles.connectedActions}>
            <View style={styles.connectedBadge}>
              <Ionicons name="checkmark-circle" size={18} color={Colors.status.success} />
            </View>
            <TouchableOpacity
              style={styles.disconnectBtn}
              onPress={() => handleDisconnect(integration!.id, item.label)}
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            >
              <Ionicons name="close-circle-outline" size={20} color={Colors.text.muted} />
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity
            style={[styles.connectBtn, { backgroundColor: item.color + "15", borderColor: item.color + "40" }]}
            onPress={() => handleConnect(item.key)}
            disabled={connectingPlatform !== null}
            activeOpacity={0.7}
          >
            {isConnecting ? (
              <ActivityIndicator size="small" color={item.color} />
            ) : (
              <Text style={[styles.connectBtnText, { color: item.color }]}>Connecter</Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Connecter mes réseaux</Text>
        <View style={{ width: 40 }} />
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
        </View>
      ) : (
        <FlatList
          data={PLATFORMS}
          keyExtractor={(item) => item.key}
          renderItem={renderPlatform}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={Colors.brand.primary}
            />
          }
          ListHeaderComponent={
            <View style={styles.statusSection}>
              <View style={styles.statusCard}>
                <Text style={styles.statusCount}>{connectedCount}</Text>
                <Text style={styles.statusLabel}>
                  {connectedCount === 0
                    ? "Aucun réseau connecté"
                    : connectedCount === 1
                      ? "réseau connecté"
                      : "réseaux connectés"}
                </Text>
              </View>
              <Text style={styles.hint}>
                Appuie sur "Connecter" pour lier chaque compte. Tu verras la page de connexion officielle de chaque plateforme.
              </Text>
            </View>
          }
          ListFooterComponent={
            connectedCount > 0 ? (
              <TouchableOpacity
                style={styles.publishCta}
                onPress={() => nav.navigate("Publish")}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={[Colors.brand.primary, Colors.brand.amber]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.publishCtaGradient}
                >
                  <Ionicons name="paper-plane" size={18} color="#FFF" />
                  <Text style={styles.publishCtaText}>Publier un post</Text>
                </LinearGradient>
              </TouchableOpacity>
            ) : null
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg.primary },
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
  headerTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  center: { flex: 1, justifyContent: "center", alignItems: "center" },
  list: { paddingHorizontal: 16, paddingBottom: 40 },

  // Status section
  statusSection: { marginTop: 20, marginBottom: 24, alignItems: "center" },
  statusCard: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
    marginBottom: 12,
  },
  statusCount: {
    fontSize: 32,
    fontWeight: "800",
    color: Colors.brand.primary,
  },
  statusLabel: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text.secondary,
  },
  hint: {
    fontSize: 13,
    color: Colors.text.muted,
    textAlign: "center",
    lineHeight: 18,
    paddingHorizontal: 12,
  },

  // Platform card
  platformCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 16,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  iconWrap: {
    width: 48,
    height: 48,
    borderRadius: 14,
    justifyContent: "center",
    alignItems: "center",
  },
  platformInfo: { flex: 1, marginLeft: 14 },
  platformName: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.text.primary,
  },
  accountName: {
    fontSize: 13,
    fontWeight: "600",
    marginTop: 2,
  },
  disconnectedLabel: {
    fontSize: 13,
    color: Colors.text.muted,
    marginTop: 2,
  },

  // Connected state
  connectedActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  connectedBadge: {
    flexDirection: "row",
    alignItems: "center",
  },
  disconnectBtn: { padding: 4 },

  // Connect button
  connectBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
    minWidth: 90,
    alignItems: "center",
  },
  connectBtnText: {
    fontSize: 13,
    fontWeight: "600",
  },

  // Publish CTA
  publishCta: { marginTop: 20 },
  publishCtaGradient: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: 16,
    borderRadius: 14,
  },
  publishCtaText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#FFFFFF",
  },
});
