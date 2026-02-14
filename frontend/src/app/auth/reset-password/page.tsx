"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Loader2, ArrowLeft, CheckCircle, AlertCircle, Eye, EyeOff } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!token) {
      toast({
        title: "Lien invalide",
        description: "Le lien de réinitialisation est invalide ou a expiré",
        variant: "destructive",
      });
    }
  }, [token]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (password.length < 8) {
      newErrors.password = "Le mot de passe doit contenir au moins 8 caractères";
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Les mots de passe ne correspondent pas";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;
    if (!token) return;

    setIsLoading(true);

    try {
      await api.post("/auth/reset-password", {
        token,
        new_password: password,
      });
      setIsSuccess(true);
    } catch (error: any) {
      const message = error.response?.data?.detail || "Une erreur est survenue";
      toast({
        title: "Erreur",
        description: message,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-mesh-gradient-strong p-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-fuchsia-200/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        <Card className="w-full max-w-md shadow-2xl shadow-purple-500/[0.07] border-gray-200/60 backdrop-blur-sm relative z-10">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
            <CardTitle className="text-2xl">Lien invalide</CardTitle>
            <CardDescription>
              Le lien de réinitialisation est invalide ou a expiré.
              Veuillez demander un nouveau lien.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-2">
              <Link href="/auth/forgot-password">
                <Button className="w-full" variant="gradient">
                  Demander un nouveau lien
                </Button>
              </Link>
              <Link href="/auth/login">
                <Button variant="ghost" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Retour à la connexion
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (isSuccess) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-mesh-gradient-strong p-4 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-violet-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-fuchsia-200/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />
        <Card className="w-full max-w-md shadow-2xl shadow-purple-500/[0.07] border-gray-200/60 backdrop-blur-sm relative z-10">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <CardTitle className="text-2xl">Mot de passe modifié!</CardTitle>
            <CardDescription>
              Votre mot de passe a été changé avec succès.
              Vous pouvez maintenant vous connecter.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/auth/login">
              <Button className="w-full" variant="gradient">
                Se connecter
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-50 via-white to-fuchsia-50 p-4">
      <Card className="w-full max-w-md shadow-xl shadow-purple-500/5 border-gray-200/80">
        <CardHeader className="text-center">
          <Link href="/" className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-14 h-14 rounded-2xl gradient-bg shadow-glow-md flex items-center justify-center">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
          </Link>
          <CardTitle className="text-2xl">Nouveau mot de passe</CardTitle>
          <CardDescription>
            Choisissez un nouveau mot de passe sécurisé
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Nouveau mot de passe
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={errors.password ? "border-destructive pr-10" : "pr-10"}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Minimum 8 caractères
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="text-sm font-medium">
                Confirmer le mot de passe
              </label>
              <Input
                id="confirmPassword"
                type={showPassword ? "text" : "password"}
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={errors.confirmPassword ? "border-destructive" : ""}
                required
              />
              {errors.confirmPassword && (
                <p className="text-sm text-destructive">{errors.confirmPassword}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              variant="gradient"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Modification...
                </>
              ) : (
                "Modifier le mot de passe"
              )}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <Link
              href="/auth/login"
              className="text-sm text-muted-foreground hover:text-primary inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-50 via-white to-fuchsia-50">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  );
}
