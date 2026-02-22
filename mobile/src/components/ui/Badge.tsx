// PresenceOS Mobile — Status Badge component

import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Colors } from "@/constants/colors";

type Status = "pending" | "approved" | "published" | "rejected" | string;

const STATUS_CONFIG: Record<string, { color: string; bg: string; label: string }> = {
  pending: { color: Colors.brand.amber, bg: "rgba(244,162,97,0.15)", label: "En attente" },
  approved: { color: Colors.status.info, bg: "rgba(59,130,246,0.15)", label: "Approuve" },
  published: { color: Colors.status.success, bg: "rgba(16,184,129,0.15)", label: "Publie" },
  rejected: { color: Colors.status.danger, bg: "rgba(239,68,68,0.15)", label: "Rejete" },
};

interface Props {
  status: Status;
  label?: string;
  size?: "sm" | "md";
}

export default function Badge({ status, label, size = "md" }: Props) {
  const config = STATUS_CONFIG[status] || {
    color: Colors.text.secondary,
    bg: "rgba(167,169,190,0.1)",
    label: status,
  };

  const isSmall = size === "sm";

  return (
    <View style={[styles.badge, { backgroundColor: config.bg }, isSmall && styles.badgeSm]}>
      <View style={[styles.dot, { backgroundColor: config.color }]} />
      <Text
        style={[styles.text, { color: config.color }, isSmall && styles.textSm]}
      >
        {label || config.label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
  },
  badgeSm: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    gap: 4,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  text: {
    fontSize: 12,
    fontWeight: "600",
  },
  textSm: {
    fontSize: 10,
  },
});
