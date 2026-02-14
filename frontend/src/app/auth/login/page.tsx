"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Sparkles, Loader2, ArrowRight, Eye, EyeOff } from "lucide-react";
import { authApi } from "@/lib/api";
import { toast } from "@/hooks/use-toast";
import { FormField } from '@/components/ui/form-field';

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authApi.login(email, password);
      const { token, workspaces } = response.data;

      localStorage.setItem("token", token.access_token);

      if (workspaces.length > 0) {
        localStorage.setItem("workspace_id", workspaces[0].id);
        router.push("/dashboard");
      } else {
        router.push("/onboarding");
      }
    } catch (error: any) {
      toast({
        title: "Erreur de connexion",
        description: error.response?.data?.detail || "Email ou mot de passe incorrect",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-mesh-gradient-strong p-4 relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-violet-200/30 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-fuchsia-200/20 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="w-full max-w-md relative z-10"
      >
        <Card className="shadow-2xl shadow-purple-500/[0.07] border-gray-200/60 backdrop-blur-sm">
          <CardHeader className="text-center pb-2">
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="mx-auto mb-4"
            >
              <Link href="/" className="inline-block">
                <div className="w-14 h-14 rounded-2xl gradient-bg flex items-center justify-center shadow-glow-md">
                  <Sparkles className="w-7 h-7 text-white" />
                </div>
              </Link>
            </motion.div>
            <CardTitle className="text-2xl font-bold">Bon retour!</CardTitle>
            <CardDescription className="text-base">
              Connectez-vous à votre compte PresenceOS
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="space-y-2"
              >
                <label htmlFor="email" className="text-sm font-medium text-gray-700">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="vous@exemple.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
                {email && email.length > 0 && !email.includes('@') && (
                  <p className="text-xs text-amber-600 mt-1">L&apos;email doit contenir @</p>
                )}
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="text-sm font-medium text-gray-700">
                    Mot de passe
                  </label>
                  <Link
                    href="/auth/forgot-password"
                    className="text-xs text-violet-600 hover:text-violet-700 transition-colors"
                  >
                    Mot de passe oublié?
                  </Link>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {password && password.length > 0 && password.length < 8 && (
                  <p className="text-xs text-amber-600 mt-1">Le mot de passe doit faire au moins 8 caractères</p>
                )}
              </motion.div>
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
              >
                <Button
                  type="submit"
                  className="w-full group"
                  variant="gradient"
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Se connecter
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </Button>
              </motion.div>
            </form>
            <div className="mt-8 text-center text-sm">
              <span className="text-muted-foreground">Pas encore de compte?</span>{" "}
              <Link href="/auth/register" className="text-violet-600 font-medium hover:text-violet-700 transition-colors">
                Créer un compte
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
