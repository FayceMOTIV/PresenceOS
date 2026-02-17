'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronDown, MessageCircle, Mail } from 'lucide-react';
import { HelpTooltip } from '@/components/ui/help-tooltip';

const FAQ_CATEGORIES = [
  {
    name: 'Démarrage',
    icon: '🚀',
    faqs: [
      {
        q: 'Comment connecter mon compte Instagram ?',
        a: "Allez dans Réglages → Plateformes → Instagram. Cliquez sur \"Connecter\". Vous serez redirigé vers Facebook pour autoriser l'accès. Important : vous devez avoir un compte Instagram BUSINESS (pas personnel)."
      },
      {
        q: 'Pourquoi mes posts ne se publient pas ?',
        a: "Vérifiez : 1) Votre compte Instagram est bien connecté, 2) Votre compte est Instagram Business (pas Creator ou Personnel), 3) Votre caption ne contient pas de hashtags bannis, 4) Votre photo respecte les dimensions Instagram (min 400x400px)."
      },
      {
        q: 'Combien de posts puis-je publier par jour ?',
        a: "Plan Free : 5 posts/jour. Plan Pro : 50 posts/jour. Plan Business : 500 posts/jour. Ces limites protègent votre compte Instagram des restrictions."
      },
    ]
  },
  {
    name: 'Facturation',
    icon: '💳',
    faqs: [
      {
        q: "Comment annuler mon abonnement ?",
        a: "Allez dans Réglages → Facturation → Gérer l'abonnement. Vous pouvez annuler à tout moment. Votre accès reste actif jusqu'à la fin de votre période de facturation."
      },
      {
        q: 'Puis-je obtenir un remboursement ?',
        a: "Nous ne remboursons pas les mois partiels. Si vous annulez, votre abonnement reste actif jusqu'à la fin du mois payé. Exception : problèmes techniques majeurs dans les 7 premiers jours."
      },
    ]
  },
  {
    name: 'IA & Captions',
    icon: '🤖',
    faqs: [
      {
        q: 'Comment améliorer la qualité des captions ?',
        a: "Conseils : 1) Uploadez des photos de haute qualité, 2) Utilisez des photos avec un sujet clair, 3) Définissez votre voix de marque dans Réglages → Marque, 4) Donnez des exemples de captions que vous aimez."
      },
      {
        q: 'Puis-je personnaliser le ton ?',
        a: "Oui ! Allez dans Réglages → Voix de marque. Vous pouvez choisir : Professionnel, Décontracté, Fun, Luxe, Authentique. Vous pouvez aussi donner des exemples."
      },
    ]
  },
  {
    name: 'Photos & Médias',
    icon: '📸',
    faqs: [
      {
        q: 'Quels formats sont acceptés ?',
        a: "Photos : JPG, PNG, WebP. Taille max : 10 Mo. Dimensions min : 400x400px, max : 8000x8000px. Ratio recommandé : 1:1 (carré) ou 4:5 (portrait)."
      },
      {
        q: 'Mes photos sont-elles sécurisées ?',
        a: "Oui. Vos photos sont chiffrées au repos et en transit (HTTPS). Stockage sur serveurs conformes RGPD. Nous ne partageons JAMAIS vos photos avec des tiers."
      },
    ]
  },
  {
    name: 'Technique',
    icon: '🔧',
    faqs: [
      {
        q: 'Puis-je programmer des posts à l\'avance ?',
        a: "Oui. Allez dans Calendrier. Vous pouvez programmer jusqu'à 30 jours à l'avance. Le post sera publié automatiquement à l'heure choisie."
      },
      {
        q: 'Puis-je connecter plusieurs comptes ?',
        a: "Plan Free : 1 compte. Plan Pro : 3 comptes. Plan Business : comptes illimités."
      },
    ]
  },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedIndex, setExpandedIndex] = useState<string | null>(null);

  const toggleFAQ = (catIdx: number, faqIdx: number) => {
    const key = `${catIdx}-${faqIdx}`;
    setExpandedIndex(expandedIndex === key ? null : key);
  };

  const filtered = FAQ_CATEGORIES.map(cat => ({
    ...cat,
    faqs: cat.faqs.filter(f =>
      f.q.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.a.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(cat => cat.faqs.length > 0);

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Centre d&apos;aide <HelpTooltip content="Trouvez des réponses à vos questions les plus fréquentes." />
        </h1>
        <p className="text-muted-foreground">Trouvez rapidement des réponses à vos questions</p>
      </div>

      {/* Search */}
      <div className="relative max-w-2xl">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher dans la FAQ..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-white border border-gray-200 rounded-xl pl-12 pr-4 py-3 text-gray-900 placeholder-gray-400 focus:border-violet-400 focus:outline-none focus:ring-2 focus:ring-violet-100 transition-all"
        />
      </div>

      {/* FAQ */}
      <div className="space-y-6">
        {filtered.map((cat, catIdx) => (
          <div key={catIdx} className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span>{cat.icon}</span> {cat.name}
            </h2>
            <div className="space-y-3">
              {cat.faqs.map((faq, faqIdx) => {
                const key = `${catIdx}-${faqIdx}`;
                const isExpanded = expandedIndex === key;
                return (
                  <div key={faqIdx} className="bg-gray-50/80 rounded-xl overflow-hidden border border-gray-100">
                    <button
                      onClick={() => toggleFAQ(catIdx, faqIdx)}
                      className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-100/80 transition-colors"
                    >
                      <span className="text-left font-medium text-gray-800">{faq.q}</span>
                      <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                    </button>
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <div className="px-5 pb-4 text-gray-600 text-sm">{faq.a}</div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400 mb-2">Aucun résultat pour &quot;{searchQuery}&quot;</p>
          <p className="text-gray-400 text-sm">Essayez d&apos;autres mots-clés ou contactez notre support</p>
        </div>
      )}

      {/* Contact */}
      <div className="bg-gradient-to-r from-violet-50 to-purple-50 rounded-2xl p-8 border border-violet-100">
        <h3 className="text-xl font-bold text-gray-900 mb-2 text-center">Vous ne trouvez pas de réponse ?</h3>
        <p className="text-gray-500 text-center mb-6">Notre équipe support est là pour vous aider</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="mailto:help@presenceos.com"
            className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-purple-600 text-white px-6 py-3 rounded-xl font-medium hover:opacity-90 transition-opacity"
          >
            <Mail className="w-5 h-5" />
            help@presenceos.com
          </a>
        </div>
        <p className="text-xs text-gray-400 text-center mt-4">Temps de réponse moyen : moins de 24 heures</p>
      </div>
    </motion.div>
  );
}
