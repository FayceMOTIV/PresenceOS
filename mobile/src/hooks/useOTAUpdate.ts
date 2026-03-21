/**
 * Hook OTA Update — vérifie et applique les mises à jour automatiquement.
 * L'app vérifie à chaque lancement si une MAJ est disponible.
 * Si oui → télécharge en background → applique au prochain lancement.
 *
 * Pour forcer une MAJ immédiate (urgence) : reloadAsync()
 */
import { useEffect } from "react";
import * as Updates from "expo-updates";

export function useOTAUpdate() {
  useEffect(() => {
    checkForUpdate();
  }, []);

  async function checkForUpdate() {
    if (__DEV__) return;

    try {
      const update = await Updates.checkForUpdateAsync();

      if (update.isAvailable) {
        console.log("[OTA] Mise à jour disponible, téléchargement...");
        await Updates.fetchUpdateAsync();
        console.log("[OTA] Téléchargée. Sera appliquée au prochain lancement.");
      }
    } catch (e) {
      // Silencieux en prod — ne jamais crasher à cause d'une MAJ
      console.log("[OTA] Vérification impossible (mode offline ?)");
    }
  }
}
