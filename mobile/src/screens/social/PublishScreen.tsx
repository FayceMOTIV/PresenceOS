// PresenceOS Mobile — PublishScreen (Postiz social publishing)

import React, { useState, useEffect, useCallback, useContext } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  StyleSheet,
  RefreshControl,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import type { HomeStackParams } from "@/navigation/TabNavigator";
import { BrandContext } from "@/contexts/BrandContext";
import { Colors } from "@/constants/colors";
import { postizApi } from "@/lib/api";

interface Integration {
  id: string;
  name: string;
  identifier: string;
  picture?: string;
  disabled?: boolean;
}

const PLATFORM_ICONS: Record<string, { icon: keyof typeof Ionicons.glyphMap; color: string }> = {
  instagram: { icon: "logo-instagram", color: "#E4405F" },
  facebook: { icon: "logo-facebook", color: "#1877F2" },
  tiktok: { icon: "logo-tiktok", color: "#010101" },
  linkedin: { icon: "logo-linkedin", color: "#0A66C2" },
  x: { icon: "logo-twitter", color: "#1DA1F2" },
  youtube: { icon: "logo-youtube", color: "#FF0000" },
};

const SCHEDULE_OPTIONS = [
  { label: "Maintenant", value: "now" },
  { label: "Demain 9h", value: "tomorrow_9" },
  { label: "Demain 12h", value: "tomorrow_12" },
  { label: "Demain 18h", value: "tomorrow_18" },
];

function getScheduleDate(value: string): Date | null {
  if (value === "now") return null;
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  tomorrow.setMinutes(0, 0, 0);
  if (value === "tomorrow_9") tomorrow.setHours(9);
  if (value === "tomorrow_12") tomorrow.setHours(12);
  if (value === "tomorrow_18") tomorrow.setHours(18);
  return tomorrow;
}

