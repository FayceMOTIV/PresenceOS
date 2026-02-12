"use client";

import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import {
  Sparkles,
  Calendar,
  BarChart3,
  Zap,
  Instagram,
  Linkedin,
  ChevronRight,
} from "lucide-react";
import Link from "next/link";

const features = [
  {
    icon: Sparkles,
    title: "IA qui comprend votre marque",
    description:
      "Génération de contenu personnalisé qui respecte votre ton et votre identité.",
  },
  {
    icon: Calendar,
    title: "Planification intelligente",
    description:
      "Calendrier éditorial automatique avec les meilleurs créneaux de publication.",
  },
  {
    icon: BarChart3,
    title: "Analytics & Learning",
    description:
      "L'IA apprend de vos performances pour améliorer continuellement vos résultats.",
  },
  {
    icon: Zap,
    title: "Publication multi-plateforme",
    description:
      "Instagram, TikTok, LinkedIn, Facebook - tout depuis une seule interface.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 glass border-b">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">PresenceOS</span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition">
              Fonctionnalités
            </a>
            <a href="#pricing" className="text-muted-foreground hover:text-foreground transition">
              Tarifs
            </a>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/auth/login">
              <Button variant="ghost">Connexion</Button>
            </Link>
            <Link href="/auth/register">
              <Button variant="gradient">Commencer</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-20 px-6">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              Agent Marketing IA pour entrepreneurs
            </div>
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Votre présence digitale,
              <br />
              <span className="gradient-text">automatisée par l&apos;IA</span>
            </h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
              PresenceOS planifie, génère et publie du contenu adapté à votre
              marque sur tous vos réseaux sociaux. Gagnez 10h par semaine.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/auth/register">
                <Button size="lg" variant="gradient" className="text-lg px-8">
                  Démarrer gratuitement
                  <ChevronRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="text-lg px-8">
                Voir la démo
              </Button>
            </div>
            <div className="flex items-center justify-center gap-6 mt-8 text-muted-foreground">
              <div className="flex items-center gap-2">
                <Instagram className="w-5 h-5" />
                <span className="text-sm">Instagram</span>
              </div>
              <div className="flex items-center gap-2">
                <svg
                  className="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z" />
                </svg>
                <span className="text-sm">TikTok</span>
              </div>
              <div className="flex items-center gap-2">
                <Linkedin className="w-5 h-5" />
                <span className="text-sm">LinkedIn</span>
              </div>
            </div>
          </motion.div>

          {/* Dashboard Preview */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="mt-16 relative"
          >
            <div className="glass-card rounded-2xl overflow-hidden">
              <div className="bg-gradient-to-br from-background to-muted p-8">
                <div className="grid grid-cols-3 gap-4">
                  {/* Mock Dashboard */}
                  <div className="col-span-2 space-y-4">
                    <div className="h-8 w-48 bg-muted-foreground/20 rounded animate-pulse" />
                    <div className="grid grid-cols-3 gap-4">
                      {[1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className="glass-card rounded-xl p-4 space-y-2"
                        >
                          <div className="h-4 w-16 bg-muted-foreground/20 rounded" />
                          <div className="h-8 w-24 bg-primary/30 rounded" />
                        </div>
                      ))}
                    </div>
                    <div className="glass-card rounded-xl p-4 h-48">
                      <div className="h-4 w-32 bg-muted-foreground/20 rounded mb-4" />
                      <div className="flex gap-2 h-32">
                        {[60, 80, 45, 90, 70, 55, 85].map((h, i) => (
                          <div
                            key={i}
                            className="flex-1 bg-primary/30 rounded-t"
                            style={{ height: `${h}%`, marginTop: "auto" }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="space-y-4">
                    <div className="glass-card rounded-xl p-4 space-y-3">
                      <div className="h-4 w-24 bg-muted-foreground/20 rounded" />
                      {[1, 2, 3].map((i) => (
                        <div
                          key={i}
                          className="flex items-center gap-3 p-2 rounded-lg bg-muted/50"
                        >
                          <div className="w-10 h-10 rounded bg-muted-foreground/20" />
                          <div className="space-y-1 flex-1">
                            <div className="h-3 w-full bg-muted-foreground/20 rounded" />
                            <div className="h-2 w-2/3 bg-muted-foreground/10 rounded" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-3/4 h-8 bg-gradient-to-t from-background to-transparent" />
          </motion.div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">
              Tout ce dont vous avez besoin
            </h2>
            <p className="text-muted-foreground text-lg">
              Une solution complète pour gérer votre présence digitale
            </p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="glass-card rounded-2xl p-6 hover:scale-[1.02] transition-transform"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                  <feature.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="container mx-auto max-w-4xl">
          <div className="glass-card rounded-3xl p-12 text-center bg-gradient-to-br from-primary/10 to-purple-600/10">
            <h2 className="text-4xl font-bold mb-4">
              Prêt à automatiser votre marketing?
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              Rejoignez les entrepreneurs qui gagnent du temps avec PresenceOS
            </p>
            <Link href="/auth/register">
              <Button size="lg" variant="gradient" className="text-lg px-8">
                Commencer maintenant
                <ChevronRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12 px-6">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold">PresenceOS</span>
            </div>
            <p className="text-muted-foreground text-sm">
              © 2024 PresenceOS. Tous droits réservés.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
