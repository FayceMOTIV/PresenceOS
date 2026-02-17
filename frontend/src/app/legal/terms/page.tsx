import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50/80 via-white to-violet-50/30">
      <div className="container max-w-4xl mx-auto px-4 py-12">
        <Link href="/dashboard" className="inline-flex items-center gap-2 text-violet-600 hover:text-violet-700 mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Retour au tableau de bord
        </Link>

        <h1 className="text-4xl font-bold text-gray-900 mb-2">Conditions Générales d&apos;Utilisation</h1>
        <p className="text-gray-500 mb-8">Dernière mise à jour : 17 février 2026</p>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 md:p-12 space-y-8">
          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">1. Acceptation des conditions</h2>
            <p className="text-gray-600">
              En accédant et en utilisant PresenceOS (&quot;le Service&quot;), vous acceptez d&apos;être lié par
              ces Conditions Générales d&apos;Utilisation. Si vous n&apos;acceptez pas ces conditions,
              veuillez ne pas utiliser le Service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">2. Description du service</h2>
            <p className="text-gray-600 mb-4">
              PresenceOS est une plateforme SaaS de marketing automation pour restaurants qui permet :
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>L&apos;upload de photos de plats et restaurants</li>
              <li>La génération automatique de captions avec IA</li>
              <li>La publication automatique sur les réseaux sociaux (Instagram, Facebook, TikTok)</li>
              <li>L&apos;analyse de performance des publications</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">3. Compte utilisateur</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">3.1 Création de compte</h3>
            <p className="text-gray-600 mb-4">
              Pour utiliser le Service, vous devez créer un compte en fournissant des informations
              exactes et à jour. Vous êtes responsable de maintenir la confidentialité de vos
              identifiants de connexion.
            </p>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">3.2 Responsabilités</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Vous êtes responsable de toute activité effectuée via votre compte</li>
              <li>Vous devez nous informer immédiatement de toute utilisation non autorisée</li>
              <li>Vous ne devez pas partager vos identifiants avec des tiers</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">4. Utilisation acceptable</h2>
            <p className="text-gray-600 mb-4">Vous acceptez de NE PAS :</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Utiliser le Service pour des activités illégales ou non autorisées</li>
              <li>Upload du contenu offensant, diffamatoire ou violant des droits d&apos;auteur</li>
              <li>Tenter de contourner les mesures de sécurité du Service</li>
              <li>Utiliser des bots ou scripts automatisés sans autorisation</li>
              <li>Revendre ou redistribuer le Service sans autorisation écrite</li>
              <li>Spammer ou abuser du système de publication</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">5. Propriété intellectuelle</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">5.1 Votre contenu</h3>
            <p className="text-gray-600 mb-4">
              Vous conservez tous les droits sur le contenu que vous uploadez (photos, textes).
              En utilisant le Service, vous nous accordez une licence mondiale, non-exclusive,
              pour stocker, traiter et publier votre contenu uniquement dans le cadre du Service.
            </p>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">5.2 Notre contenu</h3>
            <p className="text-gray-600">
              Le Service, incluant son code, design, logos et marques, est la propriété de
              PresenceOS et est protégé par les lois sur la propriété intellectuelle.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">6. Tarification et paiements</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">6.1 Plans d&apos;abonnement</h3>
            <p className="text-gray-600 mb-4">
              Le Service propose différents plans d&apos;abonnement (Free, Pro, Business). Les prix
              sont indiqués en euros (EUR) et sont susceptibles de changer avec un préavis de 30 jours.
            </p>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">6.2 Facturation</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Les paiements sont mensuels ou annuels selon le plan choisi</li>
              <li>Les paiements sont traités via Stripe de manière sécurisée</li>
              <li>Pas de remboursement au prorata en cas d&apos;annulation</li>
              <li>Vous pouvez annuler à tout moment, l&apos;accès reste actif jusqu&apos;à la fin de la période payée</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">7. Résiliation</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">7.1 Par vous</h3>
            <p className="text-gray-600 mb-4">
              Vous pouvez annuler votre abonnement à tout moment depuis votre compte.
              L&apos;annulation prendra effet à la fin de votre période de facturation en cours.
            </p>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">7.2 Par nous</h3>
            <p className="text-gray-600">
              Nous pouvons suspendre ou résilier votre compte en cas de violation de ces CGU,
              avec ou sans préavis. En cas de violation grave, aucun remboursement ne sera effectué.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">8. Limitation de responsabilité</h2>
            <p className="text-gray-600 mb-4">
              LE SERVICE EST FOURNI &quot;EN L&apos;ÉTAT&quot; SANS GARANTIE D&apos;AUCUNE SORTE. PRESENCEOS NE GARANTIT PAS :
            </p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Que le Service sera ininterrompu ou sans erreur</li>
              <li>Que les résultats obtenus seront exacts ou fiables</li>
              <li>Que les publications seront toujours réussies (dépend des API tierces)</li>
            </ul>
            <p className="text-gray-600 mt-4">
              EN AUCUN CAS PRESENCEOS NE SERA RESPONSABLE DE DOMMAGES INDIRECTS,
              ACCESSOIRES OU PUNITIFS, Y COMPRIS LA PERTE DE PROFITS OU DE DONNÉES.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">9. Modifications des CGU</h2>
            <p className="text-gray-600">
              Nous nous réservons le droit de modifier ces CGU à tout moment. Les modifications
              importantes seront notifiées par email 30 jours avant leur prise d&apos;effet.
              Votre utilisation continue du Service après ces modifications constitue votre
              acceptation des nouvelles CGU.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">10. Droit applicable</h2>
            <p className="text-gray-600">
              Ces CGU sont régies par les lois françaises. Tout litige sera soumis à la
              compétence exclusive des tribunaux de Paris, France.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">11. Contact</h2>
            <p className="text-gray-600">
              Pour toute question concernant ces CGU, contactez-nous à :
            </p>
            <ul className="list-none text-gray-600 mt-2 space-y-1">
              <li>Email : legal@presenceos.com</li>
              <li>Adresse : Paris, France</li>
            </ul>
          </section>

          <section className="border-t border-gray-200 pt-6">
            <p className="text-sm text-gray-400">
              En utilisant PresenceOS, vous reconnaissez avoir lu, compris et accepté
              ces Conditions Générales d&apos;Utilisation.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
