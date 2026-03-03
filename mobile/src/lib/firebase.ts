// PresenceOS Mobile — Firebase SDK Setup
// Uses EXPO_PUBLIC_FIREBASE_* env vars.
// Gracefully handles missing config (app works without Firebase in dev).

import { initializeApp, getApps, getApp, FirebaseApp } from "firebase/app";
import { initializeAuth, getAuth, Auth } from "firebase/auth";
// @ts-expect-error — getReactNativePersistence is exported from the RN entrypoint (index.rn.d.ts)
import { getReactNativePersistence } from "firebase/auth";
import { getFirestore, Firestore } from "firebase/firestore";
import { getStorage, FirebaseStorage } from "firebase/storage";
import AsyncStorage from "@react-native-async-storage/async-storage";

const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY ?? "",
  authDomain: process.env.EXPO_PUBLIC_FIREBASE_AUTH_DOMAIN ?? "",
  projectId: process.env.EXPO_PUBLIC_FIREBASE_PROJECT_ID ?? "",
  storageBucket: process.env.EXPO_PUBLIC_FIREBASE_STORAGE_BUCKET ?? "",
  messagingSenderId: process.env.EXPO_PUBLIC_FIREBASE_MESSAGING_SENDER_ID ?? "",
  appId: process.env.EXPO_PUBLIC_FIREBASE_APP_ID ?? "",
};

let app: FirebaseApp;
let auth: Auth;
let db: Firestore;
let storage: FirebaseStorage;

try {
  // Guard against double initialization (Fast Refresh / HMR)
  app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

  // Auth with AsyncStorage persistence (required for Hermes / React Native)
  try {
    auth = initializeAuth(app, {
      persistence: getReactNativePersistence(AsyncStorage),
    });
  } catch (e: any) {
    // If auth was already initialized (HMR), get existing instance
    if (e.code === "auth/already-initialized") {
      auth = getAuth(app);
    } else {
      throw e;
    }
  }

  db = getFirestore(app);
  storage = getStorage(app);
} catch (e) {
  console.error("[Firebase] Init failed:", e);
  // Re-throw so the app doesn't silently fail
  throw e;
}

export { app, auth, db, storage };
