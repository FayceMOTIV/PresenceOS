// PresenceOS Mobile — KB Completeness Bar (redesigned, dark theme)

import React, { useEffect, useRef } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Animated } from "react-native";
import { Colors } from "@/constants/colors";

interface KBLevel {
  min: number;
  max: number;
  color: string;
  bg: string;
  icon: string;
  title: string;
  hint: string;
  cta: string | null;
}

const KB_LEVELS: KBLevel[] = [
  {
    min: 0, max: 10,
    color: Colors.status.danger,
    bg: Colors.status.dangerLight,
    icon: "\uD83D\uDD34",
    title: "L'IA ne vous conna\u00EEt pas encore",
    hint: "Ajoutez votre premier plat pour commencer",
    cta: "Commencer \u2192",
  },
  {
    min: 10, max: 35,
    color: Colors.status.warning,
    bg: Colors.status.warningLight,
    icon: "\uD83D\uDFE0",
    title: "L'IA apprend \u00E0 vous conna\u00EEtre",
    hint: "Ajoutez des photos et compl\u00E9tez votre menu",
    cta: "Am\u00E9liorer \u2192",
  },
  {
    min: 35, max: 65,
    color: Colors.status.info,
    bg: Colors.status.infoLight,
    icon: "\uD83D\uDD35",
    title: "L'IA ma\u00EEtrise les bases",
    hint: "Continuez pour des posts encore plus personnalis\u00E9s",
    cta: "Continuer \u2192",
  },
  {
    min: 65, max: 85,
    color: Colors.brand.primary,
    bg: Colors.brand.glow,
    icon: "\uD83D\uDFE3",
    title: "L'IA conna\u00EEt bien votre restaurant",
    hint: "Encore quelques ajouts pour atteindre l'excellence",
    cta: "Finaliser \u2192",
  },
  {
    min: 85, max: 101,
    color: Colors.brand.amber,
    bg: "rgba(244,162,97,0.12)",
    icon: "\uD83C\uDFC6",
    title: "L'IA est experte de votre restaurant !",
    hint: "Vos posts sont maintenant de qualit\u00E9 professionnelle",
    cta: null,
  },
];

function getLevel(score: number): KBLevel {
  return KB_LEVELS.find((l) => score >= l.min && score < l.max) || KB_LEVELS[0];
}

interface Props {
  score: number;
  onPress?: () => void;
  style?: any;
}

export default function KBCompletenessBar({ score, onPress, style }: Props) {
  const level = getLevel(score);
  const animatedWidth = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.spring(animatedWidth, {
      toValue: score,
      friction: 8,
      tension: 40,
      useNativeDriver: false,
    }).start();
  }, [score]);

  const widthInterpolated = animatedWidth.interpolate({
    inputRange: [0, 100],
    outputRange: ["0%", "100%"],
    extrapolate: "clamp",
  });

  return (
    <TouchableOpacity
      style={[
        styles.container,
        { backgroundColor: level.bg, borderColor: level.color + "60" },
        style,
      ]}
      onPress={onPress}
      activeOpacity={0.8}
      disabled={!onPress}
    >
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Text style={styles.icon}>{level.icon}</Text>
          <Text style={styles.title}>
            {level.title}
          </Text>
        </View>
        <Text style={[styles.score, { color: level.color }]}>{score}%</Text>
      </View>

      <View style={styles.barBg}>
        <Animated.View
          style={[
            styles.barFill,
            { width: widthInterpolated, backgroundColor: level.color },
          ]}
        />
      </View>

      <View style={styles.footer}>
        <Text style={[styles.hint, { color: level.color }]}>
          {level.hint}
        </Text>
        {level.cta && (
          <Text style={[styles.cta, { color: level.color }]}>{level.cta}</Text>
        )}
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    borderRadius: 16,
    padding: 16,
    borderWidth: 1.5,
    marginBottom: 16,
  },
  header: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    flex: 1,
  },
  icon: {
    fontSize: 18,
  },
  title: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.text.primary,
    flex: 1,
  },
  score: {
    fontSize: 22,
    fontWeight: "800",
    marginLeft: 8,
  },
  barBg: {
    height: 6,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 3,
    marginBottom: 10,
    overflow: "hidden",
  },
  barFill: {
    height: 6,
    borderRadius: 3,
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  hint: {
    fontSize: 12,
    flex: 1,
  },
  cta: {
    fontSize: 13,
    fontWeight: "700",
    marginLeft: 8,
  },
});
