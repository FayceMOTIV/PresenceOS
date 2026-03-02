// PresenceOS Mobile — Firebase Storage Media Service
// Upload images with progress tracking + get download URLs

import { ref, uploadBytesResumable, getDownloadURL } from "firebase/storage";
import { storage } from "@/lib/firebase";

export interface UploadResult {
  downloadUrl: string;
  storagePath: string;
}

/**
 * Upload an image to Firebase Storage with optional progress callback.
 * Returns the download URL and storage path.
 */
export async function uploadImage(
  bizId: string,
  uri: string,
  filename: string,
  onProgress?: (progress: number) => void
): Promise<UploadResult> {
  // Fetch the file as a blob (works with Hermes / React Native)
  const response = await fetch(uri);
  const blob = await response.blob();

  const storagePath = `media/${bizId}/${Date.now()}_${filename}`;
  const storageRef = ref(storage, storagePath);

  return new Promise<UploadResult>((resolve, reject) => {
    const task = uploadBytesResumable(storageRef, blob);

    task.on(
      "state_changed",
      (snapshot) => {
        if (onProgress) {
          const progress = snapshot.bytesTransferred / snapshot.totalBytes;
          onProgress(progress);
        }
      },
      (error) => reject(error),
      async () => {
        const downloadUrl = await getDownloadURL(task.snapshot.ref);
        resolve({ downloadUrl, storagePath });
      }
    );
  });
}
