"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Save, Loader2, Eye, EyeOff, User as UserIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "@/hooks/use-toast";
import { usersApi } from "@/lib/api";
import { User } from "@/types";

interface AccountTabProps {
  user: User | null;
  onUserUpdated?: (user: User) => void;
}

export function AccountTab({ user, onUserUpdated }: AccountTabProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingPassword, setIsSavingPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || "",
    avatar_url: user?.avatar_url || "",
  });
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || "",
        avatar_url: user.avatar_url || "",
      });
    }
  }, [user]);

  const handleSaveProfile = async () => {
    if (!formData.full_name.trim()) {
      toast({
        title: "Erreur",
        description: "Le nom est requis",
        variant: "destructive"
      });
      return;
    }
    setIsSaving(true);
    try {
      const res = await usersApi.updateMe({
        full_name: formData.full_name.trim(),
        avatar_url: formData.avatar_url.trim() || undefined,
      });
      toast({ title: "Profil mis a jour" });
      onUserUpdated?.(res.data);
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de mettre a jour le profil",
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    const errors: Record<string, string> = {};
    if (!passwordData.current_password) errors.current_password = "Requis";
    if (passwordData.new_password.length < 8) errors.new_password = "Minimum 8 caracteres";
    if (passwordData.new_password !== passwordData.confirm_password) {
      errors.confirm_password = "Les mots de passe ne correspondent pas";
    }
    setPasswordErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setIsSavingPassword(true);
    try {
      await usersApi.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      toast({ title: "Mot de passe modifie" });
      setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
      setPasswordErrors({});
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Mot de passe actuel incorrect",
        variant: "destructive"
      });
    } finally {
      setIsSavingPassword(false);
    }
  };

  if (!user) return null;

  return (
    <div className="space-y-6">
      {/* Profile Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserIcon className="w-5 h-5" />
              Informations du profil
            </CardTitle>
            <CardDescription>
              Gerez vos informations personnelles
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Nom complet</Label>
              <Input
                id="fullName"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="Votre nom complet"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={user.email}
                disabled
                className="bg-muted"
              />
              <p className="text-xs text-muted-foreground">
                L&apos;email ne peut pas etre modifie
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="avatarUrl">URL de l&apos;avatar (optionnel)</Label>
              <Input
                id="avatarUrl"
                type="url"
                value={formData.avatar_url}
                onChange={(e) => setFormData({ ...formData, avatar_url: e.target.value })}
                placeholder="https://example.com/avatar.jpg"
              />
            </div>

            {formData.avatar_url && (
              <div className="space-y-2">
                <Label>Apercu de l&apos;avatar</Label>
                <div className="flex items-center gap-4">
                  <img
                    src={formData.avatar_url}
                    alt={formData.full_name}
                    className="w-16 h-16 rounded-full object-cover border-2"
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                  <span className="text-sm text-muted-foreground">
                    {formData.full_name}
                  </span>
                </div>
              </div>
            )}

            <Separator />

            <div className="flex items-center gap-2">
              <Badge variant={user.is_verified ? "default" : "secondary"}>
                {user.is_verified ? "Verifie" : "Non verifie"}
              </Badge>
              <Badge variant={user.is_active ? "default" : "destructive"}>
                {user.is_active ? "Actif" : "Inactif"}
              </Badge>
              {user.oauth_provider && (
                <Badge variant="outline">
                  OAuth: {user.oauth_provider}
                </Badge>
              )}
            </div>

            <Separator />

            <div className="flex justify-end">
              <Button
                onClick={handleSaveProfile}
                disabled={isSaving}
                className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Enregistrement...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Enregistrer le profil
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Password Card */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Changer le mot de passe</CardTitle>
            <CardDescription>
              Modifiez votre mot de passe de connexion
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="currentPassword">Mot de passe actuel</Label>
              <div className="relative">
                <Input
                  id="currentPassword"
                  type={showCurrentPassword ? "text" : "password"}
                  value={passwordData.current_password}
                  onChange={(e) => {
                    setPasswordData({ ...passwordData, current_password: e.target.value });
                    setPasswordErrors({ ...passwordErrors, current_password: "" });
                  }}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showCurrentPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {passwordErrors.current_password && (
                <p className="text-xs text-red-500">{passwordErrors.current_password}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPassword">Nouveau mot de passe</Label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? "text" : "password"}
                  value={passwordData.new_password}
                  onChange={(e) => {
                    setPasswordData({ ...passwordData, new_password: e.target.value });
                    setPasswordErrors({ ...passwordErrors, new_password: "" });
                  }}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showNewPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Minimum 8 caracteres
              </p>
              {passwordErrors.new_password && (
                <p className="text-xs text-red-500">{passwordErrors.new_password}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirmer le mot de passe</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  value={passwordData.confirm_password}
                  onChange={(e) => {
                    setPasswordData({ ...passwordData, confirm_password: e.target.value });
                    setPasswordErrors({ ...passwordErrors, confirm_password: "" });
                  }}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {passwordErrors.confirm_password && (
                <p className="text-xs text-red-500">{passwordErrors.confirm_password}</p>
              )}
            </div>

            <Separator />

            <div className="flex justify-end">
              <Button
                onClick={handleChangePassword}
                disabled={isSavingPassword}
                className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
              >
                {isSavingPassword ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Modification...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Modifier le mot de passe
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
