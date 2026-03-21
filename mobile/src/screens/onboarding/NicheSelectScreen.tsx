// PresenceOS Mobile — Onboarding: Niche Selection

import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface Props {
  onNext: (niche: string) => void;
}

const AVAILABLE_NICHES = [
  { key: "restaurant", label: "🍕 Restaurant / Café" },
  { key: "boulangerie", label: "🥐 Boulangerie / Pâtisserie" },
  { key: "medecin", label: "🏥 Médecin / Santé" },
  { key: "dentiste", label: "🦷 Dentiste" },
  { key: "pharmacie", label: "💊 Pharmacie" },
  { key: "coiffeur", label: "💇 Coiffeur / Salon" },
  { key: "estheticienne", label: "💅 Institut de beauté" },
  { key: "coach_sportif", label: "🏋️ Coach sportif / Gym" },
  { key: "coach_vie", label: "🎯 Coach de vie / Personnel" },
  { key: "avocat", label: "⚖️ Avocat / Juridique" },
  { key: "comptable", label: "📊 Expert-comptable" },
  { key: "agent_immobilier", label: "🏠 Immobilier" },
  { key: "ecommerce", label: "🛒 E-commerce / Boutique" },
  { key: "formateur", label: "🎓 Formateur / Formation" },
  { key: "artisan", label: "🔨 Artisan / PME locale" },
  { key: "saas", label: "💻 SaaS / Tech" },
];

export default function NicheSelectScreen({ onNext }: Props) {
  const [selectedNiche, setSelectedNiche] = useState<string>("restaurant");

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.step}>Etape 2/5</Text>
          <Text style={styles.title}>Quel est votre secteur ?</Text>
          <Text style={styles.subtitle}>
            Ilyas s'adapte automatiquement aux codes de votre métier
          </Text>
        </View>

        <View style={styles.grid}>
          {AVAILABLE_NICHES.map((niche) => (
            <TouchableOpacity
              key={niche.key}
              style={[
                styles.nicheCard,
                selectedNiche === niche.key && styles.nicheCardActive,
              ]}
              onPress={() => setSelectedNiche(niche.key)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.nicheLabel,
                  selectedNiche === niche.key && styles.nicheLabelActive,
                ]}
              >
                {niche.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          onPress={() => onNext(selectedNiche)}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={[Colors.brand.primary, Colors.brand.amber]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.nextBtn}
          >
            <Text style={styles.nextText}>Continuer</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  scroll: { flex: 1 },
  header: { paddingTop: 80, paddingHorizontal: 32, marginBottom: 24 },
  step: {
    fontSize: 13,
    color: Colors.brand.primary,
    fontWeight: "600",
    marginBottom: 8,
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
    color: Colors.text.primary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: Colors.text.secondary,
    lineHeight: 22,
  },
  grid: {
    paddingHorizontal: 24,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
    paddingBottom: 120,
  },
  nicheCard: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 16,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1.5,
    borderColor: Colors.border.default,
  },
  nicheCardActive: {
    backgroundColor: Colors.brand.primary + "15",
    borderColor: Colors.brand.primary,
  },
  nicheLabel: {
    fontSize: 14,
    color: Colors.text.secondary,
    fontWeight: "500",
  },
  nicheLabelActive: {
    color: Colors.brand.primary,
    fontWeight: "700",
  },
  footer: { paddingHorizontal: 32, paddingBottom: 40 },
  nextBtn: {
    paddingVertical: 18,
    borderRadius: 16,
    alignItems: "center",
  },
  nextText: { fontSize: 17, fontWeight: "700", color: "#FFF" },
});
