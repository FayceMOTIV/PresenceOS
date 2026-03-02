// PresenceOS Mobile — Onboarding: Welcome Screen

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";

interface Props {
  onNext: () => void;
}

export default function WelcomeScreen({ onNext }: Props) {
  return (
    <View style={styles.container}>
      <LinearGradient
        colors={[Colors.brand.primary, Colors.brand.amber]}
        style={styles.heroGradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.avatarCircle}>
          <Text style={styles.avatarEmoji}>{"👨‍🍳"}</Text>
        </View>
        <Text style={styles.heroTitle}>Bienvenue sur PresenceOS</Text>
        <Text style={styles.heroSubtitle}>
          Je suis Ilyas, votre Community Manager IA.{"\n"}
          Je vais gerer vos reseaux sociaux comme un pro.
        </Text>
      </LinearGradient>

      <View style={styles.features}>
        {[
          { icon: "sparkles", text: "Posts IA personnalises a votre restaurant" },
          { icon: "camera", text: "Analysez vos photos de plats en 1 tap" },
          { icon: "trending-up", text: "Publiez sur Instagram, Facebook, TikTok" },
        ].map((f, i) => (
          <View key={i} style={styles.featureRow}>
            <View style={styles.featureIcon}>
              <Ionicons name={f.icon as any} size={20} color={Colors.brand.primary} />
            </View>
            <Text style={styles.featureText}>{f.text}</Text>
          </View>
        ))}
      </View>

      <TouchableOpacity onPress={onNext} activeOpacity={0.8}>
        <LinearGradient
          colors={[Colors.brand.primary, Colors.brand.amber]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={styles.ctaBtn}
        >
          <Text style={styles.ctaText}>Commencer</Text>
          <Ionicons name="arrow-forward" size={20} color="#FFF" />
        </LinearGradient>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  heroGradient: {
    paddingTop: 80,
    paddingBottom: 40,
    alignItems: "center",
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
  },
  avatarCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: "rgba(255,255,255,0.2)",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 24,
  },
  avatarEmoji: { fontSize: 48 },
  heroTitle: {
    fontSize: 28,
    fontWeight: "800",
    color: "#FFF",
    textAlign: "center",
    marginBottom: 12,
  },
  heroSubtitle: {
    fontSize: 16,
    color: "rgba(255,255,255,0.9)",
    textAlign: "center",
    lineHeight: 24,
    paddingHorizontal: 32,
  },
  features: { padding: 32, gap: 20 },
  featureRow: { flexDirection: "row", alignItems: "center", gap: 16 },
  featureIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.brand.glow,
    justifyContent: "center",
    alignItems: "center",
  },
  featureText: {
    flex: 1,
    fontSize: 15,
    color: Colors.text.primary,
    fontWeight: "500",
  },
  ctaBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    marginHorizontal: 32,
    paddingVertical: 18,
    borderRadius: 16,
  },
  ctaText: { fontSize: 18, fontWeight: "700", color: "#FFF" },
});
