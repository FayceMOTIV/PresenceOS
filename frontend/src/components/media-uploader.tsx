"use client";

import { useState, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  X,
  Image as ImageIcon,
  Video,
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { mediaApi } from "@/lib/api";

interface MediaFile {
  id: string;
  file: File;
  preview: string;
  status: "pending" | "uploading" | "success" | "error";
  progress: number;
  url?: string;
  key?: string;
  error?: string;
}

interface MediaUploaderProps {
  brandId: string;
  maxFiles?: number;
  acceptImages?: boolean;
  acceptVideos?: boolean;
  onUploadComplete?: (files: { url: string; key: string; type: string }[]) => void;
  className?: string;
}

const ACCEPTED_IMAGE_TYPES = [
  "image/jpeg",
  "image/png",
  "image/gif",
  "image/webp",
];

const ACCEPTED_VIDEO_TYPES = [
  "video/mp4",
  "video/quicktime",
  "video/webm",
];

export function MediaUploader({
  brandId,
  maxFiles = 10,
  acceptImages = true,
  acceptVideos = true,
  onUploadComplete,
  className,
}: MediaUploaderProps) {
  const [files, setFiles] = useState<MediaFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const acceptedTypes = [
    ...(acceptImages ? ACCEPTED_IMAGE_TYPES : []),
    ...(acceptVideos ? ACCEPTED_VIDEO_TYPES : []),
  ];

  const validateFile = (file: File): string | null => {
    if (!acceptedTypes.includes(file.type)) {
      return "Type de fichier non supporte";
    }

    const isVideo = file.type.startsWith("video/");
    const maxSize = isVideo ? 500 * 1024 * 1024 : 20 * 1024 * 1024;

    if (file.size > maxSize) {
      return `Fichier trop volumineux (max ${isVideo ? "500" : "20"} MB)`;
    }

    return null;
  };

  const createPreview = (file: File): string => {
    return URL.createObjectURL(file);
  };

  const addFiles = useCallback(
    (newFiles: FileList | File[]) => {
      const fileArray = Array.from(newFiles);
      const remainingSlots = maxFiles - files.length;

      if (remainingSlots <= 0) return;

      const filesToAdd = fileArray.slice(0, remainingSlots);

      const mediaFiles: MediaFile[] = filesToAdd.map((file) => {
        const error = validateFile(file);
        return {
          id: Math.random().toString(36).substring(7),
          file,
          preview: error ? "" : createPreview(file),
          status: error ? "error" as const : "pending" as const,
          progress: 0,
          error: error || undefined,
        };
      });

      setFiles((prev) => [...prev, ...mediaFiles]);

      // Auto-upload valid files
      mediaFiles
        .filter((f) => f.status === "pending")
        .forEach((mediaFile) => uploadFile(mediaFile));
    },
    [files.length, maxFiles]
  );

  const uploadFile = async (mediaFile: MediaFile) => {
    setFiles((prev) =>
      prev.map((f) =>
        f.id === mediaFile.id ? { ...f, status: "uploading", progress: 0 } : f
      )
    );

    try {
      // Simulate progress (actual progress would require XHR or fetch with ReadableStream)
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === mediaFile.id && f.status === "uploading"
              ? { ...f, progress: Math.min(f.progress + 10, 90) }
              : f
          )
        );
      }, 100);

      const response = await mediaApi.upload(brandId, mediaFile.file);

      clearInterval(progressInterval);

      setFiles((prev) =>
        prev.map((f) =>
          f.id === mediaFile.id
            ? {
                ...f,
                status: "success",
                progress: 100,
                url: response.data.url,
                key: response.data.key,
              }
            : f
        )
      );

      // Notify parent of completed uploads
      setTimeout(() => {
        setFiles((currentFiles) => {
          const completedFiles = currentFiles.filter((f) => f.status === "success");
          if (completedFiles.length > 0 && onUploadComplete) {
            onUploadComplete(
              completedFiles.map((f) => ({
                url: f.url!,
                key: f.key!,
                type: f.file.type.startsWith("video/") ? "video" : "image",
              }))
            );
          }
          return currentFiles;
        });
      }, 500);
    } catch (error: any) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === mediaFile.id
            ? {
                ...f,
                status: "error",
                progress: 0,
                error: error.response?.data?.detail || "Erreur lors de l'upload",
              }
            : f
        )
      );
    }
  };

  const removeFile = (id: string) => {
    setFiles((prev) => {
      const file = prev.find((f) => f.id === id);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter((f) => f.id !== id);
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(e.dataTransfer.files);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      addFiles(e.target.files);
    }
    // Reset input so same file can be selected again
    e.target.value = "";
  };

  const successfulUploads = files.filter((f) => f.status === "success");
  const isUploading = files.some((f) => f.status === "uploading");

  return (
    <div className={cn("space-y-4", className)}>
      {/* Drop Zone */}
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer",
          isDragging
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-muted-foreground/50",
          files.length >= maxFiles && "opacity-50 cursor-not-allowed"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={files.length < maxFiles ? handleClick : undefined}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={acceptedTypes.join(",")}
          onChange={handleFileChange}
          className="hidden"
        />

        <div className="flex flex-col items-center gap-2 text-center">
          <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center">
            <Upload className="w-6 h-6 text-muted-foreground" />
          </div>
          <div>
            <p className="font-medium">
              Glissez-deposez ou cliquez pour ajouter
            </p>
            <p className="text-sm text-muted-foreground">
              {acceptImages && acceptVideos
                ? "Images et videos"
                : acceptImages
                ? "Images uniquement"
                : "Videos uniquement"}
              {" • "}
              {maxFiles - files.length} fichier{maxFiles - files.length !== 1 ? "s" : ""} restant
            </p>
          </div>
        </div>
      </div>

      {/* File Preview Grid */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3"
          >
            {files.map((mediaFile) => (
              <motion.div
                key={mediaFile.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="relative group"
              >
                <div className="aspect-square rounded-lg overflow-hidden bg-muted">
                  {mediaFile.preview ? (
                    mediaFile.file.type.startsWith("video/") ? (
                      <video
                        src={mediaFile.preview}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <img
                        src={mediaFile.preview}
                        alt=""
                        className="w-full h-full object-cover"
                      />
                    )
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      {mediaFile.file.type.startsWith("video/") ? (
                        <Video className="w-8 h-8 text-muted-foreground" />
                      ) : (
                        <ImageIcon className="w-8 h-8 text-muted-foreground" />
                      )}
                    </div>
                  )}

                  {/* Status Overlay */}
                  {mediaFile.status === "uploading" && (
                    <div className="absolute inset-0 bg-black/50 flex flex-col items-center justify-center">
                      <Loader2 className="w-6 h-6 text-white animate-spin" />
                      <Progress
                        value={mediaFile.progress}
                        className="w-2/3 mt-2 h-1"
                      />
                    </div>
                  )}

                  {mediaFile.status === "success" && (
                    <div className="absolute bottom-2 right-2">
                      <CheckCircle className="w-5 h-5 text-green-500" />
                    </div>
                  )}

                  {mediaFile.status === "error" && (
                    <div className="absolute inset-0 bg-red-500/20 flex items-center justify-center">
                      <div className="text-center p-2">
                        <AlertCircle className="w-6 h-6 text-red-500 mx-auto" />
                        <p className="text-xs text-red-500 mt-1">
                          {mediaFile.error}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Remove Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(mediaFile.id);
                  }}
                  className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="w-4 h-4" />
                </button>

                {/* File Type Badge */}
                <div className="absolute bottom-2 left-2">
                  <span className="text-xs px-1.5 py-0.5 rounded bg-black/50 text-white">
                    {mediaFile.file.type.startsWith("video/") ? "Video" : "Image"}
                  </span>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Summary */}
      {files.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {successfulUploads.length} sur {files.length} fichier{files.length !== 1 ? "s" : ""} uploade{successfulUploads.length !== 1 ? "s" : ""}
          </span>
          {isUploading && (
            <span className="flex items-center gap-1">
              <Loader2 className="w-3 h-3 animate-spin" />
              Upload en cours...
            </span>
          )}
        </div>
      )}
    </div>
  );
}
