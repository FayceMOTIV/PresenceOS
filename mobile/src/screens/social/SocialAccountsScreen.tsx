// PresenceOS Mobile — Social Accounts Screen (Late / getlate.dev integration)

import React, { useContext, useState, useEffect, useCallback, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  RefreshControl,
  AppState,
  ActivityIndicator,
  Alert,
  Image,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { socialApi } from "@/lib/api";
import { openOAuthSession, buildRedirectUrl } from "@/lib/deepLinking";

interface SocialAccount {
  platform: string;
  username?: string;
  display_name?: string;
  connected: boolean;
  avatar_url?: string;
  account_id?: string;
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
    key: "twitter",
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

export default function SocialAccountsScreen() {
  const nav = useNavigation();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connectingPlatform, setConnectingPlatform] = useState<string | null>(null);
  const appState = useRef(AppState.currentState);

  const fetchAccounts = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await socialApi.accounts(brandId);
      const raw: SocialAccount[] = res.data?.accounts || [];
      // Merge with platform list to show all platforms
      const merged = PLATFORMS.map((p) => {
        const match = raw.find((a) => a.platform?.toLowerCase() === p.key);
        if (match && match.connected) {
          return {
            platform: p.key,
            username: match.username || match.display_name || undefined,
            display_name: match.display_name,
            avatar_url: match.avatar_url,
            account_id: match.account_id,
            connected: true,
          };
        }
        return { platform: p.key, connected: false };
      });
      setAccounts(merged);
    } catch {
      setAccounts(PLATFORMS.map((p) => ({ platform: p.key, connected: false })));
    } finally {
      setLoading(false);
    }
  }, [brandId]);

  useEffect(() => {
    fetchAccounts();
  }, [fetchAccounts]);

  // Auto-refresh when app returns to foreground (after OAuth flow)
  useEffect(() => {
    const sub = AppState.addEventListener("change", (nextState) => {
      if (appState.current.match(/inactive|background/) && nextState === "active") {
        fetchAccounts();
      }
      appState.current = nextState;
    });
    return () => sub.remove();
  }, [fetchAccounts]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchAccounts();
    setRefreshing(false);
  }, [fetchAccounts]);

  const handleConnect = async (platform: string) => {
    if (!brandId) return;
    setConnectingPlatform(platform);
    try {
      const redirectUrl = buildRedirectUrl("social-callback");
      const res = await socialApi.connectUrl(brandId, platform, redirectUrl);
      const url = res.data?.url;
      if (!url) {
        Alert.alert("Erreur", "Impossible de generer le lien de connexion.");
        return;
      }

      const result = await openOAuthSession(url, redirectUrl);

      if (result.success) {
        // Give Late a moment to sync the account
        await new Promise((r) => setTimeout(r, 2000));
        await fetchAccounts();
        // Retry for slow sync
        await new Promise((r) => setTimeout(r, 3000));
        await fetchAccounts();
      }
    } catch (err: any) {
      Alert.alert(
        "Erreur",
        err?.response?.data?.detail || "Connexion impossible. Reessaie."
      );
    } finally {
      setConnectingPlatform(null);
    }
  };

  const handleDisconnect = async (platform: string, accountId?: string) => {
    if (!brandId || !accountId) return;
    Alert.alert(
      "Deconnecter",
      `Deconnecter ${platform} ?`,
      [
        { text: "Annuler", style: "cancel" },
        {
          text: "Deconnecter",
          style: "destructive",
          onPress: async () => {
            try {
              await socialApi.disconnect(brandId, accountId);
              await fetchAccounts();
            } catch {
              Alert.alert("Erreur", "Impossible de deconnecter.");
            }
          },
        },
      ]
    );
  };

  const connectedCount = accounts.filter((a) => a.connected).length;

  const renderPlatform = ({ item }: { item: (typeof PLATFORMS)[0] }) => {
    const account = accounts.find((a) => a.platform === item.key);
    const connected = account?.connected || false;
    const isTikTok = item.key === "tiktok";
    const isConnecting = connectingPlatform === item.key;

    return (
      <View style={styles.platformCard}>
        <LinearGradient
          colors={item.gradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.iconWrap}
        >
          {connected && account?.avatar_url ? (
            <Image source={{ uri: account.avatar_url }} style={styles.avatar} />
          ) : (
            <Ionicons name={item.icon} size={26} color={isTikTok ? "#000" : "#FFF"} />
          )}
        </LinearGradient>

        <View style={styles.platformInfo}>
          <Text style={styles.platformName}>{item.label}</Text>
          {connected && account?.username ? (
            <Text style={[styles.accountName, { color: item.color }]}>
              @{account.username}
            </Text>
          ) : (
            <Text style={styles.disconnectedLabel}>Non connecte</Text>
          )}
        </View>

        {connected ? (
          <TouchableOpacity
            style={styles.connectedBadge}
            onPress={() => handleDisconnect(item.label, account?.account_id)}
            activeOpacity={0.7}
          >
            <Ionicons name="checkmark-circle" size={20} color={Colors.status.success} />
          </TouchableOpacity>
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
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Connecter mes reseaux</Text>
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
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.brand.primary} />
          }
          ListHeaderComponent={
            <View style={styles.statusSection}>
              <View style={styles.statusCard}>
                <Text style={styles.statusCount}>{connectedCount}</Text>
                <Text style={styles.statusLabel}>
                  {connectedCount === 0
                    ? "Aucun reseau connecte"
                    : connectedCount === 1
                      ? "reseau connecte"
                      : "reseaux connectes"}
                </Text>
              </View>
              <Text style={styles.hint}>
                Appuie sur "Connecter" pour lier chaque compte. Tu verras la page de connexion officielle de chaque plateforme.
              </Text>
            </View>
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
    overflow: "hidden",
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 14,
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
  connectedBadge: {
    flexDirection: "row",
    alignItems: "center",
    padding: 8,
  },
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
});
