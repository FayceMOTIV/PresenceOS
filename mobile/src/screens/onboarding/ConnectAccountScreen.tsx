// PresenceOS Mobile — Onboarding: Connect Social Accounts

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Linking } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface Props {
  onNext: () => void;
}

const PLATFORMS = [
  { key: "instagram", label: "Instagram", icon: "logo-instagram" as const, color: "#E1306C" },
  { key: "facebook", label: "Facebook", icon: "logo-facebook" as const, color: "#1877F2" },
  { key: "tiktok", label: "TikTok", icon: "logo-tiktok" as const, color: "#000" },
];

export default function ConnectAccountScreen({ onNext }: Props) {
  const handleConnect = () => {
    Linking.openURL("https://my.blotato.com/settings");
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.step}>Etape 1/4</Text>
        <Text style={styles.title}>Connectez vos reseaux</Text>
        <Text style={styles.subtitle}>
          Liez vos comptes pour publier directement depuis l'app
        </Text>
      </View>

      <View style={styles.platforms}>
        {PLATFORMS.map((p) => (
          <View key={p.key} style={styles.platformCard}>
            <View style={[styles.iconWrap, { backgroundColor: p.color + "15" }]}>
              <Ionicons name={p.icon} size={28} color={p.color} />
            </View>
            <Text style={styles.platformLabel}>{p.label}</Text>
            <TouchableOpacity
              style={[styles.connectBtn, { borderColor: p.color + "50" }]}
              onPress={handleConnect}
            >
              <Text style={[styles.connectText, { color: p.color }]}>Connecter</Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      <View style={styles.footer}>
        <TouchableOpacity onPress={onNext} activeOpacity={0.8}>
          <LinearGradient
            colors={[Colors.brand.primary, Colors.brand.amber]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.nextBtn}
          >
            <Text style={styles.nextText}>Continuer</Text>
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity onPress={onNext} style={styles.skipBtn}>
          <Text style={styles.skipText}>Passer cette etape</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: { paddingTop: 80, paddingHorizontal: 32, marginBottom: 32 },
  step: { fontSize: 13, color: Colors.brand.primary, fontWeight: "600", marginBottom: 8 },
  title: { fontSize: 28, fontWeight: "800", color: Colors.text.primary, marginBottom: 8 },
  subtitle: { fontSize: 15, color: Colors.text.secondary, lineHeight: 22 },
  platforms: { paddingHorizontal: 32, gap: 12 },
  platformCard: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 16,
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
  platformLabel: {
    flex: 1,
    fontSize: 16,
    fontWeight: "600",
    color: Colors.text.primary,
    marginLeft: 14,
  },
  connectBtn: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 10,
    borderWidth: 1,
  },
  connectText: { fontSize: 13, fontWeight: "600" },
  footer: { position: "absolute", bottom: 40, left: 32, right: 32, gap: 12 },
  nextBtn: {
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: "center",
  },
  nextText: { fontSize: 17, fontWeight: "700", color: "#FFF" },
  skipBtn: { alignItems: "center", paddingVertical: 12 },
  skipText: { fontSize: 14, color: Colors.text.muted, fontWeight: "500" },
});
