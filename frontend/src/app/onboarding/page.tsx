'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { analytics, events } from '@/lib/analytics';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Instagram, Upload, Sparkles, Rocket, ArrowRight } from 'lucide-react';
import confetti from 'canvas-confetti';
import { Button } from '@/components/ui/button';

type Step = 1 | 2 | 3 | 4 | 5;

const STEPS = [
  { id: 1, title: 'Bienvenue', icon: Rocket },
  { id: 2, title: 'Instagram', icon: Instagram },
  { id: 3, title: 'Photo', icon: Upload },
  { id: 4, title: 'Caption IA', icon: Sparkles },
  { id: 5, title: 'Terminé', icon: Check },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    analytics.track(events.ONBOARDING_STARTED);
  }, []);

  const nextStep = () => {
    if (currentStep < 5) {
      setCurrentStep((currentStep + 1) as Step);
    }
  };

  const handleComplete = () => {
    analytics.track(events.ONBOARDING_COMPLETED);
    confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
    setCompleted(true);
    setTimeout(() => router.push('/dashboard'), 2500);
  };

  const skipToStudio = () => router.push('/studio');
  const skipToDashboard = () => router.push('/dashboard');

  if (completed) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-violet-600 to-purple-600">
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="text-center text-white">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1 }} className="inline-block mb-6">
            <Rocket className="w-24 h-24" />
          </motion.div>
          <h1 className="text-4xl font-bold mb-4">Félicitations !</h1>
          <p className="text-xl opacity-90">Votre espace est prêt</p>
          <p className="text-sm mt-2 opacity-70">Redirection vers le tableau de bord...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50/80 via-white to-violet-50/30">
      {/* Progress Bar */}
      <div className="fixed top-0 left-0 right-0 h-1.5 bg-gray-100 z-50">
        <motion.div
          className="h-full bg-gradient-to-r from-violet-500 to-purple-500"
          initial={{ width: '0%' }}
          animate={{ width: `${(currentStep / 5) * 100}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      <div className="container max-w-3xl mx-auto px-4 pt-20 pb-10">
        {/* Steps Indicator */}
        <div className="flex justify-between mb-12">
          {STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            return (
              <div key={step.id} className="flex flex-col items-center flex-1">
                <div className={`
                  w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all duration-300
                  ${isCompleted ? 'bg-green-500 text-white' : isActive ? 'bg-gradient-to-r from-violet-500 to-purple-500 text-white scale-110 shadow-lg shadow-violet-200' : 'bg-gray-100 text-gray-400'}
                `}>
                  {isCompleted ? <Check className="w-6 h-6" /> : <Icon className="w-6 h-6" />}
                </div>
                <span className={`text-xs text-center ${isActive ? 'font-bold text-violet-700' : 'text-gray-400'}`}>
                  {step.title}
                </span>
              </div>
            );
          })}
        </div>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="bg-white rounded-2xl p-8 md:p-12 shadow-sm border border-gray-100"
          >
            {currentStep === 1 && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-100 to-purple-100 flex items-center justify-center mx-auto mb-6">
                  <Rocket className="w-10 h-10 text-violet-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Bienvenue sur PresenceOS !</h2>
                <p className="text-gray-500 mb-8 text-lg max-w-md mx-auto">
                  En quelques étapes simples, configurez votre espace et commencez à publier automatiquement.
                </p>
                <Button variant="gradient" size="lg" onClick={nextStep}>
                  C&apos;est parti ! <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </div>
            )}

            {currentStep === 2 && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-pink-100 to-rose-100 flex items-center justify-center mx-auto mb-6">
                  <Instagram className="w-10 h-10 text-pink-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Connectez votre Instagram</h2>
                <p className="text-gray-500 mb-8">
                  Liez votre compte Instagram Business pour publier automatiquement vos posts.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button variant="gradient" size="lg" onClick={() => { router.push('/settings'); }}>
                    <Instagram className="w-5 h-5 mr-2" />
                    Connecter Instagram
                  </Button>
                  <Button variant="outline" size="lg" onClick={nextStep}>
                    Plus tard <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
                <p className="text-xs text-gray-400 mt-4">Vos données sont sécurisées et ne seront jamais partagées</p>
              </div>
            )}

            {currentStep === 3 && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center mx-auto mb-6">
                  <Upload className="w-10 h-10 text-blue-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Uploadez votre première photo</h2>
                <p className="text-gray-500 mb-8">
                  Choisissez une belle photo de votre restaurant ou de vos plats.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button variant="gradient" size="lg" onClick={() => { router.push('/studio'); }}>
                    <Upload className="w-5 h-5 mr-2" />
                    Aller au Studio
                  </Button>
                  <Button variant="outline" size="lg" onClick={nextStep}>
                    Plus tard <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {currentStep === 4 && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-amber-100 to-yellow-100 flex items-center justify-center mx-auto mb-6">
                  <Sparkles className="w-10 h-10 text-amber-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Générez avec l&apos;IA</h2>
                <p className="text-gray-500 mb-8">
                  Notre IA analyse votre photo et crée une caption parfaite pour vos réseaux sociaux.
                </p>
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                  <Button variant="gradient" size="lg" onClick={nextStep}>
                    Continuer <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </div>
              </div>
            )}

            {currentStep === 5 && (
              <div className="text-center">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-green-100 to-emerald-100 flex items-center justify-center mx-auto mb-6">
                  <Check className="w-10 h-10 text-green-600" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">Tout est prêt !</h2>
                <p className="text-gray-500 mb-8">
                  Votre espace PresenceOS est configuré. Commencez à créer et publier vos posts.
                </p>
                <Button variant="gradient" size="lg" onClick={handleComplete}>
                  Accéder au tableau de bord <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        {/* Skip */}
        {currentStep > 1 && currentStep < 5 && (
          <div className="text-center mt-6">
            <button onClick={skipToDashboard} className="text-gray-400 hover:text-violet-600 text-sm transition-colors">
              Passer pour l&apos;instant
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
