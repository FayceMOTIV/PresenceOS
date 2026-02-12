"use client";

import { useState, useCallback } from "react";
import { aiApi } from "@/lib/api";
import type {
  CaptionStyle,
  ToneOption,
  PhotoCaptionSuggestion,
  ImageAnalysis,
  EngagementScore,
  PhotoCaptionsResponse,
} from "@/types";

export type PhotoCaptionStep = "upload" | "analyzing" | "suggestions" | "editing" | "validating";

export function usePhotoCaptions() {
  // Step state
  const [step, setStep] = useState<PhotoCaptionStep>("upload");

  // Photo state
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreviewUrl, setPhotoPreviewUrl] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);

  // Analysis state
  const [imageAnalysis, setImageAnalysis] = useState<ImageAnalysis | null>(null);
  const [suggestions, setSuggestions] = useState<PhotoCaptionSuggestion[]>([]);
  const [engagementScores, setEngagementScores] = useState<Record<string, EngagementScore>>({});

  // Editing state
  const [selectedStyle, setSelectedStyle] = useState<CaptionStyle | null>(null);
  const [editedCaption, setEditedCaption] = useState("");
  const [editedHashtags, setEditedHashtags] = useState<string[]>([]);
  const [currentTone, setCurrentTone] = useState<ToneOption | null>(null);

  // Platform state
  const [platforms, setPlatforms] = useState<string[]>(["instagram_post"]);

  // Loading states
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRegeneratingHashtags, setIsRegeneratingHashtags] = useState(false);
  const [isChangingTone, setIsChangingTone] = useState(false);
  const [isSuggestingEmojis, setIsSuggestingEmojis] = useState(false);

  // Error state
  const [error, setError] = useState<string | null>(null);

  const getBrandId = () => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("brand_id") || "";
    }
    return "";
  };

  // Core action: upload photo and get 3 captions
  const uploadAndAnalyze = useCallback(async (file: File) => {
    setPhotoFile(file);
    setPhotoPreviewUrl(URL.createObjectURL(file));
    setStep("analyzing");
    setIsAnalyzing(true);
    setError(null);

    try {
      const brandId = getBrandId();
      if (!brandId) {
        throw new Error("Aucune marque configuree. Completez l'onboarding d'abord.");
      }
      const res = await aiApi.generatePhotoCaptions(brandId, file, platforms.join(","));
      const data: PhotoCaptionsResponse = res.data;

      setPhotoUrl(data.photo_url);
      setImageAnalysis(data.image_analysis);
      setSuggestions(data.suggestions);
      setEngagementScores(data.engagement_scores);
      setStep("suggestions");
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Erreur lors de l'analyse. Reessaie !");
      setStep("upload");
    } finally {
      setIsAnalyzing(false);
    }
  }, [platforms]);

  // Select a suggestion and move to editing
  const selectSuggestion = useCallback((style: CaptionStyle) => {
    const suggestion = suggestions.find((s) => s.style === style);
    if (suggestion) {
      setSelectedStyle(style);
      setEditedCaption(suggestion.caption);
      setEditedHashtags(suggestion.hashtags);
      setCurrentTone(null);
      setStep("editing");
    }
  }, [suggestions]);

  // Regenerate hashtags
  const regenerateHashtags = useCallback(async () => {
    setIsRegeneratingHashtags(true);
    try {
      const brandId = getBrandId();
      const res = await aiApi.regenerateHashtags(brandId, {
        caption: editedCaption,
        platform: platforms[0],
        count: 10,
      });
      setEditedHashtags(res.data.hashtags);
    } catch (err: any) {
      setError("Erreur lors de la regeneration des hashtags");
    } finally {
      setIsRegeneratingHashtags(false);
    }
  }, [editedCaption, platforms]);

  // Change tone
  const changeTone = useCallback(async (tone: ToneOption) => {
    setIsChangingTone(true);
    try {
      const brandId = getBrandId();
      const res = await aiApi.changeTone(brandId, {
        caption: editedCaption,
        tone,
        platform: platforms[0],
      });
      setEditedCaption(res.data.caption);
      setCurrentTone(tone);
    } catch (err: any) {
      setError("Erreur lors du changement de ton");
    } finally {
      setIsChangingTone(false);
    }
  }, [editedCaption, platforms]);

  // Suggest emojis
  const suggestEmojis = useCallback(async () => {
    setIsSuggestingEmojis(true);
    try {
      const brandId = getBrandId();
      const res = await aiApi.suggestEmojis(brandId, {
        caption: editedCaption,
      });
      setEditedCaption(res.data.caption_with_emojis);
    } catch (err: any) {
      setError("Erreur lors de la suggestion d'emojis");
    } finally {
      setIsSuggestingEmojis(false);
    }
  }, [editedCaption]);

  // Refresh engagement score for current caption
  const refreshEngagementScore = useCallback(async () => {
    try {
      const brandId = getBrandId();
      const res = await aiApi.getEngagementScore(brandId, {
        caption: editedCaption,
        hashtags: editedHashtags,
        platform: platforms[0],
      });
      setEngagementScores((prev) => ({
        ...prev,
        current: res.data,
      }));
    } catch {
      // Silent fail — engagement score is non-critical
    }
  }, [editedCaption, editedHashtags, platforms]);

  // Navigate to validation
  const goToValidation = useCallback(() => {
    setStep("validating");
    refreshEngagementScore();
  }, [refreshEngagementScore]);

  // Back navigation
  const goBackToSuggestions = useCallback(() => {
    setStep("suggestions");
  }, []);

  const goBackToEditing = useCallback(() => {
    setStep("editing");
  }, []);

  // Reset everything
  const reset = useCallback(() => {
    setStep("upload");
    setPhotoFile(null);
    if (photoPreviewUrl) URL.revokeObjectURL(photoPreviewUrl);
    setPhotoPreviewUrl(null);
    setPhotoUrl(null);
    setImageAnalysis(null);
    setSuggestions([]);
    setEngagementScores({});
    setSelectedStyle(null);
    setEditedCaption("");
    setEditedHashtags([]);
    setCurrentTone(null);
    setError(null);
  }, [photoPreviewUrl]);

  // Regenerate all 3 captions
  const regenerateAll = useCallback(async () => {
    if (!photoFile) return;
    await uploadAndAnalyze(photoFile);
  }, [photoFile, uploadAndAnalyze]);

  return {
    // State
    step,
    photoFile,
    photoPreviewUrl,
    photoUrl,
    imageAnalysis,
    suggestions,
    engagementScores,
    selectedStyle,
    editedCaption,
    setEditedCaption,
    editedHashtags,
    setEditedHashtags,
    currentTone,
    platforms,
    setPlatforms,
    error,

    // Loading
    isAnalyzing,
    isRegeneratingHashtags,
    isChangingTone,
    isSuggestingEmojis,

    // Actions
    uploadAndAnalyze,
    selectSuggestion,
    regenerateHashtags,
    changeTone,
    suggestEmojis,
    refreshEngagementScore,
    goToValidation,
    goBackToSuggestions,
    goBackToEditing,
    reset,
    regenerateAll,
  };
}
