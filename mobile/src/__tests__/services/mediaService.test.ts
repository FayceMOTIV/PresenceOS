/**
 * Tests du mediaService
 */

import { uploadImage } from "@/services/mediaService";

const mockUploadBytesResumable = jest.fn();
const mockGetDownloadURL = jest.fn();
const mockRef = jest.fn();

jest.mock("firebase/storage", () => ({
  ref: (...args: any[]) => mockRef(...args),
  uploadBytesResumable: (...args: any[]) => mockUploadBytesResumable(...args),
  getDownloadURL: (...args: any[]) => mockGetDownloadURL(...args),
}));

jest.mock("@/lib/firebase", () => ({
  storage: { type: "mock-storage" },
}));

// Mock global fetch for blob creation
const mockBlob = { type: "image/jpeg" } as any;
global.fetch = jest.fn().mockResolvedValue({ blob: () => Promise.resolve(mockBlob) }) as any;

beforeEach(() => {
  jest.clearAllMocks();
  mockRef.mockReturnValue("mock-storage-ref");
});

describe("uploadImage", () => {
  test("upload réussit et retourne URL + path", async () => {
    const taskSnapshot = { ref: "mock-ref" };
    let stateChangedCallback: any;
    let errorCallback: any;
    let completeCallback: any;

    mockUploadBytesResumable.mockReturnValue({
      on: (event: string, onState: any, onError: any, onComplete: any) => {
        stateChangedCallback = onState;
        errorCallback = onError;
        completeCallback = onComplete;
      },
      snapshot: taskSnapshot,
    });

    mockGetDownloadURL.mockResolvedValue("https://storage.example.com/image.jpg");

    const promise = uploadImage("biz-1", "file://photo.jpg", "photo.jpg");

    // Flush microtasks from await fetch() + await blob()
    await new Promise((r) => setTimeout(r, 0));

    // Simulate progress
    stateChangedCallback({ bytesTransferred: 50, totalBytes: 100 });
    // Simulate completion
    await completeCallback();

    const result = await promise;
    expect(result.downloadUrl).toBe("https://storage.example.com/image.jpg");
    expect(result.storagePath).toContain("media/biz-1/");
    expect(result.storagePath).toContain("photo.jpg");
  });

  test("appelle onProgress callback", async () => {
    let stateChangedCallback: any;
    let completeCallback: any;

    mockUploadBytesResumable.mockReturnValue({
      on: (event: string, onState: any, onError: any, onComplete: any) => {
        stateChangedCallback = onState;
        completeCallback = onComplete;
      },
      snapshot: { ref: "mock-ref" },
    });

    mockGetDownloadURL.mockResolvedValue("https://storage.example.com/image.jpg");

    const onProgress = jest.fn();
    const promise = uploadImage("biz-1", "file://photo.jpg", "photo.jpg", onProgress);

    // Flush microtasks from await fetch() + await blob()
    await new Promise((r) => setTimeout(r, 0));

    stateChangedCallback({ bytesTransferred: 75, totalBytes: 100 });
    expect(onProgress).toHaveBeenCalledWith(0.75);

    await completeCallback();
    await promise;
  });

  test("reject en cas d'erreur d'upload", async () => {
    let errorCallback: any;

    mockUploadBytesResumable.mockReturnValue({
      on: (event: string, onState: any, onError: any, onComplete: any) => {
        errorCallback = onError;
      },
      snapshot: { ref: "mock-ref" },
    });

    const promise = uploadImage("biz-1", "file://photo.jpg", "photo.jpg");

    // Flush microtasks from await fetch() + await blob()
    await new Promise((r) => setTimeout(r, 0));

    errorCallback(new Error("Upload failed"));

    await expect(promise).rejects.toThrow("Upload failed");
  });
});
