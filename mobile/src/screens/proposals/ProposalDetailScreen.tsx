// PresenceOS Mobile — Proposal Detail (dark theme, French)

import React, { useContext, useState, useEffect, useCallback } from "react";
import {
  View, Text, Image, StyleSheet, ScrollView, TouchableOpacity, Alert, TextInput, ActivityIndicator,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useNavigation, useRoute, RouteProp } from "@react-navigation/native";
import { Ionicons } from "@expo/vector-icons";
import { BrandContext } from "@/contexts/BrandContext";
import { ProposalsStackParams } from "@/navigation/TabNavigator";
import { Colors } from "@/constants/colors";
import { FR } from "@/constants/i18n";
import { proposalsApi } from "@/lib/api";
import { AIProposal } from "@/types";

type Route = RouteProp<ProposalsStackParams, "ProposalDetail">;

const STATUS_COLORS: Record<string, string> = {
  pending: Colors.status.warning,
  approved: Colors.brand.amber,
  published: Colors.status.success,
  rejected: Colors.status.danger,
};

const STATUS_LABELS: Record<string, string> = {
  pending: FR.proposals_filter_pending,
  approved: FR.proposals_filter_approved,
  published: FR.proposals_filter_published,
  rejected: FR.proposals_filter_rejected,
};

