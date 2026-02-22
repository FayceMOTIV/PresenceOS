// PresenceOS Mobile — Proposal Card (Instagram-style, dark theme, French)

import React from "react";
import { View, Text, Image, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { AIProposal } from "@/types";
import { LinearGradient } from "expo-linear-gradient";

const STATUS_COLORS: Record<string, string> = {
  pending: Colors.brand.amber,
  approved: Colors.status.info,
  published: Colors.status.success,
  rejected: Colors.status.danger,
};

const STATUS_LABELS: Record<string, string> = {
  pending: FR.proposals_filter_pending,
  approved: FR.proposals_filter_approved,
  published: FR.proposals_filter_published,
  rejected: FR.proposals_filter_rejected,
};

const PLATFORM_ICONS: Record<string, any> = {
  instagram: "logo-instagram",
  facebook: "logo-facebook",
  tiktok: "logo-tiktok",
};

const PLATFORM_COLORS: Record<string, string> = {
  instagram: "#E4405F",
  facebook: "#1877F2",
  tiktok: "#000000",
};

interface Props {
  proposal: AIProposal;
  onPress: () => void;
}

export default function ProposalCard({ proposal, onPress }: Props) {
  const statusColor = STATUS_COLORS[proposal.status] || Colors.text.secondary;
  const imageUrl = proposal.improved_image_url || proposal.image_url;
  const platformKey = proposal.platform.toLowerCase();
  const platformIcon = PLATFORM_ICONS[platformKey] || "apps";
  const platformColor = PLATFORM_COLORS[platformKey] || Colors.brand.primary;

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      {/* Horizontal layout: thumbnail left, content right */}
      <View style={styles.container}>
        {/* Thumbnail with badge overlay */}
        <View style={styles.thumbnailContainer}>
          {imageUrl ? (
            <Image source={{ uri: imageUrl }} style={styles.thumbnail} resizeMode="cover" />
          ) : (
            <LinearGradient
              colors={["#EDE9FF", "#F0EEFF"]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.thumbnail}
            />
          )}
          {/* Badge overlay in top-right corner */}
          <View style={[styles.badge, { backgroundColor: statusColor }]}>
            <Text style={styles.badgeText}>
              {STATUS_LABELS[proposal.status] || proposal.status}
            </Text>
          </View>
        </View>

        {/* Content on the right */}
        <View style={styles.content}>
          {/* Platform icon and type */}
          <View style={styles.headerRow}>
            <View style={styles.platformContainer}>
              <Ionicons name={platformIcon} size={16} color={platformColor} />
              <Text style={styles.type}>{proposal.proposal_type}</Text>
            </View>
          </View>

          {/* Caption truncated to 2 lines */}
          <Text style={styles.caption} numberOfLines={2}>
            {proposal.caption}
          </Text>

          {/* Confidence score as percentage with bar */}
          {proposal.confidence_score != null && (
            <View style={styles.scoreContainer}>
              <View style={styles.scoreBar}>
                <View
                  style={[
                    styles.scoreBarFill,
                    {
                      width: `${Math.round(proposal.confidence_score * 100)}%`,
                      backgroundColor: Colors.brand.amber,
                    },
                  ]}
                />
              </View>
              <Text style={styles.scoreText}>
                {Math.round(proposal.confidence_score * 100)}%
              </Text>
            </View>
          )}
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.border.default,
    overflow: "hidden",
  },
  container: {
    flexDirection: "row",
    padding: 12,
  },
  thumbnailContainer: {
    position: "relative",
    width: 80,
    height: 80,
    borderRadius: 14,
    overflow: "hidden",
    marginRight: 12,
  },
  thumbnail: {
    width: 80,
    height: 80,
  },
  badge: {
    position: "absolute",
    top: 4,
    right: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: "700",
    color: Colors.text.primary,
    textTransform: "uppercase",
  },
  content: {
    flex: 1,
    justifyContent: "space-between",
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 6,
  },
  platformContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  type: {
    fontSize: 12,
    color: Colors.text.secondary,
    fontWeight: "600",
    textTransform: "capitalize",
  },
  caption: {
    fontSize: 14,
    color: Colors.text.primary,
    lineHeight: 18,
    marginBottom: 8,
  },
  scoreContainer: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  scoreBar: {
    flex: 1,
    height: 4,
    backgroundColor: Colors.bg.elevated,
    borderRadius: 2,
    overflow: "hidden",
  },
  scoreBarFill: {
    height: "100%",
    borderRadius: 2,
  },
  scoreText: {
    fontSize: 11,
    color: Colors.brand.amber,
    fontWeight: "700",
    minWidth: 35,
    textAlign: "right",
  },
});
