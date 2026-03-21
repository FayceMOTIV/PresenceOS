// PresenceOS Mobile — VideoPlanCard
// Reusable card for the cinematic video generation flow.
// States: idle → generating → preview → publishing → done (+ error)

import React, { useState, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  TextInput,
} from "react-native";
import {
  generateCinematicVideo,
  publishVideo,
  saveVideoAsDraft,
  CinematicVideoResult,
} from "@/services/videoApi";
import { Colors } from "@/constants/colors";

// ── Types ──

interface VideoPlanCardProps {
  brandId: string;
  dishName: string;
  platform?: "instagram" | "tiktok" | "facebook";
}

type CardState =
  | "idle"
  | "generating"
  | "error"
  | "preview"
  | "publishing"
  | "done";

// ── Component ──

export default function VideoPlanCard({
  brandId,
  dishName,
  platform = "instagram",
}: VideoPlanCardProps) {
  const [state, setState] = useState<CardState>("idle");
  const [result, setResult] = useState<CinematicVideoResult | null>(null);
  const [caption, setCaption] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  // ── Generate ──

  const handleGenerate = useCallback(async () => {
    setState("generating");
    setErrorMessage("");

    const response = await generateCinematicVideo(brandId, dishName);

    if (!response || !response.success) {
      setState("error");
      setErrorMessage(
        "La génération a échoué. Vérifiez votre connexion et réessayez.",
      );
      return;
    }

    setResult(response);
    setCaption(
      `🍽️ ${dishName} — découvrez notre plat du jour ! #restaurant #food`,
    );
    setState("preview");
  }, [brandId, dishName]);

  // ── Publish ──

  const handlePublish = useCallback(async () => {
    if (!result?.video_url) return;

    setState("publishing");

    const response = await publishVideo(
      brandId,
      result.video_url,
      caption,
      platform,
    );

    if (!response || !response.success) {
      Alert.alert(
        "Erreur",
        "La publication a échoué. Réessayez dans quelques instants.",
      );
      setState("preview");
      return;
    }

    setState("done");
  }, [brandId, result, caption, platform]);

  // ── Save as Draft ──

  const handleSave = useCallback(async () => {
    if (!result?.video_url) return;

    const response = await saveVideoAsDraft(
      brandId,
      result.video_url,
      caption,
      platform,
    );

    if (!response || !response.success) {
      Alert.alert("Erreur", "Impossible de sauvegarder le brouillon.");
      return;
    }

    Alert.alert("Brouillon sauvegardé", "La vidéo a été enregistrée.");
  }, [brandId, result, caption, platform]);

  // ── Reset ──

  const handleReset = useCallback(() => {
    setState("idle");
    setResult(null);
    setCaption("");
    setErrorMessage("");
  }, []);

  // ── Render by State ──

  const renderContent = () => {
    switch (state) {
      case "idle":
        return (
          <View>
            <Text style={styles.dishName}>{dishName}</Text>
            <Text style={styles.meta}>
              Vidéo cinématique Kling 2.6 Pro • ~$0.35
            </Text>
            <TouchableOpacity
              style={styles.amberButton}
              onPress={handleGenerate}
              activeOpacity={0.8}
            >
              <Text style={styles.amberButtonText}>Générer la vidéo</Text>
            </TouchableOpacity>
          </View>
        );

      case "generating":
        return (
          <View style={styles.centeredContent}>
            <ActivityIndicator size="large" color={Colors.brand.amber} />
            <Text style={styles.generatingTitle}>Création en cours…</Text>
            <Text style={styles.generatingSubtext}>
              3 clips Kling 2.6 Pro • 45-90 secondes
            </Text>
          </View>
        );

      case "error":
        return (
          <View>
            <Text style={styles.dishName}>{dishName}</Text>
            <Text style={styles.errorText}>{errorMessage}</Text>
            <TouchableOpacity
              style={styles.amberButton}
              onPress={handleGenerate}
              activeOpacity={0.8}
            >
              <Text style={styles.amberButtonText}>Réessayer</Text>
            </TouchableOpacity>
          </View>
        );

      case "preview":
        return (
          <View>
            <Text style={styles.successText}>
              {result?.clips_count ?? 3} clips générés •{" "}
              ${result?.cost_usd?.toFixed(2) ?? "0.35"}
            </Text>
            {result?.video_url ? (
              <Text style={styles.videoUrlText} numberOfLines={1}>
                {result.video_url}
              </Text>
            ) : null}
            <Text style={styles.captionLabel}>Légende</Text>
            <TextInput
              style={styles.captionInput}
              value={caption}
              onChangeText={setCaption}
              multiline
              textAlignVertical="top"
              placeholder="Ajoutez une légende…"
              placeholderTextColor={Colors.text.muted}
            />
            <View style={styles.previewActions}>
              <TouchableOpacity
                style={styles.amberButton}
                onPress={handlePublish}
                activeOpacity={0.8}
              >
                <Text style={styles.amberButtonText}>Publier</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.outlinedButton}
                onPress={handleSave}
                activeOpacity={0.8}
              >
                <Text style={styles.outlinedButtonText}>Sauver</Text>
              </TouchableOpacity>
            </View>
          </View>
        );

      case "publishing":
        return (
          <View style={styles.centeredContent}>
            <ActivityIndicator size="small" color={Colors.brand.amber} />
            <Text style={styles.generatingTitle}>Publication en cours…</Text>
          </View>
        );

      case "done":
        return (
          <View style={styles.centeredContent}>
            <Text style={styles.doneText}>
              Vidéo publiée sur {platform} !
            </Text>
            <TouchableOpacity
              style={styles.amberButton}
              onPress={handleReset}
              activeOpacity={0.8}
            >
              <Text style={styles.amberButtonText}>Nouvelle vidéo</Text>
            </TouchableOpacity>
          </View>
        );
    }
  };

  return <View style={styles.card}>{renderContent()}</View>;
}

