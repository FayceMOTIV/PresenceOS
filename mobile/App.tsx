// PresenceOS Mobile — Root Entry Point

// Polyfill URL before anything else (fixes Hermes URL.protocol read-only issue)
import "react-native-url-polyfill/auto";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { ActivityIndicator, View, Text } from "react-native";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { NavigationContainer, createNavigationContainerRef } from "@react-navigation/native";
import { BottomSheetModalProvider } from "@gorhom/bottom-sheet";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import ErrorBoundary from "@/components/ErrorBoundary";
import TabNavigator from "@/navigation/TabNavigator";
import LoginScreen from "@/screens/auth/LoginScreen";
import RegisterScreen from "@/screens/auth/RegisterScreen";
import ForgotPasswordScreen from "@/screens/auth/ForgotPasswordScreen";
import WelcomeScreen from "@/screens/onboarding/WelcomeScreen";
import OnboardingChatScreen from "@/screens/onboarding/OnboardingChatScreen";
import ConnectAccountScreen from "@/screens/onboarding/ConnectAccountScreen";
import CompleteScreen from "@/screens/onboarding/CompleteScreen";
import { AuthContext, BrandContext, AuthContextType } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { deepLinkingConfig } from "@/lib/deepLinking";
import { useAuthStore } from "@/stores/authStore";
import { useBusinessStore } from "@/stores/businessStore";
import { useOnboardingStore } from "@/stores/onboardingStore";
import { addNotificationResponseListener, removeNotificationSubscriptions } from "@/lib/pushNotifications";
import { useOTAUpdate } from "@/hooks/useOTAUpdate";

// Navigation ref for programmatic navigation (e.g. from push notification taps)
export const navigationRef = createNavigationContainerRef<any>();

// Auth stack navigator (Login / Register / ForgotPassword)
const AuthStack = createNativeStackNavigator();

// Re-export so any remaining imports from App still work
export { AuthContext, BrandContext };

export default function App() {
  // OTA updates — check for JS updates on every app launch
  useOTAUpdate();

  // Firebase auth store
  const authStore = useAuthStore();
  const { isAuthenticated, isLoading: authLoading, isInitializing, user } = authStore;

  // Business store (PostgreSQL via backend API)
  const businessStore = useBusinessStore();
  const { brands, activeBrand, isLoading: bizLoading } = businessStore;

  // Onboarding
  const onboardingStore = useOnboardingStore();
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [onboardingStep, setOnboardingStep] = useState(0);

  // ── Initialize Firebase Auth listener ──
  useEffect(() => {
    const unsubscribe = authStore._initListener();
    return unsubscribe;
  }, []);

  // ── Fetch brands from backend when authenticated ──
  // Sprint 7: cancelled flag prevents stale updates on rapid auth changes
  // Sprint 7: checkCompleted now tries backend first (needs brandId from fetchBrands)
  useEffect(() => {
    if (isAuthenticated && user) {
      let cancelled = false;
      businessStore.fetchBrands().then(() => {
        if (cancelled) return;
        const brandId = useBusinessStore.getState().activeBrand?.id;
        onboardingStore.checkCompleted(brandId).then(() => {
          if (!cancelled) setOnboardingChecked(true);
        });
      });
      return () => { cancelled = true; };
    } else {
      businessStore.reset();
      setOnboardingChecked(false);
      setOnboardingStep(0);
    }
  }, [isAuthenticated, user?.uid]);

  // ── Push notification tap → navigate to CMChat ──
  useEffect(() => {
    const sub = addNotificationResponseListener((response) => {
      const data = response.notification.request.content.data as Record<string, string> | undefined;
      if (data?.screen === "CMChat" && navigationRef.isReady()) {
        (navigationRef as any).navigate("Inbox", {
          screen: "CMChat",
          params: { sessionId: data.sessionId },
        });
      }
    });
    return () => removeNotificationSubscriptions(sub);
  }, []);

  // ── Auth context bridging (Firebase → legacy AuthContextType) ──
  const handleLogin = useCallback(async (email: string, password: string) => {
    await authStore.login(email, password);
  }, []);

  const handleRegister = useCallback(async (email: string, password: string, fullName: string) => {
    await authStore.register(email, password, fullName);
  }, []);

  const handleLogout = useCallback(async () => {
    businessStore.reset();
    await authStore.logout();
  }, []);

  const handleResetPassword = useCallback(async (email: string) => {
    await authStore.resetPassword(email);
  }, []);

  const authCtx: AuthContextType = {
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    resetPassword: handleResetPassword,
  };

  const handleSwitchBrand = useCallback((id: string) => {
    businessStore.switchBusiness(id);
  }, []);

  const brandCtx = useMemo(() => ({
    activeBrand,
    brands,
    switchBrand: handleSwitchBrand,
    isLoading: bizLoading,
  }), [activeBrand, brands, handleSwitchBrand, bizLoading]);

  // ── Loading screen (Firebase restoring session from AsyncStorage) ──
  if (isInitializing) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.bg.primary }}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
          <Text style={{ color: Colors.text.secondary, marginTop: 16, fontSize: 16 }}>Chargement...</Text>
        </View>
      </GestureHandlerRootView>
    );
  }

  // ── Auth screen (not authenticated) ──
  if (!isAuthenticated) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <SafeAreaProvider>
          <NavigationContainer>
            <StatusBar style="dark" />
            <AuthContext.Provider value={authCtx}>
              <AuthStack.Navigator screenOptions={{ headerShown: false }}>
                <AuthStack.Screen name="Login" component={LoginScreen} />
                <AuthStack.Screen name="Register" component={RegisterScreen} />
                <AuthStack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
              </AuthStack.Navigator>
            </AuthContext.Provider>
          </NavigationContainer>
        </SafeAreaProvider>
      </GestureHandlerRootView>
    );
  }

  // ── Loading brands from backend ──
  if (bizLoading) {
    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.bg.primary }}>
          <ActivityIndicator size="large" color={Colors.brand.primary} />
          <Text style={{ color: Colors.text.secondary, marginTop: 16, fontSize: 16 }}>Chargement des marques...</Text>
        </View>
      </GestureHandlerRootView>
    );
  }

  // ── Onboarding flow (onboarding not completed) ──
  if (onboardingChecked && !onboardingStore.completed) {
    const currentBrandId = activeBrand?.id ?? "";
    const screens = [
      <WelcomeScreen key="welcome" onNext={() => setOnboardingStep(1)} />,
      <OnboardingChatScreen
        key="dna-chat"
        brandId={currentBrandId}
        onComplete={() => setOnboardingStep(2)}
      />,
      <ConnectAccountScreen key="connect" onNext={() => setOnboardingStep(3)} />,
      <CompleteScreen key="complete" onFinish={async () => {
        await onboardingStore.markCompleted();
      }} />,
    ];

    return (
      <GestureHandlerRootView style={{ flex: 1 }}>
        <SafeAreaProvider>
          <StatusBar style="dark" />
          {screens[onboardingStep] || screens[0]}
        </SafeAreaProvider>
      </GestureHandlerRootView>
    );
  }

  // ── Main app ──
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ErrorBoundary>
        <SafeAreaProvider>
          <BottomSheetModalProvider>
            <NavigationContainer ref={navigationRef} linking={deepLinkingConfig}>
              <StatusBar style="dark" />
              <AuthContext.Provider value={authCtx}>
                <BrandContext.Provider value={brandCtx}>
                  <TabNavigator />
                </BrandContext.Provider>
              </AuthContext.Provider>
            </NavigationContainer>
          </BottomSheetModalProvider>
        </SafeAreaProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}
