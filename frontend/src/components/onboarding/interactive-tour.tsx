'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight } from 'lucide-react';
import confetti from 'canvas-confetti';

interface TourStep {
  title: string;
  description: string;
  emoji: string;
}

const STEPS: TourStep[] = [
  {
    title: 'Bienvenue ! 👋',
    description: "Je vais vous montrer comment créer vos posts Instagram en 2 minutes. C\u2019est très simple !",
    emoji: '🎉',
  },
  {
    title: '1. Prenez une photo 📸',
    description: "Allez dans \u00ab Créer un post \u00bb et uploadez une photo de votre plat. C\u2019est tout ce qu\u2019il faut !",
    emoji: '📸',
  },
  {
    title: "2. L\u2019IA écrit le texte ✨",
    description: "Cliquez sur \u00ab Générer \u00bb et attendez 10 secondes. L\u2019intelligence artificielle crée 3 textes pour vous !",
    emoji: '✨',
  },
  {
    title: '3. Choisissez votre préféré 🎯',
    description: "Sélectionnez le texte que vous aimez le plus. Vous pouvez le modifier si vous voulez !",
    emoji: '🎯',
  },
  {
    title: '4. Publiez ! 🚀',
    description: "Cliquez sur \u00ab Publier maintenant \u00bb ou \u00ab Programmer \u00bb pour choisir quand publier. Terminé !",
    emoji: '🚀',
  },
  {
    title: 'Bravo ! Vous êtes prêt ! 🎊',
    description: "Vous savez maintenant créer des posts en 2 minutes. Essayez dès maintenant !",
    emoji: '🎊',
  },
];

export function InteractiveTour() {
  const [step, setStep] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const done = localStorage.getItem('tour-done');
    if (!done) {
      setTimeout(() => setOpen(true), 2000);
    }
  }, []);

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  const handleNext = () => {
    if (isLast) {
      confetti({ particleCount: 100, spread: 70 });
      localStorage.setItem('tour-done', 'true');
      setTimeout(() => setOpen(false), 2000);
    } else {
      confetti({ particleCount: 30, spread: 50, origin: { y: 0.7 } });
      setStep(s => s + 1);
    }
  };

  const handleSkip = () => {
    setOpen(false);
    localStorage.setItem('tour-skip', 'true');
  };

  if (!open) return null;

  return (
    <AnimatePresence>
      {/* Overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={handleSkip}
      />

      {/* Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.9 }}
        className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[60] w-full max-w-lg px-4"
      >
        <div className="bg-white rounded-3xl shadow-2xl p-8">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div className="text-6xl mb-2">{current.emoji}</div>
            <button
              onClick={handleSkip}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <h3 className="text-2xl font-bold mb-4 text-gray-900">
            {current.title}
          </h3>
          <p className="text-lg text-gray-600 mb-8 leading-relaxed">
            {current.description}
          </p>

          {/* Progress */}
          <div className="mb-6">
            <div className="flex justify-between text-sm text-gray-500 mb-2">
              <span>Étape {step + 1}/{STEPS.length}</span>
              <span>{Math.round(((step + 1) / STEPS.length) * 100)}%</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                initial={{ width: 0 }}
                animate={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            {!isLast && (
              <button
                onClick={handleSkip}
                className="flex-1 px-6 py-3 rounded-xl text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Passer
              </button>
            )}
            <button
              onClick={handleNext}
              className="flex-1 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold hover:shadow-lg transition-all flex items-center justify-center gap-2"
            >
              {isLast ? 'Commencer !' : 'Suivant'}
              {!isLast && <ArrowRight className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
