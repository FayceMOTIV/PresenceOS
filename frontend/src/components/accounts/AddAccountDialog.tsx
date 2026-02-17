"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Instagram,
  Facebook,
  Linkedin,
  ArrowLeft,
  Plus,
  Loader2,
  CheckCircle2,
} from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { connectorsApi } from "@/lib/api";
import { fireSuccessConfetti } from "@/lib/confetti";
import { useToast } from "@/hooks/use-toast";

// --- Types ---

type Platform = "instagram" | "facebook" | "tiktok" | "linkedin";

interface AddAccountDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  brandId: string;
  existingCounts: Record<string, number>;
  onAccountAdded: () => void;
}

// --- Platform config ---

const MAX_LIMITS: Record<Platform, number> = {
  instagram: 3,
  facebook: 2,
  tiktok: 2,
  linkedin: 1,
};

const PLATFORM_META: Record<
  Platform,
  {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    icon: React.ReactNode;
    usesOAuth: boolean;
  }
> = {
  instagram: {
    label: "Instagram",
    color: "#E4405F",
    bgColor: "rgba(228, 64, 95, 0.07)",
    borderColor: "rgba(228, 64, 95, 0.3)",
    icon: <Instagram size={26} />,
    usesOAuth: false,
  },
  facebook: {
    label: "Facebook",
    color: "#1877F2",
    bgColor: "rgba(24, 119, 242, 0.07)",
    borderColor: "rgba(24, 119, 242, 0.3)",
    icon: <Facebook size={26} />,
    usesOAuth: false,
  },
  tiktok: {
    label: "TikTok",
    color: "#111111",
    bgColor: "rgba(0,0,0,0.05)",
    borderColor: "rgba(0,0,0,0.15)",
    icon: (
      <svg
        width="26"
        height="26"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-label="TikTok"
      >
        <path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.32 6.32 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.78 1.52V6.77a4.85 4.85 0 0 1-1.01-.08z" />
      </svg>
    ),
    usesOAuth: false,
  },
  linkedin: {
    label: "LinkedIn",
    color: "#0A66C2",
    bgColor: "rgba(10, 102, 194, 0.07)",
    borderColor: "rgba(10, 102, 194, 0.3)",
    icon: <Linkedin size={26} />,
    usesOAuth: true,
  },
};

const PLATFORMS: Platform[] = ["instagram", "facebook", "tiktok", "linkedin"];

// --- Step animations ---

const stepVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 40 : -40,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction > 0 ? -40 : 40,
    opacity: 0,
  }),
};

// --- Component ---

