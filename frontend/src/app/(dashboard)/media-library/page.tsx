"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ImageIcon,
  Video,
  Mic,
  Trash2,
  Eye,
  Tag,
  MessageSquare,
  HardDrive,
  Archive,
  ArchiveRestore,
  Download,
} from "lucide-react";
import { mediaLibraryApi, mediaApi } from "@/lib/api";
import { MediaAsset, VoiceNote, MediaLibraryStats } from "@/types";
import { cn } from "@/lib/utils";

type Tab = "images" | "videos" | "voice-notes";

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024)
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function MediaLibraryPage() {
  const [activeTab, setActiveTab] = useState<Tab>("images");
  const [images, setImages] = useState<MediaAsset[]>([]);
  const [videos, setVideos] = useState<MediaAsset[]>([]);
  const [voiceNotes, setVoiceNotes] = useState<VoiceNote[]>([]);
  const [stats, setStats] = useState<MediaLibraryStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState<MediaAsset | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<VoiceNote | null>(null);

  const brandId =
    typeof window !== "undefined" ? localStorage.getItem("brand_id") : null;

  useEffect(() => {
    if (!brandId) return;
    loadData();
  }, [brandId]);

  async function loadData() {
    if (!brandId) return;
    setIsLoading(true);
    try {
      const [imagesRes, videosRes, voiceRes, statsRes] = await Promise.all([
        mediaLibraryApi.listAssets(brandId, { media_type: "image", limit: 100 }),
        mediaLibraryApi.listAssets(brandId, { media_type: "video", limit: 100 }),
        mediaLibraryApi.listVoiceNotes(brandId, { limit: 100 }),
        mediaLibraryApi.getStats(brandId),
      ]);
      setImages(imagesRes.data);
      setVideos(videosRes.data);
      setVoiceNotes(voiceRes.data);
      setStats(statsRes.data);
    } catch (err) {
      console.error("Failed to load media library", err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDeleteAsset(assetId: string) {
    try {
      await mediaLibraryApi.deleteAsset(assetId);
      setImages((prev) => prev.filter((a) => a.id !== assetId));
      setVideos((prev) => prev.filter((a) => a.id !== assetId));
      setSelectedAsset(null);
      loadData();
    } catch (err) {
      console.error("Delete failed", err);
    }
  }

  async function handleArchiveAsset(assetId: string, archive: boolean) {
    try {
      await mediaLibraryApi.updateAsset(assetId, { is_archived: archive });
      loadData();
    } catch (err) {
      console.error("Archive failed", err);
    }
  }

  async function handleDeleteVoiceNote(noteId: string) {
    try {
      await mediaLibraryApi.deleteVoiceNote(noteId);
      setVoiceNotes((prev) => prev.filter((n) => n.id !== noteId));
      setSelectedVoice(null);
      loadData();
    } catch (err) {
      console.error("Delete failed", err);
    }
  }

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!brandId || !e.target.files?.length) return;
    const file = e.target.files[0];
    try {
      await mediaApi.upload(brandId, file);
      loadData();
    } catch (err) {
      console.error("Upload failed", err);
    }
  }

  const tabs = [
    {
      id: "images" as Tab,
      label: "Images",
      icon: ImageIcon,
      count: stats?.total_images || 0,
    },
    {
      id: "videos" as Tab,
      label: "Videos",
      icon: Video,
      count: stats?.total_videos || 0,
    },
    {
      id: "voice-notes" as Tab,
      label: "Notes vocales",
      icon: Mic,
      count: stats?.total_voice_notes || 0,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Media Library</h1>
          <p className="text-muted-foreground">
            Gerez vos images, videos et notes vocales
          </p>
        </div>
        <div>
          <label htmlFor="upload-input">
            <Button variant="gradient" asChild>
              <span>
                <Download className="w-4 h-4 mr-2 rotate-180" />
                Importer
              </span>
            </Button>
          </label>
          <input
            id="upload-input"
            type="file"
            accept="image/*,video/*"
            className="hidden"
            onChange={handleUpload}
          />
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bento-card">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <ImageIcon className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total_images}</p>
                <p className="text-xs text-muted-foreground">Images</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bento-card">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center">
                <Video className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total_videos}</p>
                <p className="text-xs text-muted-foreground">Videos</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bento-card">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                <Mic className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">{stats.total_voice_notes}</p>
                <p className="text-xs text-muted-foreground">Notes vocales</p>
              </div>
            </CardContent>
          </Card>
          <Card className="bento-card">
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-orange-500/10 flex items-center justify-center">
                <HardDrive className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {formatFileSize(stats.total_size_bytes)}
                </p>
                <p className="text-xs text-muted-foreground">Stockage</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted"
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
            <span className="ml-1 text-xs bg-muted px-2 py-0.5 rounded-full">
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="text-center py-12 text-muted-foreground">
          Chargement...
        </div>
      ) : (
        <>
          {/* Images Grid */}
          {activeTab === "images" && (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {images.length > 0 ? (
                images.map((asset, index) => (
                  <motion.div
                    key={asset.id}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.03 }}
                  >
                    <Card
                      className={cn(
                        "bento-card overflow-hidden cursor-pointer group",
                        selectedAsset?.id === asset.id && "ring-2 ring-primary"
                      )}
                      onClick={() => setSelectedAsset(asset)}
                    >
                      <div className="aspect-square relative">
                        <img
                          src={asset.public_url}
                          alt={asset.ai_description || "Media"}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-end">
                          <div className="w-full p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="flex gap-1">
                              {asset.source === "whatsapp" && (
                                <span className="text-[10px] bg-green-500/80 text-white px-1.5 py-0.5 rounded">
                                  WhatsApp
                                </span>
                              )}
                              {asset.ai_analyzed && (
                                <span className="text-[10px] bg-blue-500/80 text-white px-1.5 py-0.5 rounded">
                                  AI
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                      <CardContent className="p-2">
                        <p className="text-xs text-muted-foreground truncate">
                          {asset.ai_description ||
                            asset.original_filename ||
                            formatDate(asset.created_at)}
                        </p>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))
              ) : (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  <ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Aucune image</p>
                  <p className="text-sm mt-1">
                    Envoyez des photos via WhatsApp ou importez-les
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Videos Grid */}
          {activeTab === "videos" && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {videos.length > 0 ? (
                videos.map((asset, index) => (
                  <motion.div
                    key={asset.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card
                      className={cn(
                        "bento-card overflow-hidden cursor-pointer",
                        selectedAsset?.id === asset.id && "ring-2 ring-primary"
                      )}
                      onClick={() => setSelectedAsset(asset)}
                    >
                      <div className="aspect-video relative bg-muted flex items-center justify-center">
                        <Video className="w-12 h-12 text-muted-foreground/30" />
                        <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded">
                          {asset.duration_seconds
                            ? `${Math.floor(asset.duration_seconds / 60)}:${String(
                                Math.floor(asset.duration_seconds % 60)
                              ).padStart(2, "0")}`
                            : formatFileSize(asset.file_size)}
                        </div>
                        {asset.source === "whatsapp" && (
                          <div className="absolute top-2 left-2">
                            <span className="text-[10px] bg-green-500/80 text-white px-1.5 py-0.5 rounded">
                              WhatsApp
                            </span>
                          </div>
                        )}
                      </div>
                      <CardContent className="p-3">
                        <p className="text-sm truncate">
                          {asset.original_filename || `Video ${formatDate(asset.created_at)}`}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatDate(asset.created_at)}
                        </p>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))
              ) : (
                <div className="col-span-full text-center py-12 text-muted-foreground">
                  <Video className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Aucune video</p>
                  <p className="text-sm mt-1">
                    Envoyez des videos via WhatsApp ou importez-les
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Voice Notes List */}
          {activeTab === "voice-notes" && (
            <div className="space-y-3">
              {voiceNotes.length > 0 ? (
                voiceNotes.map((note, index) => (
                  <motion.div
                    key={note.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.05 }}
                  >
                    <Card
                      className={cn(
                        "bento-card cursor-pointer",
                        selectedVoice?.id === note.id && "ring-2 ring-primary"
                      )}
                      onClick={() => setSelectedVoice(note)}
                    >
                      <CardContent className="p-4 flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center shrink-0">
                          <Mic className="w-5 h-5 text-green-500" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium">
                              Note vocale
                            </span>
                            {note.is_transcribed && (
                              <span className="text-[10px] bg-blue-500/80 text-white px-1.5 py-0.5 rounded">
                                Transcrit
                              </span>
                            )}
                            {note.sender_phone && (
                              <span className="text-[10px] bg-green-500/80 text-white px-1.5 py-0.5 rounded">
                                WhatsApp
                              </span>
                            )}
                          </div>
                          {note.transcription ? (
                            <p className="text-sm text-muted-foreground line-clamp-2">
                              {note.transcription}
                            </p>
                          ) : (
                            <p className="text-sm text-muted-foreground italic">
                              Transcription non disponible
                            </p>
                          )}
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            <span>{formatDate(note.created_at)}</span>
                            <span>{formatFileSize(note.file_size)}</span>
                            {note.duration_seconds && (
                              <span>
                                {Math.floor(note.duration_seconds / 60)}:
                                {String(
                                  Math.floor(note.duration_seconds % 60)
                                ).padStart(2, "0")}
                              </span>
                            )}
                          </div>
                          {note.parsed_instructions && (
                            <div className="mt-2 p-2 bg-muted/50 rounded text-xs">
                              <span className="font-medium">Instructions: </span>
                              {note.parsed_instructions.caption_directive && (
                                <span className="text-muted-foreground">
                                  {String(note.parsed_instructions.caption_directive).slice(0, 100)}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="shrink-0"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteVoiceNote(note.id);
                          }}
                        >
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <Mic className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p>Aucune note vocale</p>
                  <p className="text-sm mt-1">
                    Envoyez un message vocal via WhatsApp pour commencer
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Asset Detail Panel */}
      {selectedAsset && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-4 right-4 w-80 z-50"
        >
          <Card className="glass-card shadow-xl">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Details</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedAsset(null)}
                >
                  Fermer
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {selectedAsset.media_type === "image" && (
                <img
                  src={selectedAsset.public_url}
                  alt="Preview"
                  className="w-full rounded-lg object-cover max-h-48"
                />
              )}
              {selectedAsset.ai_description && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Description IA
                  </p>
                  <p className="text-sm">{selectedAsset.ai_description}</p>
                </div>
              )}
              {selectedAsset.ai_tags && selectedAsset.ai_tags.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-muted-foreground mb-1">
                    Tags
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {selectedAsset.ai_tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs bg-muted px-2 py-0.5 rounded-full"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              <div className="text-xs text-muted-foreground space-y-1">
                <p>Source: {selectedAsset.source}</p>
                <p>Taille: {formatFileSize(selectedAsset.file_size)}</p>
                <p>Date: {formatDate(selectedAsset.created_at)}</p>
                {selectedAsset.width && selectedAsset.height && (
                  <p>
                    Dimensions: {selectedAsset.width}x{selectedAsset.height}
                  </p>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  onClick={() =>
                    handleArchiveAsset(
                      selectedAsset.id,
                      !selectedAsset.is_archived
                    )
                  }
                >
                  {selectedAsset.is_archived ? (
                    <>
                      <ArchiveRestore className="w-3 h-3 mr-1" />
                      Restaurer
                    </>
                  ) : (
                    <>
                      <Archive className="w-3 h-3 mr-1" />
                      Archiver
                    </>
                  )}
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleDeleteAsset(selectedAsset.id)}
                >
                  <Trash2 className="w-3 h-3 mr-1" />
                  Supprimer
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