export default function ProposalDetailScreen() {
  const nav = useNavigation();
  const route = useRoute<Route>();
  const { proposalId } = route.params;
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [proposal, setProposal] = useState<AIProposal | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingCaption, setEditingCaption] = useState(false);
  const [captionText, setCaptionText] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [publishState, setPublishState] = useState<"idle" | "publishing" | "success" | "error">("idle");
  const [publishError, setPublishError] = useState("");

  const fetchProposal = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await proposalsApi.list(brandId);
      const list = res.data.proposals || res.data || [];
      const found = list.find((p: AIProposal) => p.id === proposalId);
      if (found) {
        setProposal(found);
        setCaptionText(found.caption || "");
      }
    } catch { /* silent */ } finally { setLoading(false); }
  }, [brandId, proposalId]);

  useEffect(() => { fetchProposal(); }, [fetchProposal]);

  const handleApprove = async () => {
    if (!brandId || !proposal) return;
    setActionLoading(true);
    setPublishState("publishing");
    setPublishError("");
    try {
      const res = await proposalsApi.approve(brandId, proposal.id);
      setPublishState("success");
      setProposal({ ...proposal, status: "published" });
      const postUrl = res.data?.post_url;
      Alert.alert(
        "Publie sur Instagram !",
        postUrl
          ? `Votre post est en ligne.\n\n${postUrl}`
          : "Votre post a ete envoye avec succes.",
        [{ text: "OK", onPress: () => nav.goBack() }]
      );
    } catch (err: any) {
      setPublishState("error");
      const detail = err?.response?.data?.detail || FR.error_generic;
      setPublishError(detail);
      Alert.alert("Erreur de publication", detail);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!brandId || !proposal) return;
    setActionLoading(true);
    try {
      await proposalsApi.reject(brandId, proposal.id);
      nav.goBack();
    } catch { Alert.alert(FR.error_generic); } finally { setActionLoading(false); }
  };

  const handleRegenerate = async () => {
    if (!brandId || !proposal) return;
    setActionLoading(true);
    try {
      await proposalsApi.regenerate(brandId, proposal.id);
      Alert.alert("🔄", "Nouvelle version en cours de génération...");
      nav.goBack();
    } catch { Alert.alert(FR.error_generic); } finally { setActionLoading(false); }
  };

  const handleSaveCaption = async () => {
    if (!brandId || !proposal) return;
    try {
      await proposalsApi.editCaption(brandId, proposal.id, captionText);
      setProposal({ ...proposal, caption: captionText });
      setEditingCaption(false);
    } catch { Alert.alert(FR.error_generic); }
  };

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={Colors.brand.primary} /></View>;
  }

  if (!proposal) {
    return <View style={styles.center}><Text style={styles.errorText}>{FR.error_generic}</Text></View>;
  }

  const statusColor = STATUS_COLORS[proposal.status] || Colors.text.secondary;

  return (
    <SafeAreaView style={styles.container} edges={["top"]}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => nav.goBack()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <View style={[styles.statusBadge, { backgroundColor: statusColor + "20", borderColor: statusColor + "40" }]}>
          <Text style={[styles.statusText, { color: statusColor }]}>
            {STATUS_LABELS[proposal.status] || proposal.status}
          </Text>
        </View>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        {/* Preview image */}
        {(proposal.image_url || proposal.improved_image_url) && (
          <Image
            source={{ uri: proposal.improved_image_url || proposal.image_url }}
            style={styles.image}
            resizeMode="cover"
          />
        )}

        {/* Caption */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>{FR.proposal_caption}</Text>
            {!editingCaption && (
              <TouchableOpacity onPress={() => setEditingCaption(true)}>
                <Ionicons name="pencil" size={18} color={Colors.brand.primary} />
              </TouchableOpacity>
            )}
          </View>
          {editingCaption ? (
            <View>
              <TextInput
                style={styles.captionInput}
                value={captionText}
                onChangeText={setCaptionText}
                multiline
                textAlignVertical="top"
              />
              <View style={styles.captionActions}>
                <TouchableOpacity style={styles.cancelBtn} onPress={() => { setEditingCaption(false); setCaptionText(proposal.caption || ""); }}>
                  <Text style={styles.cancelText}>{FR.cancel}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.saveBtn} onPress={handleSaveCaption}>
                  <Text style={styles.saveText}>{FR.save}</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <Text style={styles.caption}>{proposal.caption || "—"}</Text>
          )}
        </View>

        {/* Hashtags */}
        {proposal.hashtags && proposal.hashtags.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>{FR.proposal_hashtags}</Text>
            <Text style={styles.hashtags}>{proposal.hashtags.join(" ")}</Text>
          </View>
        )}

        {/* Meta */}
        <View style={styles.metaRow}>
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>{FR.proposal_platform}</Text>
            <Text style={styles.metaValue}>{proposal.platform}</Text>
          </View>
          <View style={styles.metaItem}>
            <Text style={styles.metaLabel}>{FR.proposal_type}</Text>
            <Text style={styles.metaValue}>{proposal.proposal_type}</Text>
          </View>
          {proposal.confidence_score != null && (
            <View style={styles.metaItem}>
              <Text style={styles.metaLabel}>{FR.proposal_score}</Text>
              <Text style={[styles.metaValue, { color: Colors.brand.amber }]}>
                {Math.round(proposal.confidence_score * 100)}%
              </Text>
            </View>
          )}
        </View>
      </ScrollView>

      {/* Actions */}
      {proposal.status === "pending" && (
        <View style={styles.actions}>
          <TouchableOpacity style={styles.approveBtn} onPress={handleApprove} disabled={actionLoading}>
            {publishState === "publishing" ? (
              <View style={styles.publishingRow}>
                <ActivityIndicator color="#FFF" size="small" />
                <Text style={styles.approveBtnText}>Publication en cours...</Text>
              </View>
            ) : (
              <Text style={styles.approveBtnText}>{FR.proposal_approve}</Text>
            )}
          </TouchableOpacity>
          {publishError ? (
            <Text style={styles.publishError}>{publishError}</Text>
          ) : null}
          <View style={styles.secondaryActions}>
            <TouchableOpacity style={styles.secondaryBtn} onPress={handleRegenerate} disabled={actionLoading}>
              <Ionicons name="refresh" size={18} color={Colors.text.secondary} />
              <Text style={styles.secondaryText}>{FR.proposal_variant}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryBtn} onPress={handleReject} disabled={actionLoading}>
              <Ionicons name="close-circle-outline" size={18} color={Colors.status.danger} />
              <Text style={[styles.secondaryText, { color: Colors.status.danger }]}>{FR.proposal_reject}</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
      {proposal.status === "published" && (
        <View style={styles.actions}>
          <View style={styles.publishedBanner}>
            <Ionicons name="checkmark-circle" size={22} color={Colors.status.success} />
            <Text style={styles.publishedText}>Publie sur Instagram</Text>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  center: { flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: Colors.bg.primary },
  errorText: { color: Colors.text.secondary, fontSize: 14 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", paddingHorizontal: 16, paddingVertical: 12 },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, borderWidth: 1 },
  statusText: { fontSize: 12, fontWeight: "600" },
  scroll: { paddingBottom: 120 },
  image: { width: "100%", aspectRatio: 1, backgroundColor: Colors.bg.secondary },
  section: { paddingHorizontal: 20, paddingTop: 16 },
  sectionHeader: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  sectionTitle: { fontSize: 14, fontWeight: "600", color: Colors.text.secondary },
  caption: { fontSize: 15, color: Colors.text.primary, lineHeight: 22 },
  captionInput: { backgroundColor: Colors.bg.elevated, borderWidth: 1, borderColor: Colors.border.default, borderRadius: 12, padding: 14, fontSize: 15, color: Colors.text.primary, minHeight: 80 },
  captionActions: { flexDirection: "row", gap: 8, marginTop: 8, justifyContent: "flex-end" },
  cancelBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, backgroundColor: Colors.bg.secondary },
  cancelText: { color: Colors.text.secondary, fontWeight: "600", fontSize: 14 },
  saveBtn: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8, backgroundColor: Colors.brand.primary },
  saveText: { color: "#FFF", fontWeight: "600", fontSize: 14 },
  hashtags: { fontSize: 14, color: Colors.status.info, lineHeight: 20 },
  metaRow: { flexDirection: "row", paddingHorizontal: 20, paddingTop: 16, gap: 16 },
  metaItem: { flex: 1, backgroundColor: Colors.bg.secondary, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: Colors.border.default },
  metaLabel: { fontSize: 11, color: Colors.text.muted, marginBottom: 4 },
  metaValue: { fontSize: 14, fontWeight: "600", color: Colors.text.primary, textTransform: "capitalize" },
  actions: { position: "absolute", bottom: 0, left: 0, right: 0, padding: 16, paddingBottom: 34, backgroundColor: Colors.bg.secondary, borderTopWidth: 1, borderTopColor: Colors.border.default },
  approveBtn: { backgroundColor: Colors.brand.primary, borderRadius: 14, paddingVertical: 16, alignItems: "center", marginBottom: 12 },
  approveBtnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
  secondaryActions: { flexDirection: "row", justifyContent: "center", gap: 24 },
  secondaryBtn: { flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 8 },
  secondaryText: { fontSize: 14, fontWeight: "500", color: Colors.text.secondary },
  publishingRow: { flexDirection: "row", alignItems: "center", gap: 10, justifyContent: "center" },
  publishError: { color: Colors.status.danger, fontSize: 13, textAlign: "center", marginTop: 8 },
  publishedBanner: { flexDirection: "row", alignItems: "center", gap: 8, justifyContent: "center", paddingVertical: 16 },
  publishedText: { fontSize: 16, fontWeight: "700", color: Colors.status.success },
});
