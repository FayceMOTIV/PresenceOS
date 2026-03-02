// PresenceOS Mobile — Onboarding: Restaurant Info

import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface Props {
  onNext: (info: { name: string; cuisine: string; tone: string }) => void;
}

const CUISINES = ["Francais", "Italien", "Japonais", "Marocain", "Libanais", "Burger", "Pizza", "Autre"];
const TONES = ["Chaleureux", "Pro & elegant", "Fun & decale", "Authentique"];

export default function RestaurantInfoScreen({ onNext }: Props) {
  const [name, setName] = useState("");
  const [cuisine, setCuisine] = useState("");
  const [tone, setTone] = useState("");

  const canContinue = name.trim().length > 0;

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.step}>Etape 2/4</Text>
          <Text style={styles.title}>Parlez-moi de votre restaurant</Text>
          <Text style={styles.subtitle}>
            Ces infos aident Ilyas a creer du contenu personnalise
          </Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.label}>Nom du restaurant</Text>
          <TextInput
            style={styles.input}
            placeholder="Ex : Le Family's"
            placeholderTextColor={Colors.text.muted}
            value={name}
            onChangeText={setName}
          />

          <Text style={styles.label}>Type de cuisine</Text>
          <View style={styles.chips}>
            {CUISINES.map((c) => (
              <TouchableOpacity
                key={c}
                style={[styles.chip, cuisine === c && styles.chipActive]}
                onPress={() => setCuisine(c)}
              >
                <Text style={[styles.chipText, cuisine === c && styles.chipTextActive]}>
                  {c}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Ton de communication</Text>
          <View style={styles.chips}>
            {TONES.map((t) => (
              <TouchableOpacity
                key={t}
                style={[styles.chip, tone === t && styles.chipActive]}
                onPress={() => setTone(t)}
              >
                <Text style={[styles.chipText, tone === t && styles.chipTextActive]}>
                  {t}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          onPress={() => onNext({ name: name.trim(), cuisine, tone })}
          disabled={!canContinue}
          activeOpacity={0.8}
        >
          <LinearGradient
            colors={canContinue ? [Colors.brand.primary, Colors.brand.amber] : ["#CCC", "#CCC"]}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.nextBtn}
          >
            <Text style={styles.nextText}>Continuer</Text>
          </LinearGradient>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  scroll: { flex: 1 },
  header: { paddingTop: 80, paddingHorizontal: 32, marginBottom: 24 },
  step: { fontSize: 13, color: Colors.brand.primary, fontWeight: "600", marginBottom: 8 },
  title: { fontSize: 26, fontWeight: "800", color: Colors.text.primary, marginBottom: 8 },
  subtitle: { fontSize: 15, color: Colors.text.secondary, lineHeight: 22 },
  form: { paddingHorizontal: 32 },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.primary,
    marginBottom: 8,
    marginTop: 20,
  },
  input: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: Colors.text.primary,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: Colors.bg.secondary,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  chipActive: {
    backgroundColor: Colors.brand.primary,
    borderColor: Colors.brand.primary,
  },
  chipText: { fontSize: 14, color: Colors.text.secondary, fontWeight: "500" },
  chipTextActive: { color: "#FFF" },
  footer: { paddingHorizontal: 32, paddingBottom: 40 },
  nextBtn: { paddingVertical: 18, borderRadius: 16, alignItems: "center" },
  nextText: { fontSize: 17, fontWeight: "700", color: "#FFF" },
});
