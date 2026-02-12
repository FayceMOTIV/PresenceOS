"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Loader2 } from "lucide-react";
import { authApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    full_name: "",
    workspace_name: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authApi.register(formData);
      const { token, workspaces } = response.data;

      localStorage.setItem("token", token.access_token);

      if (workspaces.length > 0) {
        localStorage.setItem("workspace_id", workspaces[0].id);
      }

      toast({
        title: "Compte créé!",
        description: "Bienvenue sur PresenceOS",
      });

      router.push("/onboarding");
    } catch (error: any) {
      toast({
        title: "Erreur d'inscription",
        description: error.response?.data?.detail || "Une erreur est survenue",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md glass-card">
        <CardHeader className="text-center">
          <Link href="/" className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
          </Link>
          <CardTitle className="text-2xl">Créer un compte</CardTitle>
          <CardDescription>
            Commencez à automatiser votre marketing en quelques minutes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="full_name" className="text-sm font-medium">
                Nom complet
              </label>
              <Input
                id="full_name"
                name="full_name"
                type="text"
                placeholder="John Doe"
                value={formData.full_name}
                onChange={handleChange}
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                name="email"
                type="email"
                placeholder="vous@exemple.com"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Mot de passe
              </label>
              <Input
                id="password"
                name="password"
                type="password"
                placeholder="Min. 8 caractères"
                value={formData.password}
                onChange={handleChange}
                minLength={8}
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="workspace_name" className="text-sm font-medium">
                Nom de votre entreprise
              </label>
              <Input
                id="workspace_name"
                name="workspace_name"
                type="text"
                placeholder="Ma Super Entreprise"
                value={formData.workspace_name}
                onChange={handleChange}
              />
            </div>
            <Button
              type="submit"
              className="w-full"
              variant="gradient"
              disabled={isLoading}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                "Créer mon compte"
              )}
            </Button>
          </form>
          <div className="mt-6 text-center text-sm">
            <span className="text-muted-foreground">Déjà un compte?</span>{" "}
            <Link href="/auth/login" className="text-primary hover:underline">
              Se connecter
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
