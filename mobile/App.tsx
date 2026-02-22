// PresenceOS Mobile — Root Entry Point

// Polyfill URL before anything else (fixes Hermes URL.protocol read-only issue)
import "react-native-url-polyfill/auto";

import React, { useEffect, useState } from "react";
import { ActivityIndicator, View, Text } from "react-native";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { NavigationContainer } from "@react-navigation/native";
import * as SecureStore from "expo-secure-store";
import TabNavigator from "@/navigation/TabNavigator";
import { Brand } from "@/types";
import { AuthContext, BrandContext } from "@/contexts/BrandContext";

// Re-export so any remaining imports from App still work
export { AuthContext, BrandContext };

const API_BASE = __DEV__
  ? "http://192.168.10.114:8000/api/v1"
  : "https://rs3-api-production.up.railway.app/api/v1";

// ── Mock brand for local dev (auth disabled) ──
const MOCK_BRAND: Brand = {
  id: "00000000-0000-0000-0000-000000000001",
  name: "Mon Restaurant",
  slug: "mon-restaurant",
  brand_type: "restaurant",
  description: "Restaurant de test",
  logo_url: undefined,
};

// ── Auto-login: get JWT + real brands from production API ──
async function ensureAuth(): Promise<{ token: string; brands: Brand[] }> {
  // 1. Check for existing token
  let token: string | null = null;
  try {
    token = await SecureStore.getItemAsync("auth_token");
  } catch {}

  let workspaceId: string | null = null;
  try {
    workspaceId = await SecureStore.getItemAsync("workspace_id");
  } catch {}

  // 2. If no token, login with test credentials
  if (!token) {
    const loginBody = `username=${encodeURIComponent("test@presenceos.dev")}&password=${encodeURIComponent("Test123pass")}`;
    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: loginBody,
    });

    if (!loginRes.ok) {
      const err = await loginRes.text();
      throw new Error(`Login failed (${loginRes.status}): ${err}`);
    }

    const loginData = await loginRes.json();
    token = loginData.token.access_token;
    await SecureStore.setItemAsync("auth_token", token!);

    // Store refresh token for later
    if (loginData.token.refresh_token) {
      await SecureStore.setItemAsync("refresh_token", loginData.token.refresh_token);
    }

    // Extract workspace ID from login response
    if (loginData.workspaces && loginData.workspaces.length > 0) {
      workspaceId = loginData.workspaces[0].id;
      await SecureStore.setItemAsync("workspace_id", workspaceId!);
    }
  }

  // 3. Fetch brands from API
  if (!workspaceId) {
    throw new Error("No workspace available");
  }

  const brandsRes = await fetch(`${API_BASE}/workspaces/${workspaceId}/brands`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!brandsRes.ok) {
    // Token might be expired — clear and retry once
    await SecureStore.deleteItemAsync("auth_token");
    await SecureStore.deleteItemAsync("workspace_id");
    throw new Error("RETRY");
  }

  const brandsData: any[] = await brandsRes.json();
  const brands: Brand[] = brandsData.map((b: any) => ({
    id: b.id,
    name: b.name,
    slug: b.slug,
    brand_type: b.brand_type,
    description: b.description ?? undefined,
    logo_url: b.logo_url ?? undefined,
  }));

  return { token: token!, brands };
}

export default function App() {
  const [brands, setBrands] = useState<Brand[]>([]);
  const [activeBrand, setActiveBrand] = useState<Brand | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      // In dev mode, skip auto-login (use mock brand + dev-token)
      if (__DEV__) {
        setBrands([MOCK_BRAND]);
        setActiveBrand(MOCK_BRAND);
        setIsLoading(false);
        return;
      }

      // Production (TestFlight): auto-login + fetch real brands
      let retries = 0;
      while (retries < 2) {
        try {
          const result = await ensureAuth();
          if (cancelled) return;

          if (result.brands.length === 0) {
            setError("Aucune marque trouvee");
            setIsLoading(false);
            return;
          }

          setBrands(result.brands);
          setActiveBrand(result.brands[0]);
          setIsLoading(false);
          return;
        } catch (err: any) {
          if (err.message === "RETRY" && retries === 0) {
            retries++;
            continue;
          }
          if (cancelled) return;
          console.error("Auth init failed:", err);
          setError(err.message || "Erreur d'authentification");
          setIsLoading(false);
          return;
        }
      }
    }

    init();
    return () => { cancelled = true; };
  }, []);

  const brandCtx = {
    activeBrand,
    brands,
    switchBrand: (id: string) => {
      const found = brands.find((b) => b.id === id);
      if (found) setActiveBrand(found);
    },
    isLoading,
  };

  // Loading screen
  if (isLoading) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0A0A0F" }}>
          <ActivityIndicator size="large" color="#8B5CF6" />
          <Text style={{ color: "#fff", marginTop: 16, fontSize: 16 }}>Chargement...</Text>
        </View>
      </GestureHandlerRootView>
    );
  }

  // Error screen
  if (error) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0A0A0F", padding: 24 }}>
          <Text style={{ color: "#EF4444", fontSize: 18, fontWeight: "600", marginBottom: 8 }}>Erreur</Text>
          <Text style={{ color: "#9CA3AF", fontSize: 14, textAlign: "center" }}>{error}</Text>
        </View>
      </GestureHandlerRootView>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <NavigationContainer>
          <StatusBar style="light" />
          <BrandContext.Provider value={brandCtx}>
            <TabNavigator />
          </BrandContext.Provider>
        </NavigationContainer>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
