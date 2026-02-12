"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Loader2, ArrowLeft, CheckCircle, Mail } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "@/hooks/use-toast";

export default function ForgotPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [email, setEmail] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      toast({
        title: "Email requis",
        description: "Veuillez entrer votre adresse email",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);

    try {
      await api.post("/auth/forgot-password", { email });
      setIsSubmitted(true);
    } catch (error: any) {
      // Still show success to prevent email enumeration
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
        <Card className="w-full max-w-md glass-card">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <CardTitle className="text-2xl">Email envoye!</CardTitle>
            <CardDescription className="text-base">
              Si un compte existe avec l&apos;adresse <strong>{email}</strong>,
              vous recevrez un lien pour reinitialiser votre mot de passe.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-muted/50 rounded-lg p-4 text-sm text-muted-foreground">
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium text-foreground mb-1">
                    Verifiez votre boite mail
                  </p>
                  <p>
                    Le lien de reinitialisation expire dans 1 heure.
                    Pensez a verifier vos spams.
                  </p>
                </div>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setIsSubmitted(false);
                  setEmail("");
                }}
              >
                Renvoyer un email
              </Button>
              <Link href="/auth/login">
                <Button variant="ghost" className="w-full">
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Retour a la connexion
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted p-4">
      <Card className="w-full max-w-md glass-card">
        <CardHeader className="text-center">
          <Link href="/" className="inline-flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
          </Link>
          <CardTitle className="text-2xl">Mot de passe oublie?</CardTitle>
          <CardDescription>
            Entrez votre email pour recevoir un lien de reinitialisation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="vous@exemple.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
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
                  Envoi en cours...
                </>
              ) : (
                "Envoyer le lien"
              )}
            </Button>
          </form>
          <div className="mt-6 text-center">
            <Link
              href="/auth/login"
              className="text-sm text-muted-foreground hover:text-primary inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-4 h-4" />
              Retour a la connexion
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
