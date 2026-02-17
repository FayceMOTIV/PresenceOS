"use client";

import { useState } from "react";
import HCaptcha from '@hcaptcha/react-hcaptcha';
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
import { validateEmail, validatePassword, validateName } from '@/lib/validation';

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
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
      const response = await authApi.register({...formData, ...(captchaToken && { captcha_token: captchaToken })});
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

  const fields = [
    { id: "full_name", label: "Nom complet", type: "text", placeholder: "Marie Dupont" },
    { id: "email", label: "Email", type: "email", placeholder: "vous@exemple.com" },
    { id: "password", label: "Mot de passe", type: "password", placeholder: "Min. 8 caractères" },
    { id: "workspace_name", label: "Nom de votre entreprise (optionnel)", type: "text", placeholder: "Ex: Mon Restaurant, Ma Boutique..." },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center bg-mesh-gradient-strong p-4 relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-0 left-1/3 w-96 h-96 bg-purple-200/30 rounded-full blur-3xl -translate-y-1/2" />
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-violet-200/20 rounded-full blur-3xl translate-y-1/2 translate-x-1/3" />

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
            <CardTitle className="text-2xl font-bold">Créer un compte</CardTitle>
            <CardDescription className="text-base">
              Rejoignez PresenceOS. C&apos;est gratuit et très simple !
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            <form onSubmit={handleSubmit} className="space-y-4">
              {fields.map((field, index) => (
                <motion.div
                  key={field.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + index * 0.08 }}
                  className="space-y-2"
                >
                  <label htmlFor={field.id} className="text-sm font-medium text-gray-700">
                    {field.label}
                  </label>
                  {field.id === "password" ? (
                    <>
                      <div className="relative">
                        <Input
                          id={field.id}
                          name={field.id}
                          type={showPassword ? "text" : "password"}
                          placeholder={field.placeholder}
                          value={formData[field.id as keyof typeof formData]}
                          onChange={handleChange}
                          required
                          minLength={8}
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
                      {formData.password && formData.password.length > 0 && formData.password.length < 8 && (
                        <p className="text-xs text-amber-600 mt-1">Le mot de passe doit faire au moins 8 caractères</p>
                      )}
                      {formData.password && formData.password.length >= 8 && (
                        <p className="text-xs text-green-600 mt-1">✓ Mot de passe valide</p>
                      )}
                    </>
                  ) : (
                    <Input
                      id={field.id}
                      name={field.id}
                      type={field.type}
                      placeholder={field.placeholder}
                      value={formData[field.id as keyof typeof formData]}
                      onChange={handleChange}
                      required={field.id !== "workspace_name"}
                      minLength={field.id === "password" ? 8 : undefined}
                    />
                  )}
                </motion.div>
              ))}
              <p className="text-xs text-muted-foreground -mt-2">
                {"Vous pourrez ajouter plusieurs marques dans votre espace de travail."}
              </p>
              {process.env.NEXT_PUBLIC_HCAPTCHA_SITEKEY && (
                <div className="flex justify-center">
                  <HCaptcha
                    sitekey={process.env.NEXT_PUBLIC_HCAPTCHA_SITEKEY}
                    onVerify={(token) => setCaptchaToken(token)}
                    onExpire={() => setCaptchaToken(null)}
                  />
                </div>
              )}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
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
                      Créer mon compte
                      <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                    </>
                  )}
                </Button>
              </motion.div>
            </form>
            <div className="mt-8 text-center text-sm">
              <span className="text-muted-foreground">Déjà un compte?</span>{" "}
              <Link href="/auth/login" className="text-violet-600 font-medium hover:text-violet-700 transition-colors">
                Se connecter
              </Link>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
