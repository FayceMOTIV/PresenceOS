'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cookie, Settings, X } from 'lucide-react';
import Link from 'next/link';

type CookiePreferences = {
  essential: boolean;
  analytics: boolean;
  marketing: boolean;
};

const DEFAULT_PREFERENCES: CookiePreferences = {
  essential: true,
  analytics: false,
  marketing: false,
};

export default function CookieBanner() {
  const [showBanner, setShowBanner] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [preferences, setPreferences] = useState<CookiePreferences>(DEFAULT_PREFERENCES);

  useEffect(() => {
    const saved = localStorage.getItem('cookie_preferences');
    if (!saved) {
      setTimeout(() => setShowBanner(true), 2000);
    } else {
      setPreferences(JSON.parse(saved));
    }
  }, []);

  const savePreferences = (prefs: CookiePreferences) => {
    localStorage.setItem('cookie_preferences', JSON.stringify(prefs));
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    setPreferences(prefs);
    setShowBanner(false);
    setShowSettings(false);
  };

  const acceptAll = () => savePreferences({ essential: true, analytics: true, marketing: true });
  const rejectAll = () => savePreferences({ essential: true, analytics: false, marketing: false });

  return (
    <>
      <AnimatePresence>
        {showBanner && !showSettings && (
          <motion.div
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 100, opacity: 0 }}
            className="fixed bottom-0 left-0 right-0 z-50 p-4 md:p-6"
          >
            <div className="max-w-4xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-elevated overflow-hidden">
              <div className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-violet-100 flex items-center justify-center flex-shrink-0">
                    <Cookie className="w-5 h-5 text-violet-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-900 mb-1">Cookies &amp; Confidentialité</h3>
                    <p className="text-gray-500 text-sm mb-3">
                      Nous utilisons des cookies essentiels pour le fonctionnement du site,
                      et des cookies optionnels (analytics, marketing) pour améliorer votre expérience.
                    </p>
                    <Link href="/legal/privacy" className="text-xs text-violet-600 hover:text-violet-700">
                      Politique de confidentialité
                    </Link>
                  </div>
                  <button onClick={() => setShowBanner(false)} className="text-gray-400 hover:text-gray-600 transition-colors">
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex flex-col sm:flex-row gap-3 mt-4">
                  <button
                    onClick={acceptAll}
                    className="flex-1 bg-gradient-to-r from-violet-600 to-purple-600 text-white px-5 py-2.5 rounded-xl font-medium hover:opacity-90 transition-opacity text-sm"
                  >
                    Tout accepter
                  </button>
                  <button
                    onClick={rejectAll}
                    className="flex-1 bg-gray-100 text-gray-700 px-5 py-2.5 rounded-xl font-medium hover:bg-gray-200 transition-colors text-sm"
                  >
                    Tout refuser
                  </button>
                  <button
                    onClick={() => setShowSettings(true)}
                    className="flex-1 border border-gray-200 text-gray-700 px-5 py-2.5 rounded-xl font-medium hover:border-violet-300 transition-colors inline-flex items-center justify-center gap-2 text-sm"
                  >
                    <Settings className="w-4 h-4" />
                    Personnaliser
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white border border-gray-200 rounded-2xl shadow-floating max-w-lg w-full max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    <Settings className="w-5 h-5 text-violet-600" />
                    Préférences cookies
                  </h3>
                  <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-gray-600">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-800">Cookies essentiels</h4>
                      <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-medium">Toujours actifs</span>
                    </div>
                    <p className="text-gray-500 text-sm">Nécessaires au fonctionnement du site (session, sécurité, préférences).</p>
                  </div>

                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-800">Cookies analytics</h4>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={preferences.analytics}
                          onChange={(e) => setPreferences({ ...preferences, analytics: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-violet-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all after:shadow-sm peer-checked:bg-violet-600"></div>
                      </label>
                    </div>
                    <p className="text-gray-500 text-sm">Nous aident à comprendre comment vous utilisez le site (Mixpanel). Données anonymisées.</p>
                  </div>

                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-800">Cookies marketing</h4>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={preferences.marketing}
                          onChange={(e) => setPreferences({ ...preferences, marketing: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-violet-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all after:shadow-sm peer-checked:bg-violet-600"></div>
                      </label>
                    </div>
                    <p className="text-gray-500 text-sm">Publicités pertinentes et retargeting (Facebook Pixel, TikTok Pixel).</p>
                  </div>
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => savePreferences(preferences)}
                    className="flex-1 bg-gradient-to-r from-violet-600 to-purple-600 text-white px-5 py-2.5 rounded-xl font-medium hover:opacity-90 transition-opacity text-sm"
                  >
                    Enregistrer mes préférences
                  </button>
                  <button
                    onClick={() => setShowSettings(false)}
                    className="flex-1 border border-gray-200 text-gray-700 px-5 py-2.5 rounded-xl font-medium hover:bg-gray-50 transition-colors text-sm"
                  >
                    Annuler
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export function useCookiePreferences(): CookiePreferences {
  const [prefs, setPrefs] = useState<CookiePreferences>(DEFAULT_PREFERENCES);
  useEffect(() => {
    const saved = localStorage.getItem('cookie_preferences');
    if (saved) setPrefs(JSON.parse(saved));
  }, []);
  return prefs;
}
