// Email validation
export function validateEmail(email: string): string | null {
  if (!email) return "L'email est obligatoire";
  if (email.length < 3) return "L'email est trop court";
  if (!email.includes('@')) return "L'email doit contenir @";
  if (!email.includes('.')) return "L'email doit contenir un point";
  return null;
}

// Password validation
export function validatePassword(password: string): string | null {
  if (!password) return 'Le mot de passe est obligatoire';
  if (password.length < 8) return 'Le mot de passe doit faire au moins 8 caractères';
  if (!/[A-Z]/.test(password)) return 'Le mot de passe doit contenir une majuscule';
  if (!/[0-9]/.test(password)) return 'Le mot de passe doit contenir un chiffre';
  return null;
}

// Name validation
export function validateName(name: string): string | null {
  if (!name) return 'Le nom est obligatoire';
  if (name.length < 2) return 'Le nom est trop court';
  if (name.length > 50) return 'Le nom est trop long';
  return null;
}

// Workspace name validation
export function validateWorkspaceName(name: string): string | null {
  if (!name) return 'Le nom du restaurant est obligatoire';
  if (name.length < 2) return 'Le nom doit faire au moins 2 caractères';
  if (name.length > 50) return 'Le nom ne peut pas dépasser 50 caractères';
  return null;
}

// Brand name validation
export function validateBrandName(name: string): string | null {
  if (!name) return 'Le nom de la marque est obligatoire';
  if (name.length < 2) return 'Le nom doit faire au moins 2 caractères';
  return null;
}
