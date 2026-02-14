'use client';

import { useState, useRef } from 'react';
import { Upload, Camera, X, Image as ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PhotoUploaderProps {
  onUpload: (file: File) => void;
  maxSizeMB?: number;
  className?: string;
}

export function PhotoUploader({
  onUpload,
  maxSizeMB = 10,
  className,
}: PhotoUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setError(null);

    if (!file.type.startsWith('image/')) {
      setError('Le fichier doit être une image (JPG, PNG, WebP...)');
      return;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSizeMB) {
      setError(
        `Le fichier est trop gros. Maximum ${maxSizeMB}Mo, votre fichier fait ${sizeMB.toFixed(1)}Mo`
      );
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    onUpload(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files?.[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const clearPreview = () => {
    setPreview(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  if (preview) {
    return (
      <div className={cn('relative', className)}>
        <img
          src={preview}
          alt="Aperçu"
          className="w-full h-64 object-cover rounded-xl"
        />
        <button
          onClick={clearPreview}
          className="absolute top-2 right-2 p-2 bg-black/50 hover:bg-black/70 rounded-full text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all',
          dragActive
            ? 'border-purple-500 bg-purple-50'
            : 'border-gray-300 hover:border-purple-400 hover:bg-gray-50'
        )}
      >
        <ImageIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-lg font-medium text-gray-900 mb-2">
          Glissez votre photo ici
        </p>
        <p className="text-sm text-gray-600 mb-4">
          ou cliquez pour choisir un fichier
        </p>
        <p className="text-xs text-gray-500">
          JPG, PNG, WebP &bull; Maximum {maxSizeMB}Mo
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <button
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
          className="flex items-center justify-center gap-2 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors min-h-[44px]"
        >
          <Upload className="w-5 h-5" />
          <span>Choisir fichier</span>
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            cameraInputRef.current?.click();
          }}
          className="flex items-center justify-center gap-2 px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors min-h-[44px]"
        >
          <Camera className="w-5 h-5" />
          <span>Prendre photo</span>
        </button>
      </div>

      {error && (
        <div className="flex items-start gap-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-3">
          <span>{error}</span>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="hidden"
      />
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}
