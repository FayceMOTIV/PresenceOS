// PresenceOS Mobile — Social Accounts Screen (Upload-Post integration)

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
} from "react-native";
import * as WebBrowser from "expo-web-browser";
import * as Linking from "expo-linking";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { socialApi } from "@/lib/api";

interface SocialAccount {
  platform: string;
  username?: string;
  display_name?: string;
  connected: boolean;
  avatar_url?: string;
  reauth_required?: boolean;
}

const PLATFORMS = [
  {
    key: "instagram",
    label: "Instagram",
    icon: "logo-instagram" as const,
    color: "#E1306C",
    gradient: ["#E1306C", "#F77737"] as const,
  },
  {
    key: "facebook",
    label: "Facebook",
    icon: "logo-facebook" as const,
    color: "#1877F2",
    gradient: ["#1877F2", "#1877F2"] as const,
  },
  {
    key: "tiktok",
    label: "TikTok",
    icon: "logo-tiktok" as const,
    color: "#00F2EA",
    gradient: ["#00F2EA", "#00F2EA"] as const,
  },
];

// Deep link callback URL for OAuth redirect
const REDIRECT_URL = Linking.createURL("social-callback");

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

      // Merge API response with our platform list
      const merged = PLATFORMS.map((p) => {
        const match = raw.find(
          (a) => a.platform?.toLowerCase() === p.key
        );
        if (match && match.connected) {
          return {
            platform: p.key,
            username: match.username || match.display_name || undefined,
            avatar_url: match.avatar_url,
            connected: true,
          };
        }
        return { platform: p.key, connected: false };
      });
      setAccounts(merged);
    } catch {
      setAccounts(
        PLATFORMS.map((p) => ({ platform: p.key, connected: false }))
      );
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
      if (
        appState.current.match(/inactive|background/) &&
        nextState === "active"
      ) {
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

  /**
   * Connect a specific platform via OAuth.
   * Uses openAuthSessionAsync so the browser dismisses automatically on redirect.
   * Retries fetchAccounts with a delay to allow Upload-Post sync.
   */
  const handleConnect = async (platform: string) => {
    if (!brandId) return;
    setConnectingPlatform(platform);
    try {
      const res = await socialApi.linkUrl(brandId, platform, REDIRECT_URL);
      const url = res.data?.url;
      if (!url) {
        Alert.alert("Erreur", "Impossible de generer le lien de connexion.");
        return;
      }

      // openAuthSessionAsync auto-dismisses when redirect matches our scheme
      const result = await WebBrowser.openAuthSessionAsync(url, REDIRECT_URL);

      if (result.type === "success" || result.type === "dismiss") {
        // Give Upload-Post a moment to sync the connection
        await new Promise((r) => setTimeout(r, 1500));
        await fetchAccounts();
        // Retry once more after another delay in case sync is slow
        await new Promise((r) => setTimeout(r, 3000));
        await fetchAccounts();
      }
    } catch (err: any) {
      Alert.alert(
        "Erreur",
        err?.response?.data?.detail || "Connexion impossible."
      );
    } finally {
      setConnectingPlatform(null);
    }
  };

  /** Connect all platforms at once (global CTA button) */
  const handleConnectAll = async () => {
    if (!brandId) return;
    setConnectingPlatform("all");
    try {
      // No platform param = all platforms
      const res = await socialApi.linkUrl(brandId, undefined, REDIRECT_URL);
      const url = res.data?.url;
      if (!url) {
        Alert.alert("Erreur", "Impossible de generer le lien de connexion.");
        return;
      }

      const result = await WebBrowser.openAuthSessionAsync(url, REDIRECT_URL);

      if (result.type === "success" || result.type === "dismiss") {
        await new Promise((r) => setTimeout(r, 1500));
        await fetchAccounts();
        await new Promise((r) => setTimeout(r, 3000));
        await fetchAccounts();
      }
    } catch (err: any) {
      Alert.alert(
        "Erreur",
        err?.response?.data?.detail || "Connexion impossible."
      );
    } finally {
      setConnectingPlatform(null);
    }
  };

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
          <Ionicons
            name={item.icon}
            size={28}
            color={isTikTok ? "#000" : "#FFF"}
          />
        </LinearGradient>
        <View style={styles.platformInfo}>
          <Text style={styles.platformName}>{item.label}</Text>
          {connected && account?.username ? (
            <Text style={[styles.username, { color: item.color }]}>
              @{account.username}
            </Text>
          ) : (
            <Text style={styles.disconnected}>Non connecte</Text>
          )}
        </View>
        {connected ? (
          <View style={styles.connectedBadge}>
            <Ionicons name="checkmark-circle" size={22} color={Colors.status.success} />
            <Text style={styles.connectedText}>Connecte</Text>
          </View>
        ) : (
          <TouchableOpacity
            style={[
              styles.connectBtn,
              {
                backgroundColor: item.color + "20",
                borderColor: item.color + "50"
              }
            ]}
            onPress={() => handleConnect(item.key)}
            disabled={connectingPlatform !== null}
          >
            {isConnecting ? (
              <ActivityIndicator size="small" color={item.color} />
            ) : (
              <Text style={[styles.connectBtnText, { color: item.color }]}>
                Connecter
              </Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    );
  };

  const isConnectingAny = connectingPlatform !== null;

  return (
    <SafeAreaView style={styles.safe} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()} style={styles.backBtn}>
          <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Mes reseaux sociaux</Text>
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
            <View style={styles.ctaSection}>
              <TouchableOpacity
                onPress={handleConnectAll}
                disabled={isConnectingAny}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={[Colors.brand.primary, Colors.brand.amber]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.mainConnectBtn}
                >
                  {connectingPlatform === "all" ? (
                    <ActivityIndicator size="small" color="#FFF" />
                  ) : (
                    <>
                      <Ionicons name="link" size={20} color="#FFF" />
                      <Text style={styles.mainConnectText}>
                        Connecter mes reseaux
                      </Text>
                    </>
                  )}
                </LinearGradient>
              </TouchableOpacity>
              <Text style={styles.ctaHint}>
                Ouvre une page securisee pour lier vos comptes Instagram,
                Facebook et TikTok.
              </Text>
            </View>
          }
          ListFooterComponent={
            accounts.every((a) => !a.connected) ? (
              <View style={styles.emptyFooter}>
                <Ionicons name="information-circle-outline" size={20} color={Colors.text.secondary} />
                <Text style={styles.emptyFooterText}>
                  Aucun reseau connecte. Appuyez sur "Connecter" pour lier chaque compte individuellement.
                </Text>
              </View>
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

  // CTA Section
  ctaSection: { marginTop: 24, marginBottom: 32, alignItems: "center" },
  mainConnectBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 16,
    width: "100%",
  },
  mainConnectText: {
    color: "#FFF",
    fontSize: 16,
    fontWeight: "700",
  },
  ctaHint: {
    color: Colors.text.secondary,
    fontSize: 13,
    textAlign: "center",
    marginTop: 12,
    lineHeight: 18,
  },

  // Platform Card
  platformCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
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
  username: {
    fontSize: 13,
    fontWeight: "600",
    marginTop: 2,
  },
  disconnected: {
    fontSize: 13,
    color: Colors.text.muted,
    marginTop: 2,
  },
  connectedBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  connectedText: {
    fontSize: 13,
    color: Colors.status.success,
    fontWeight: "600",
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

  // Empty footer
  emptyFooter: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 12,
    padding: 16,
    marginTop: 8,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  emptyFooterText: {
    flex: 1,
    fontSize: 13,
    color: Colors.text.secondary,
    lineHeight: 18,
  },
});
