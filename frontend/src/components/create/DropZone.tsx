"use client";

import { useCallback, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Camera, Plus, X, Upload } from "lucide-react";

interface DropZoneProps {
  photoUrls: string[];
  onFileDrop: (file: File) => void;
  disabled?: boolean;
}

export function DropZone({ photoUrls, onFileDrop, disabled }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (disabled) return;
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        for (let i = 0; i < files.length; i++) {
          if (files[i].type.startsWith("image/") || files[i].type.startsWith("video/")) {
            onFileDrop(files[i]);
          }
        }
      }
    },
    [onFileDrop, disabled]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || disabled) return;
      for (let i = 0; i < files.length; i++) {
        onFileDrop(files[i]);
      }
      e.target.value = "";
    },
    [onFileDrop, disabled]
  );

  const hasPhotos = photoUrls.length > 0;

  return (
    <div className="space-y-3">
      <AnimatePresence mode="wait">
        {!hasPhotos ? (
          <motion.div
            key="empty"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            onDragEnter={handleDragIn}
            onDragLeave={handleDragOut}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`
              relative cursor-pointer rounded-2xl border-2 border-dashed
              transition-all duration-300 overflow-hidden
              ${
                isDragging
                  ? "border-primary bg-primary/5 shadow-[0_0_40px_rgba(245,158,11,0.15)]"
                  : "border-border/50 hover:border-primary/50 hover:bg-secondary/30"
              }
              ${disabled ? "opacity-50 pointer-events-none" : ""}
            `}
          >
            <div className="flex flex-col items-center justify-center py-16 px-6">
              <motion.div
                animate={isDragging ? { scale: 1.1 } : { scale: [1, 1.05, 1] }}
                transition={isDragging ? { duration: 0.2 } : { repeat: Infinity, duration: 3 }}
                className={`
                  w-16 h-16 rounded-2xl flex items-center justify-center mb-4
                  ${isDragging ? "bg-primary/20" : "bg-secondary"}
                `}
              >
                {isDragging ? (
                  <Upload className="w-8 h-8 text-primary" />
                ) : (
                  <Camera className="w-8 h-8 text-muted-foreground" />
                )}
              </motion.div>
              <p className="text-base font-medium text-foreground mb-1">
                {isDragging ? "Depose ici !" : "Depose ta photo ici"}
              </p>
              <p className="text-sm text-muted-foreground">
                ou clique pour parcourir
              </p>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="photos"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-3"
          >
            <div className="grid grid-cols-2 gap-2">
              {photoUrls.map((url, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: i * 0.1, type: "spring", stiffness: 200 }}
                  className="relative aspect-square rounded-xl overflow-hidden group"
                >
                  <img
                    src={url}
                    alt={`Photo ${i + 1}`}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
                </motion.div>
              ))}
              {/* Add more button */}
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                onClick={() => inputRef.current?.click()}
                className={`
                  aspect-square rounded-xl border-2 border-dashed border-border/50
                  flex items-center justify-center cursor-pointer
                  hover:border-primary/50 hover:bg-primary/5 transition-all
                  ${disabled ? "opacity-50 pointer-events-none" : ""}
                `}
                onDragEnter={handleDragIn}
                onDragLeave={handleDragOut}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Plus className="w-8 h-8 text-muted-foreground" />
              </motion.div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <input
        ref={inputRef}
        type="file"
        accept="image/*,video/*"
        multiple
        onChange={handleFileSelect}
        className="hidden"
      />
    </div>
  );
}
