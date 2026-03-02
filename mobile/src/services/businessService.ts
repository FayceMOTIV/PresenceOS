// PresenceOS Mobile — Firestore Business Service
// CRUD + real-time subscription for businesses (replaces API-based brand fetching)

import {
  collection,
  query,
  where,
  getDocs,
  onSnapshot,
  doc,
  setDoc,
  updateDoc,
  Unsubscribe,
} from "firebase/firestore";
import { db } from "@/lib/firebase";

export interface FirestoreBusiness {
  id: string;
  name: string;
  slug: string;
  businessType: string;
  description?: string;
  logoUrl?: string;
  ownerId: string;
  memberIds: string[];
  isActive: boolean;
  createdAt?: string;
}

const BUSINESSES_COLLECTION = "businesses";

/**
 * Get all businesses where the user is a member.
 */
export async function getMyBusinesses(
  uid: string
): Promise<FirestoreBusiness[]> {
  const q = query(
    collection(db, BUSINESSES_COLLECTION),
    where("memberIds", "array-contains", uid)
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map((d) => ({
    id: d.id,
    ...(d.data() as Omit<FirestoreBusiness, "id">),
  }));
}

/**
 * Real-time subscription to user's businesses.
 * Returns an unsubscribe function.
 */
export function subscribeToMyBusinesses(
  uid: string,
  callback: (businesses: FirestoreBusiness[]) => void
): Unsubscribe {
  const q = query(
    collection(db, BUSINESSES_COLLECTION),
    where("memberIds", "array-contains", uid)
  );
  return onSnapshot(q, (snapshot) => {
    const businesses = snapshot.docs.map((d) => ({
      id: d.id,
      ...(d.data() as Omit<FirestoreBusiness, "id">),
    }));
    callback(businesses);
  });
}

/**
 * Create a new business document.
 * Uses the provided id (matching PostgreSQL brands.id UUID).
 */
export async function createBusiness(
  data: FirestoreBusiness
): Promise<void> {
  const ref = doc(db, BUSINESSES_COLLECTION, data.id);
  await setDoc(ref, {
    name: data.name,
    slug: data.slug,
    businessType: data.businessType,
    description: data.description ?? null,
    logoUrl: data.logoUrl ?? null,
    ownerId: data.ownerId,
    memberIds: data.memberIds,
    isActive: data.isActive,
    createdAt: new Date().toISOString(),
  });
}

/**
 * Update an existing business document (partial update).
 */
export async function updateBusiness(
  bizId: string,
  data: Partial<Omit<FirestoreBusiness, "id">>
): Promise<void> {
  const ref = doc(db, BUSINESSES_COLLECTION, bizId);
  await updateDoc(ref, data);
}
