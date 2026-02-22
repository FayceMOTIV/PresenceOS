// PresenceOS Mobile — Glassmorphism Card component

import React from "react";
import { View, StyleSheet, TouchableOpacity, ViewStyle } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Colors } from "@/constants/colors";

interface Props {
  children: React.ReactNode;
  gradient?: readonly [string, string, ...string[]];
  glow?: boolean;
  glowColor?: string;
  onPress?: () => void;
  style?: ViewStyle;
}

export default function Card({ children, gradient, glow, glowColor, onPress, style }: Props) {
  const glowShadow = glow
    ? {
        shadowColor: glowColor || Colors.brand.primary,
        shadowOpacity: 0.3,
        shadowRadius: 16,
        shadowOffset: { width: 0, height: 4 },
        elevation: 8,
      }
    : {};

  const content = gradient ? (
    <LinearGradient
      colors={[...gradient]}
      style={[styles.inner, style]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
    >
      {children}
    </LinearGradient>
  ) : (
    <View style={[styles.card, glowShadow, style]}>{children}</View>
  );

  if (onPress) {
    return (
      <TouchableOpacity activeOpacity={0.85} onPress={onPress} style={[gradient ? styles.wrapper : undefined, glowShadow]}>
        {content}
      </TouchableOpacity>
    );
  }

  return gradient ? <View style={[styles.wrapper, glowShadow]}>{content}</View> : content;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border.default,
    padding: 16,
  },
  wrapper: {
    borderRadius: 16,
    overflow: "hidden",
  },
  inner: {
    borderRadius: 16,
    padding: 16,
  },
});
