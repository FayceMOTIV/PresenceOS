"""
PresenceOS — Firebase Firestore Service (Sprint 4)

Thin wrapper around firebase_admin.firestore for DNA storage.
Gracefully degrades when Firebase is not configured.
"""

import logging
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class FirestoreService:
    """Firestore document operations for Business DNA and other collections."""

    def __init__(self) -> None:
        self._db = None

    def _get_db(self):
        """Lazy init — returns Firestore client or None if not configured."""
        if self._db is None:
            settings = get_settings()
            if not settings.firebase_project_id:
                logger.debug("Firestore: Firebase not configured, skipping")
                return None
            try:
                from firebase_admin import firestore
                self._db = firestore.client()
            except Exception as exc:
                logger.warning("Firestore client init failed: %s", exc)
                return None
        return self._db

    async def get_document(
        self, collection: str, doc_id: str
    ) -> dict[str, Any] | None:
        """Get a single document by path."""
        db = self._get_db()
        if db is None:
            return None
        try:
            doc_ref = db.collection(collection).document(doc_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as exc:
            logger.warning("Firestore get failed: %s/%s — %s", collection, doc_id, exc)
            return None

    async def set_document(
        self,
        collection: str,
        doc_id: str,
        data: dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """Set (upsert) a document."""
        db = self._get_db()
        if db is None:
            return False
        try:
            doc_ref = db.collection(collection).document(doc_id)
            doc_ref.set(data, merge=merge)
            return True
        except Exception as exc:
            logger.warning("Firestore set failed: %s/%s — %s", collection, doc_id, exc)
            return False

    async def get_subcollection_doc(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        sub_doc_id: str,
    ) -> dict[str, Any] | None:
        """Get a document from a subcollection."""
        db = self._get_db()
        if db is None:
            return None
        try:
            doc_ref = (
                db.collection(collection)
                .document(doc_id)
                .collection(subcollection)
                .document(sub_doc_id)
            )
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as exc:
            logger.warning(
                "Firestore subcollection get failed: %s/%s/%s/%s — %s",
                collection, doc_id, subcollection, sub_doc_id, exc,
            )
            return None

    async def set_subcollection_doc(
        self,
        collection: str,
        doc_id: str,
        subcollection: str,
        sub_doc_id: str,
        data: dict[str, Any],
        merge: bool = True,
    ) -> bool:
        """Set a document in a subcollection."""
        db = self._get_db()
        if db is None:
            return False
        try:
            doc_ref = (
                db.collection(collection)
                .document(doc_id)
                .collection(subcollection)
                .document(sub_doc_id)
            )
            doc_ref.set(data, merge=merge)
            return True
        except Exception as exc:
            logger.warning(
                "Firestore subcollection set failed: %s/%s/%s/%s — %s",
                collection, doc_id, subcollection, sub_doc_id, exc,
            )
            return False
