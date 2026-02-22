// PresenceOS Mobile — Empty State Card (premium)

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface EmptyStateProps {
  emoji: string;
  title: string;
  body: string;
  ctaLabel?: string;
  onCta?: () => void;
  secondaryLabel?: string;
  onSecondary?: () => void;
}

export default function EmptyStateCard({
  emoji,
  title,
  body,
  ctaLabel,
  onCta,
  secondaryLabel,
  onSecondary,
}: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <View style={styles.emojiContainer}>
        <Text style={styles.emoji}>{emoji}</Text>
      </View>

      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{body}</Text>

      {ctaLabel && (
        <TouchableOpacity style={styles.ctaButton} onPress={onCta} activeOpacity={0.85}>
          <LinearGradient
            colors={[...Colors.gradient.hero]}
            style={styles.ctaGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
          >
            <Text style={styles.ctaText}>{ctaLabel}</Text>
          </LinearGradient>
        </TouchableOpacity>
      )}
      {secondaryLabel && (
        <TouchableOpacity style={styles.secondaryButton} onPress={onSecondary}>
          <Text style={styles.secondaryText}>{secondaryLabel}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 24,
    borderWidth: 1,
    borderColor: Colors.border.default,
    margin: 16,
  },
  emojiContainer: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.bg.elevated,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 24,
    borderWidth: 2,
    borderColor: Colors.brand.primary + "40",
  },
  emoji: {
    fontSize: 48,
  },
  title: {
    fontSize: 22,
    fontWeight: "700",
    color: Colors.text.primary,
    textAlign: "center",
    marginBottom: 12,
  },
  body: {
    fontSize: 15,
    color: Colors.text.secondary,
    textAlign: "center",
    lineHeight: 22,
    marginBottom: 28,
  },
  ctaButton: {
    borderRadius: 14,
    overflow: "hidden",
    marginBottom: 12,
  },
  ctaGradient: {
    paddingHorizontal: 28,
    paddingVertical: 16,
    borderRadius: 14,
  },
  ctaText: {
    color: "#FFF",
    fontWeight: "700",
    fontSize: 16,
    textAlign: "center",
  },
  secondaryButton: {
    paddingHorizontal: 28,
    paddingVertical: 12,
  },
  secondaryText: {
    color: Colors.text.secondary,
    fontSize: 14,
  },
});