// ── Styles ──

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.secondary,
    borderRadius: 16,
    padding: 20,
    marginVertical: 8,
    marginHorizontal: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 3,
  },

  // ── Text ──
  dishName: {
    fontSize: 18,
    fontWeight: "700",
    color: Colors.text.primary,
    marginBottom: 4,
  },
  meta: {
    fontSize: 13,
    color: Colors.text.muted,
    marginBottom: 16,
  },

  // ── Generating ──
  centeredContent: {
    alignItems: "center",
    paddingVertical: 12,
  },
  generatingTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.text.primary,
    marginTop: 12,
  },
  generatingSubtext: {
    fontSize: 13,
    color: Colors.text.muted,
    marginTop: 4,
  },

  // ── Error ──
  errorText: {
    fontSize: 14,
    color: Colors.status.danger,
    marginBottom: 16,
  },

  // ── Preview ──
  successText: {
    fontSize: 15,
    fontWeight: "600",
    color: Colors.status.success,
    marginBottom: 8,
  },
  videoUrlText: {
    fontSize: 12,
    color: Colors.text.muted,
    marginBottom: 12,
  },
  captionLabel: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.text.secondary,
    marginBottom: 6,
  },
  captionInput: {
    borderWidth: 1,
    borderColor: Colors.border.default,
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: Colors.text.primary,
    minHeight: 80,
    marginBottom: 16,
    backgroundColor: Colors.bg.primary,
  },
  previewActions: {
    flexDirection: "row",
    gap: 12,
  },

  // ── Buttons ──
  amberButton: {
    flex: 1,
    backgroundColor: Colors.brand.amber,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  amberButtonText: {
    fontSize: 15,
    fontWeight: "700",
    color: "#FFFFFF",
  },
  outlinedButton: {
    flex: 1,
    borderWidth: 2,
    borderColor: Colors.brand.amber,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    backgroundColor: "transparent",
  },
  outlinedButtonText: {
    fontSize: 15,
    fontWeight: "700",
    color: Colors.brand.amber,
  },

  // ── Done ──
  doneText: {
    fontSize: 16,
    fontWeight: "600",
    color: Colors.status.success,
    marginBottom: 16,
    textAlign: "center",
  },
});