export default function PublishScreen() {
  const nav = useNavigation<NativeStackNavigationProp<HomeStackParams>>();
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;

  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [content, setContent] = useState("");
  const [scheduleOption, setScheduleOption] = useState("now");
  const [loading, setLoading] = useState(false);
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadIntegrations = useCallback(async () => {
    if (!brandId) return;
    try {
      const res = await postizApi.integrations(brandId);
      const list = Array.isArray(res.data) ? res.data : [];
      setIntegrations(list.filter((i: Integration) => !i.disabled));
    } catch {
      // Postiz may not be configured yet
      setIntegrations([]);
    } finally {
      setLoadingIntegrations(false);
    }
  }, [brandId]);

  useEffect(() => {
    loadIntegrations();
  }, [loadIntegrations]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadIntegrations();
    setRefreshing(false);
  }, [loadIntegrations]);

  const togglePlatform = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handlePublish = async () => {
    if (!brandId) return;
    if (selected.length === 0) {
      return Alert.alert("Erreur", "Selectionne au moins une plateforme.");
    }
    if (!content.trim()) {
      return Alert.alert("Erreur", "Le contenu est vide.");
    }

    setLoading(true);
    try {
      const scheduleDate = getScheduleDate(scheduleOption);
      if (scheduleDate) {
        await postizApi.schedule(
          brandId,
          selected,
          content.trim(),
          scheduleDate.toISOString(),
        );
        Alert.alert(
          "Planifie !",
          `Ton post sera publie le ${scheduleDate.toLocaleDateString("fr-FR")} a ${scheduleDate.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}.`,
        );
      } else {
        await postizApi.publishNow(brandId, selected, content.trim());
        Alert.alert("Publie !", "Ton post est en ligne.");
      }
      setContent("");
      setSelected([]);
    } catch (e: any) {
      Alert.alert("Erreur", e?.response?.data?.detail || "Publication echouee.");
    } finally {
      setLoading(false);
    }
  };

  const canPublish = selected.length > 0 && content.trim().length > 0 && !loading;

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.brand.primary} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => nav.goBack()} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Ionicons name="arrow-back" size={24} color={Colors.text.primary} />
          </TouchableOpacity>
          <Text style={styles.title}>Publier</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Platforms */}
        <Text style={styles.sectionLabel}>Plateformes</Text>
        {loadingIntegrations ? (
          <ActivityIndicator color={Colors.brand.primary} style={{ marginVertical: 20 }} />
        ) : integrations.length === 0 ? (
          <View style={styles.emptyCard}>
            <Ionicons name="link-outline" size={32} color={Colors.text.muted} />
            <Text style={styles.emptyTitle}>Aucun compte connecté</Text>
            <Text style={styles.emptyBody}>
              Connecte tes réseaux sociaux pour commencer à publier.
            </Text>
            <TouchableOpacity
              style={styles.connectCta}
              onPress={() => nav.navigate("ConnectSocials")}
              activeOpacity={0.8}
            >
              <Ionicons name="add-circle-outline" size={18} color="#FFF" />
              <Text style={styles.connectCtaText}>Connecter mes réseaux</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <View style={styles.platformGrid}>
            {integrations.map((integ) => {
              const platformInfo = PLATFORM_ICONS[integ.identifier] || {
                icon: "globe-outline" as keyof typeof Ionicons.glyphMap,
                color: Colors.text.secondary,
              };
              const isSelected = selected.includes(integ.id);
              return (
                <TouchableOpacity
                  key={integ.id}
                  style={[styles.platformChip, isSelected && styles.platformChipActive]}
                  onPress={() => togglePlatform(integ.id)}
                  activeOpacity={0.7}
                >
                  <Ionicons
                    name={platformInfo.icon}
                    size={20}
                    color={isSelected ? Colors.brand.primary : platformInfo.color}
                  />
                  <Text style={[styles.platformName, isSelected && styles.platformNameActive]}>
                    {integ.name || integ.identifier}
                  </Text>
                  {isSelected && (
                    <Ionicons name="checkmark-circle" size={16} color={Colors.brand.primary} />
                  )}
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {/* Content */}
        <Text style={styles.sectionLabel}>Contenu</Text>
        <View style={styles.textareaWrap}>
          <TextInput
            style={styles.textarea}
            value={content}
            onChangeText={setContent}
            placeholder="Qu'est-ce que tu veux partager ?"
            placeholderTextColor={Colors.text.muted}
            multiline
            maxLength={2200}
            textAlignVertical="top"
          />
          <Text style={styles.charCount}>{content.length}/2200</Text>
        </View>

        {/* Schedule */}
        <Text style={styles.sectionLabel}>Quand publier ?</Text>
        <View style={styles.scheduleGrid}>
          {SCHEDULE_OPTIONS.map((opt) => (
            <TouchableOpacity
              key={opt.value}
              style={[
                styles.scheduleChip,
                scheduleOption === opt.value && styles.scheduleChipActive,
              ]}
              onPress={() => setScheduleOption(opt.value)}
              activeOpacity={0.7}
            >
              <Text
                style={[
                  styles.scheduleLabel,
                  scheduleOption === opt.value && styles.scheduleLabelActive,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* CTA */}
        <TouchableOpacity
          style={[styles.publishBtn, !canPublish && styles.publishBtnDisabled]}
          onPress={handlePublish}
          disabled={!canPublish}
          activeOpacity={0.8}
        >
          {loading ? (
            <ActivityIndicator color="#FFF" />
          ) : (
            <>
              <Ionicons
                name={scheduleOption === "now" ? "paper-plane" : "calendar"}
                size={18}
                color="#FFF"
              />
              <Text style={styles.publishBtnText}>
                {scheduleOption === "now" ? "Publier maintenant" : "Planifier le post"}
              </Text>
            </>
          )}
        </TouchableOpacity>

        <View style={{ height: 60 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  scroll: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 60,
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary,
  },
  sectionLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text.secondary,
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 10,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  emptyCard: {
    marginHorizontal: 20,
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  emptyTitle: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.text.primary,
  },
  emptyBody: {
    fontSize: 13,
    color: Colors.text.muted,
    textAlign: "center",
    lineHeight: 18,
  },
  connectCta: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    backgroundColor: Colors.brand.primary,
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 10,
    marginTop: 12,
  },
  connectCtaText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FFFFFF",
  },
  platformGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginHorizontal: 20,
  },
  platformChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  platformChipActive: {
    backgroundColor: Colors.brand.glow,
    borderColor: Colors.brand.primary,
  },
  platformName: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text.secondary,
  },
  platformNameActive: {
    color: Colors.brand.primary,
  },
  textareaWrap: {
    marginHorizontal: 20,
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: Colors.border.default,
    overflow: "hidden",
  },
  textarea: {
    padding: 14,
    fontSize: 15,
    color: Colors.text.primary,
    minHeight: 120,
    lineHeight: 22,
  },
  charCount: {
    fontSize: 11,
    color: Colors.text.muted,
    textAlign: "right",
    paddingRight: 12,
    paddingBottom: 8,
  },
  scheduleGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
    marginHorizontal: 20,
  },
  scheduleChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  scheduleChipActive: {
    backgroundColor: Colors.brand.primary,
    borderColor: Colors.brand.primary,
  },
  scheduleLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text.secondary,
  },
  scheduleLabelActive: {
    color: "#FFFFFF",
  },
  publishBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    marginHorizontal: 20,
    marginTop: 28,
    paddingVertical: 16,
    borderRadius: 14,
    backgroundColor: Colors.brand.primary,
    shadowColor: Colors.brand.primary,
    shadowOpacity: 0.3,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  publishBtnDisabled: {
    opacity: 0.4,
  },
  publishBtnText: {
    fontSize: 16,
    fontWeight: "700",
    color: "#FFFFFF",
  },
});