export function AddAccountDialog({
  open,
  onOpenChange,
  brandId,
  existingCounts,
  onAccountAdded,
}: AddAccountDialogProps) {
  const { toast } = useToast();

  const [step, setStep] = useState<1 | 2>(1);
  const [direction, setDirection] = useState(1);
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | null>(null);
  const [username, setUsername] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  // --- Handlers ---

  function handleOpenChange(nextOpen: boolean) {
    onOpenChange(nextOpen);
    if (!nextOpen) {
      // Reset state when closed
      setTimeout(() => {
        setStep(1);
        setSelectedPlatform(null);
        setUsername("");
        setIsLoading(false);
        setIsSuccess(false);
        setDirection(1);
      }, 200);
    }
  }

  function handleSelectPlatform(platform: Platform) {
    setSelectedPlatform(platform);
    setDirection(1);
    setStep(2);
  }

  function handleBack() {
    setDirection(-1);
    setStep(1);
    setUsername("");
    setIsSuccess(false);
  }

  async function handleSubmitUsername() {
    if (!selectedPlatform) return;
    const cleanUsername = username.replace(/^@+/, "").trim();
    if (!cleanUsername) {
      toast({
        title: "Nom d'utilisateur requis",
        description: "Veuillez saisir un nom d'utilisateur.",
      });
      return;
    }

    setIsLoading(true);
    try {
      await connectorsApi.connectWithApiKey(
        selectedPlatform,
        brandId,
        "server",
        cleanUsername
      );
      setIsSuccess(true);
      fireSuccessConfetti();
      toast({
        title: "Compte connecté !",
        description: `@${cleanUsername} a bien été ajouté à votre marque.`,
      });
      setTimeout(() => {
        onAccountAdded();
        handleOpenChange(false);
      }, 1400);
    } catch (err: unknown) {
      const message =
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response &&
        err.response.data &&
        typeof err.response.data === "object" &&
        "detail" in err.response.data
          ? String((err.response.data as { detail: string }).detail)
          : "Une erreur est survenue. Veuillez réessayer.";
      toast({
        title: "Erreur de connexion",
        description: message,
      });
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLinkedInOAuth() {
    if (!selectedPlatform) return;
    setIsLoading(true);
    try {
      const { data } = await connectorsApi.getOAuthUrl("linkedin", brandId);
      if (data?.url) {
        window.location.href = data.url;
      } else {
        throw new Error("URL OAuth manquante.");
      }
    } catch {
      toast({
        title: "Erreur OAuth",
        description: "Impossible d'obtenir l'URL d'autorisation LinkedIn.",
      });
      setIsLoading(false);
    }
  }

  // --- Render helpers ---

  function getCountLabel(platform: Platform): string {
    const current = existingCounts[platform] ?? 0;
    const max = MAX_LIMITS[platform];
    return `${current}/${max}`;
  }

  function isMaxReached(platform: Platform): boolean {
    const current = existingCounts[platform] ?? 0;
    return current >= MAX_LIMITS[platform];
  }

  const meta = selectedPlatform ? PLATFORM_META[selectedPlatform] : null;

  // --- Render ---

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md rounded-2xl overflow-hidden p-0">
        {/* Animated steps container */}
        <div className="relative overflow-hidden min-h-[320px]">
          <AnimatePresence mode="wait" custom={direction}>
            {/* ---- STEP 1: Choose platform ---- */}
            {step === 1 && (
              <motion.div
                key="step-1"
                custom={direction}
                variants={stepVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.22, ease: "easeInOut" }}
                className="absolute inset-0 flex flex-col p-6"
              >
                <DialogHeader className="mb-5">
                  <DialogTitle className="text-lg font-semibold text-gray-900">
                    Ajouter un compte
                  </DialogTitle>
                  <DialogDescription className="text-sm text-gray-500">
                    Choisissez la plateforme que vous souhaitez connecter.
                  </DialogDescription>
                </DialogHeader>

                <div className="grid grid-cols-2 gap-3">
                  {PLATFORMS.map((platform) => {
                    const cfg = PLATFORM_META[platform];
                    const maxReached = isMaxReached(platform);
                    return (
                      <button
                        key={platform}
                        disabled={maxReached}
                        onClick={() => handleSelectPlatform(platform)}
                        className={[
                          "flex flex-col items-center gap-2.5 rounded-2xl border-2 p-4 transition-all duration-200 text-left",
                          maxReached
                            ? "opacity-40 cursor-not-allowed border-gray-200 bg-gray-50"
                            : "cursor-pointer border-gray-200 bg-white hover:border-opacity-60 hover:shadow-md active:scale-95",
                        ].join(" ")}
                      >
                        {/* Icon */}
                        <div
                          className="flex items-center justify-center rounded-xl p-2.5"
                          style={{
                            color: maxReached ? "#9ca3af" : cfg.color,
                            backgroundColor: maxReached
                              ? "rgba(0,0,0,0.04)"
                              : cfg.bgColor,
                          }}
                        >
                          {cfg.icon}
                        </div>

                        {/* Label */}
                        <span
                          className={`text-sm font-semibold ${
                            maxReached ? "text-gray-400" : "text-gray-800"
                          }`}
                        >
                          {cfg.label}
                        </span>

                        {/* Count pill */}
                        <span
                          className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            maxReached
                              ? "bg-gray-100 text-gray-400"
                              : "bg-violet-100 text-violet-700"
                          }`}
                        >
                          {getCountLabel(platform)}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </motion.div>
            )}

            {/* ---- STEP 2: Connect ---- */}
            {step === 2 && selectedPlatform && meta && (
              <motion.div
                key="step-2"
                custom={direction}
                variants={stepVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={{ duration: 0.22, ease: "easeInOut" }}
                className="absolute inset-0 flex flex-col p-6"
              >
                {/* Back button */}
                <button
                  onClick={handleBack}
                  className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors mb-5 w-fit"
                >
                  <ArrowLeft size={15} />
                  Retour
                </button>

                <DialogHeader className="mb-6">
                  {/* Platform icon */}
                  <div
                    className="inline-flex items-center justify-center rounded-2xl p-3 mb-3 w-fit"
                    style={{
                      color: meta.color,
                      backgroundColor: meta.bgColor,
                      border: `1px solid ${meta.borderColor}`,
                    }}
                  >
                    {meta.icon}
                  </div>
                  <DialogTitle className="text-lg font-semibold text-gray-900">
                    Connecter {meta.label}
                  </DialogTitle>
                  <DialogDescription className="text-sm text-gray-500">
                    {meta.usesOAuth
                      ? "Vous serez redirigé vers LinkedIn pour autoriser l'accès."
                      : `Entrez le nom d'utilisateur du compte ${meta.label} à connecter.`}
                  </DialogDescription>
                </DialogHeader>

                {/* LinkedIn OAuth flow */}
                {meta.usesOAuth ? (
                  <div className="flex flex-col gap-3">
                    <Button
                      onClick={handleLinkedInOAuth}
                      disabled={isLoading}
                      className="w-full h-11 rounded-xl font-semibold text-white"
                      style={{ backgroundColor: meta.color }}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 size={16} className="animate-spin mr-2" />
                          Redirection...
                        </>
                      ) : (
                        <>
                          <Linkedin size={16} className="mr-2" />
                          Autoriser via LinkedIn
                        </>
                      )}
                    </Button>
                  </div>
                ) : (
                  /* Upload-post platform (IG / FB / TikTok) — username flow */
                  <div className="flex flex-col gap-3">
                    {isSuccess ? (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="flex flex-col items-center gap-3 py-4 text-center"
                      >
                        <div className="flex items-center justify-center w-14 h-14 rounded-full bg-emerald-100">
                          <CheckCircle2 size={28} className="text-emerald-600" />
                        </div>
                        <p className="text-base font-semibold text-gray-900">
                          Compte connecté !
                        </p>
                        <p className="text-sm text-gray-500">
                          @{username.replace(/^@+/, "")} a été ajouté avec succès.
                        </p>
                      </motion.div>
                    ) : (
                      <>
                        <div className="relative">
                          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm select-none">
                            @
                          </span>
                          <Input
                            className="pl-7 h-11 rounded-xl border-gray-200 focus-visible:ring-violet-400 text-sm"
                            placeholder="moncompte"
                            value={username.replace(/^@+/, "")}
                            onChange={(e) => setUsername(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") handleSubmitUsername();
                            }}
                            autoFocus
                            disabled={isLoading}
                          />
                        </div>

                        <Button
                          onClick={handleSubmitUsername}
                          disabled={isLoading || !username.replace(/^@+/, "").trim()}
                          className="w-full h-11 rounded-xl font-semibold bg-violet-600 hover:bg-violet-700 text-white"
                        >
                          {isLoading ? (
                            <>
                              <Loader2 size={16} className="animate-spin mr-2" />
                              Connexion en cours...
                            </>
                          ) : (
                            <>
                              <Plus size={16} className="mr-2" />
                              Connecter le compte
                            </>
                          )}
                        </Button>
                      </>
                    )}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default AddAccountDialog;
