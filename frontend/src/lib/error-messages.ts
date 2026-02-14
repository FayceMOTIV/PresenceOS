/**
 * Messages d'erreur, succès et chargement en français simple.
 * Aucun jargon technique — compréhensible par tout le monde.
 */

export function getSimpleErrorMessage(error: unknown): string {
  const msg =
    (error as any)?.response?.data?.detail ||
    (error as any)?.message ||
    String(error);

  if (/fetch|network|ERR_/i.test(msg)) {
    return "Impossible de se connecter à Internet. Vérifiez votre connexion et réessayez.";
  }
  if (/401|unauthorized/i.test(msg)) {
    return "Vous êtes resté trop longtemps inactif. Veuillez vous reconnecter.";
  }
  if (/403|forbidden/i.test(msg)) {
    return "Vous n'avez pas le droit de faire cette action. Contactez un administrateur de votre espace.";
  }
  if (/password|mot de passe/i.test(msg)) {
    return "Mot de passe incorrect. Réessayez ou cliquez sur « Mot de passe oublié ».";
  }
  if (/500|server|internal/i.test(msg)) {
    return "Un problème technique est survenu. Réessayez dans quelques instants.";
  }
  if (/file|upload|taille/i.test(msg)) {
    return "Le fichier est trop gros ou dans un format non reconnu. Essayez avec une photo plus petite.";
  }
  if (/rate|limit|too many/i.test(msg)) {
    return "Vous allez trop vite ! Attendez quelques secondes avant de réessayer.";
  }
  if (/required|invalid|validation/i.test(msg)) {
    return "Certaines informations sont manquantes ou incorrectes. Vérifiez le formulaire.";
  }
  if (/already exists|duplicate|déjà/i.test(msg)) {
    return "Cet élément existe déjà. Essayez avec un autre nom.";
  }

  return "Quelque chose n'a pas fonctionné. Réessayez dans quelques secondes.";
}

export function getSuccessMessage(action: string): string {
  const messages: Record<string, string> = {
    post_created: "Votre post est créé !",
    post_published: "Votre post est publié !",
    post_scheduled: "Votre post sera publié automatiquement.",
    post_deleted: "Post supprimé.",
    post_duplicated: "Post dupliqué avec succès.",
    idea_generated: "Nouvelles idées prêtes !",
    idea_approved: "Idée approuvée !",
    idea_rejected: "Idée rejetée.",
    brand_created: "Votre marque est créée !",
    analysis_complete: "Votre Instagram a été analysé.",
    connection_success: "Instagram est maintenant connecté à votre compte.",
    password_changed: "Mot de passe modifié avec succès.",
    profile_updated: "Profil mis à jour.",
    workspace_created: "Nouvel espace créé !",
    member_invited: "Invitation envoyée !",
  };

  return messages[action] || "Action réussie !";
}

export function getLoadingMessage(action: string): string {
  const messages: Record<string, string> = {
    generating_caption: "Je crée vos textes... (quelques secondes)",
    generating_ideas: "Je cherche des idées... (quelques secondes)",
    analyzing_brand: "J'analyse votre Instagram... (30 secondes environ)",
    uploading_photo: "J'envoie votre photo...",
    publishing: "Je publie votre post...",
    scheduling: "Je programme votre post...",
    connecting: "Je me connecte à Instagram...",
    loading: "Chargement...",
    saving: "Enregistrement...",
  };

  return messages[action] || "Chargement...";
}
