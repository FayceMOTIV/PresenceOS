// PresenceOS Mobile — War Room Ilyas (light theme)
// Envoie n'importe quoi à Ilyas : texte, URL, image, vocal → plan stratégique

import React, { useState, useContext } from "react";
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as ImagePicker from "expo-image-picker";
import { Colors } from "@/constants/colors";
import { BrandContext } from "@/contexts/BrandContext";
import { warRoomApi } from "@/lib/api";

type InputMode = "text" | "url" | "image" | "audio";

const INPUT_MODES: { key: InputMode; icon: string; label: string }[] = [
  { key: "text", icon: "chatbubble-ellipses", label: "Texte" },
  { key: "url", icon: "link", label: "URL" },
  { key: "image", icon: "camera", label: "Image" },
  { key: "audio", icon: "mic", label: "Vocal" },
];

export default function WarRoomScreen({ navigation }: any) {
  const brand = useContext(BrandContext);
  const brandId = brand?.activeBrand?.id;
  const brandName = brand?.activeBrand?.name || "Mon business";

  const [mode, setMode] = useState<InputMode>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [imageNote, setImageNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!brandId) {
      Alert.alert("Erreur", "Aucun brand sélectionné.");
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      let res: any;

      if (mode === "text") {
        if (!text.trim() || text.trim().length < 5) {
          Alert.alert("Erreur", "Saisis au moins 5 caractères.");
          setLoading(false);
          return;
        }
        res = await warRoomApi.analyzeText(brandId, text.trim());
      } else if (mode === "url") {
        if (!url.trim().startsWith("http")) {
          Alert.alert("Erreur", "Colle une URL valide (commence par http).");
          setLoading(false);
          return;
        }
        res = await warRoomApi.analyzeUrl(brandId, url.trim());
      } else if (mode === "image") {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== "granted") {
          Alert.alert("Permission requise", "Accès à la galerie nécessaire.");
          setLoading(false);
          return;
        }
        const picked = await ImagePicker.launchImageLibraryAsync({
          quality: 0.85,
          allowsEditing: false,
        });
        if (picked.canceled) {
          setLoading(false);
          return;
        }
        res = await warRoomApi.analyzeImage(brandId, picked.assets[0], imageNote);
      } else if (mode === "audio") {
        Alert.alert(
          "Vocal",
          "Enregistre ton idée via l'écran Ilyas ou utilise le mode Texte.",
          [{ text: "OK" }]
        );
        setLoading(false);
        return;
      }

      setResult(res?.data?.analysis || res?.analysis);
    } catch (e: any) {
      Alert.alert("Erreur", e?.message || "Analyse échouée. Réessaie.");
    } finally {
      setLoading(false);
    }
  };

  const renderInput = () => {
    switch (mode) {
      case "text":
        return (
          <TextInput
            style={s.textarea}
            value={text}
            onChangeText={setText}
            placeholder="Un client s'est plaint du prix...\nJ'ai vu que notre concurrent fait...\nJ'ai une idée pour..."
            placeholderTextColor={Colors.text.muted}
            multiline
            numberOfLines={5}
          />
        );
      case "url":
        return (
          <>
            <TextInput
              style={s.input}
              value={url}
              onChangeText={setUrl}
              placeholder="https://www.tiktok.com/... ou https://instagram.com/..."
              placeholderTextColor={Colors.text.muted}
              autoCapitalize="none"
              keyboardType="url"
            />
            <TextInput
              style={[s.textarea, { height: 70, marginTop: 10 }]}
              value={text}
              onChangeText={setText}
              placeholder="Note optionnelle : qu'est-ce qui t'intéresse dans ce lien ?"
              placeholderTextColor={Colors.text.muted}
              multiline
            />
          </>
        );
      case "image":
        return (
          <>
            <View style={s.imageHint}>
              <Ionicons name="camera-outline" size={32} color={Colors.brand.primary} />
              <Text style={s.imageHintText}>Tu seras redirigé vers ta galerie</Text>
            </View>
            <TextInput
              style={[s.textarea, { height: 70, marginTop: 10 }]}
              value={imageNote}
              onChangeText={setImageNote}
              placeholder="Note optionnelle : qu'est-ce que tu veux analyser ?"
              placeholderTextColor={Colors.text.muted}
              multiline
            />
          </>
        );
      case "audio":
        return (
          <View style={s.audioHint}>
            <Ionicons name="mic-outline" size={48} color={Colors.text.muted} />
            <Text style={s.audioHintText}>
              Utilise l'écran Ilyas pour envoyer un message vocal, ou tape ton idée en mode Texte.
            </Text>
          </View>
        );
    }
  };

  return (
    <SafeAreaView style={s.container} edges={["top"]}>
      {/* Header */}
      <View style={s.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={s.backBtn}>
          <Ionicons name="chevron-back" size={24} color={Colors.text.primary} />
        </TouchableOpacity>
        <View style={{ flex: 1 }}>
          <Text style={s.title}>War Room</Text>
          <Text style={s.subtitle}>{brandName}</Text>
        </View>
      </View>

      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={s.scroll}>
        {/* Mode selector */}
        <View style={s.modeRow}>
          {INPUT_MODES.map((m) => (
            <TouchableOpacity
              key={m.key}
              style={[s.modeBtn, mode === m.key && s.modeBtnActive]}
              onPress={() => setMode(m.key)}
            >
              <Ionicons
                name={m.icon as any}
                size={20}
                color={mode === m.key ? Colors.brand.primary : Colors.text.muted}
              />
              <Text style={[s.modeLabel, mode === m.key && s.modeLabelActive]}>
                {m.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Input zone */}
        <View style={s.inputZone}>{renderInput()}</View>

        {/* Analyze button */}
        <TouchableOpacity
          style={[s.analyzeBtn, (loading || mode === "audio") && s.analyzeBtnDisabled]}
          onPress={handleAnalyze}
          disabled={loading || mode === "audio"}
        >
          {loading ? (
            <View style={s.loadingRow}>
              <ActivityIndicator color="#FFF" size="small" />
              <Text style={s.analyzeBtnText}> Ilyas analyse...</Text>
            </View>
          ) : (
            <LinearGradient
              colors={Colors.gradient.hero}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={s.analyzeGradient}
            >
              <Text style={s.analyzeBtnText}>Analyser</Text>
            </LinearGradient>
          )}
        </TouchableOpacity>

        {/* Results */}
        {result && (
          <View style={s.resultBox}>
            {/* Ilyas response */}
            {result.ilyas_response && (
              <View style={s.card}>
                <Text style={s.cardLabel}>Ilyas</Text>
                <Text style={s.cardText}>{result.ilyas_response}</Text>
              </View>
            )}

            {/* Action plan */}
            {result.action_plan && (
              <View style={s.card}>
                <Text style={s.cardTitle}>Plan d'action</Text>

                {(result.action_plan.this_week?.length > 0 ||
                  result.action_plan.immediate) && (
                  <View style={s.planBlock}>
                    <Text style={s.planPeriod}>Cette semaine</Text>
                    {result.action_plan.immediate && (
                      <Text style={s.planItem}>
                        {"\u2022"} {result.action_plan.immediate}
                      </Text>
                    )}
                    {result.action_plan.this_week?.map((a: string, i: number) => (
                      <Text key={i} style={s.planItem}>
                        {"\u2022"} {a}
                      </Text>
                    ))}
                  </View>
                )}
                {result.action_plan.this_month?.length > 0 && (
                  <View style={s.planBlock}>
                    <Text style={s.planPeriod}>Ce mois</Text>
                    {result.action_plan.this_month.map((a: string, i: number) => (
                      <Text key={i} style={s.planItem}>
                        {"\u2022"} {a}
                      </Text>
                    ))}
                  </View>
                )}
                {result.action_plan.next_3_months?.length > 0 && (
                  <View style={s.planBlock}>
                    <Text style={s.planPeriod}>3 mois</Text>
                    {result.action_plan.next_3_months.map((a: string, i: number) => (
                      <Text key={i} style={s.planItem}>
                        {"\u2022"} {a}
                      </Text>
                    ))}
                  </View>
                )}
              </View>
            )}

            {/* Revenue impact */}
            {(result.revenue_impact || result.revenue_connection) && (
              <View style={[s.card, s.moneyCard]}>
                <Text style={s.moneyTitle}>Impact business</Text>
                <Text style={s.moneyText}>
                  {result.revenue_impact || result.revenue_connection}
                </Text>
              </View>
            )}

            {/* Content ideas */}
            {(result.content_ideas?.length > 0 ||
              result.content_opportunities?.length > 0) && (
              <View style={s.card}>
                <Text style={s.cardTitle}>Idées de contenu</Text>
                {(result.content_ideas || result.content_opportunities)?.map(
                  (idea: string, i: number) => (
                    <Text key={i} style={s.planItem}>
                      {"\u2022"} {idea}
                    </Text>
                  )
                )}
              </View>
            )}

            {/* Caption (image analysis) */}
            {result.caption_instagram && (
              <View style={s.card}>
                <Text style={s.cardTitle}>Caption Instagram prête</Text>
                <Text style={s.cardText}>{result.caption_instagram}</Text>
                {result.hashtags?.length > 0 && (
                  <Text style={s.hashtagText}>{result.hashtags.join(" ")}</Text>
                )}
              </View>
            )}

            {/* Transcript (audio) */}
            {result.transcript && (
              <View style={s.card}>
                <Text style={s.cardLabel}>Transcription</Text>
                <Text style={s.transcriptText}>{result.transcript}</Text>
              </View>
            )}
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg.primary },
  header: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.default,
  },
  backBtn: { marginRight: 8 },
  title: { fontSize: 22, fontWeight: "800", color: Colors.text.primary },
  subtitle: { fontSize: 12, color: Colors.text.secondary, marginTop: 1 },
  scroll: { padding: 16 },
  modeRow: { flexDirection: "row", gap: 8, marginBottom: 20 },
  modeBtn: {
    flex: 1,
    backgroundColor: Colors.bg.secondary,
    borderRadius: 12,
    padding: 12,
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  modeBtnActive: {
    borderColor: Colors.brand.primary,
    backgroundColor: Colors.brand.primary + "10",
  },
  modeLabel: {
    color: Colors.text.muted,
    fontSize: 11,
    fontWeight: "600",
    marginTop: 4,
  },
  modeLabelActive: { color: Colors.brand.primary },
  inputZone: { marginBottom: 16 },
  textarea: {
    backgroundColor: Colors.bg.secondary,
    color: Colors.text.primary,
    borderRadius: 12,
    padding: 14,
    height: 120,
    textAlignVertical: "top",
    borderWidth: 1,
    borderColor: Colors.border.default,
    fontSize: 14,
  },
  input: {
    backgroundColor: Colors.bg.secondary,
    color: Colors.text.primary,
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.border.default,
    fontSize: 14,
  },
  imageHint: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 12,
    padding: 24,
    alignItems: "center",
    borderWidth: 1,
    borderColor: Colors.brand.primary,
    borderStyle: "dashed",
  },
  imageHintText: {
    color: Colors.text.secondary,
    fontWeight: "600",
    marginTop: 8,
  },
  audioHint: { alignItems: "center", padding: 30 },
  audioHintText: {
    color: Colors.text.muted,
    textAlign: "center",
    lineHeight: 22,
    marginTop: 12,
  },
  analyzeBtn: { borderRadius: 14, overflow: "hidden", marginBottom: 24 },
  analyzeBtnDisabled: { opacity: 0.5 },
  analyzeGradient: {
    paddingVertical: 16,
    alignItems: "center",
    borderRadius: 14,
  },
  analyzeBtnText: { color: "#FFF", fontWeight: "800", fontSize: 16 },
  loadingRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 16,
  },
  resultBox: { gap: 12 },
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border.default,
  },
  cardLabel: {
    color: Colors.brand.primary,
    fontWeight: "700",
    fontSize: 12,
    marginBottom: 8,
  },
  cardTitle: {
    color: Colors.text.primary,
    fontWeight: "700",
    fontSize: 16,
    marginBottom: 12,
  },
  cardText: {
    color: Colors.text.primary,
    fontSize: 14,
    lineHeight: 22,
  },
  planBlock: { marginBottom: 12 },
  planPeriod: {
    color: Colors.brand.primary,
    fontWeight: "600",
    fontSize: 13,
    marginBottom: 6,
  },
  planItem: {
    color: Colors.text.secondary,
    fontSize: 13,
    lineHeight: 22,
    paddingLeft: 4,
  },
  moneyCard: {
    backgroundColor: "#ECFDF5",
    borderColor: "#10B98130",
  },
  moneyTitle: {
    color: Colors.status.success,
    fontWeight: "700",
    fontSize: 14,
    marginBottom: 6,
  },
  moneyText: {
    color: Colors.text.secondary,
    fontSize: 13,
    lineHeight: 20,
  },
  hashtagText: {
    color: Colors.brand.primary,
    fontSize: 12,
    marginTop: 8,
  },
  transcriptText: {
    color: Colors.text.muted,
    fontSize: 12,
    fontStyle: "italic",
  },
});
