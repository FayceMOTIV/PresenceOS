// PresenceOS Mobile — Onboarding: Complete

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface Props {
  onFinish: () => void;
}

export default function CompleteScreen({ onFinish }: Props) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.checkCircle}>
          <Ionicons name="checkmark" size={48} color="#FFF" />
        </View>
        <Text style={styles.title}>C'est parti !</Text>
        <Text style={styles.subtitle}>
          Votre espace est pret. Ilyas connait votre restaurant{"\n"}
          et peut commencer a creer du contenu.
        </Text>

        <View style={styles.recap}>
          {[
            { icon: "chatbubble-ellipses", text: "Parlez a Ilyas dans l'onglet Chat" },
            { icon: "images", text: "Uploadez des photos dans Mediatheque" },
            { icon: "sparkles", text: "Validez les posts IA depuis Accueil" },
          ].map((item, i) => (
            <View key={i} style={styles.recapRow}>
              <Ionicons name={item.icon as any} size={20} color={Colors.brand.primary} />
              <Text style={styles.recapText}>{item.text}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.footer}>
        <TouchableOpacity onPress={onFinish} activeOpacity={0.8}>
          <LinearGradient
            colors={[Colors.brand.primary, Colors.brand.amber]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.finishBtn}
          >
            <Text style={styles.finishText}>Commencer</Text>
            <Ionicons name="arrow-forward" size={20} color="#FFF" />
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  content: { flex: 1, justifyContent: "center", alignItems: "center", padding: 32 },
  checkCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: Colors.status.success,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 32,
    shadowColor: Colors.status.success,
    shadowOpacity: 0.4,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 8 },
    elevation: 10,
  },
  title: {
    fontSize: 32,
    fontWeight: "800",
    color: Colors.text.primary,
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 16,
    color: Colors.text.secondary,
    textAlign: "center",
    lineHeight: 24,
    marginBottom: 40,
  },
  recap: { gap: 16, width: "100%" },
  recapRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  recapText: { fontSize: 15, color: Colors.text.primary, fontWeight: "500" },
  footer: { paddingHorizontal: 32, paddingBottom: 40 },
  finishBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    paddingVertical: 18,
    borderRadius: 16,
  },
  finishText: { fontSize: 18, fontWeight: "700", color: "#FFF" },
});
