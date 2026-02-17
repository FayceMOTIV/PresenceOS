import React from 'react';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50/80 via-white to-violet-50/30">
      <div className="container max-w-4xl mx-auto px-4 py-12">
        <Link href="/dashboard" className="inline-flex items-center gap-2 text-violet-600 hover:text-violet-700 mb-8 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          Retour au tableau de bord
        </Link>

        <h1 className="text-4xl font-bold text-gray-900 mb-2">Politique de Confidentialité</h1>
        <p className="text-gray-500 mb-8">Dernière mise à jour : 17 février 2026</p>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 md:p-12 space-y-8">
          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">1. Introduction</h2>
            <p className="text-gray-600">
              PresenceOS (&quot;nous&quot;, &quot;notre&quot;) s&apos;engage à protéger votre vie privée.
              Cette politique explique comment nous collectons, utilisons, partageons et
              protégeons vos données personnelles conformément au RGPD (Règlement Général
              sur la Protection des Données).
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">2. Données collectées</h2>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">2.1 Données que vous fournissez</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Compte :</strong> nom, email, mot de passe (hashé), nom du restaurant</li>
              <li><strong>Profil :</strong> photo de profil, bio, informations restaurant</li>
              <li><strong>Contenu :</strong> photos uploadées, captions générées, posts publiés</li>
              <li><strong>Paiement :</strong> informations de facturation (traitées par Stripe, non stockées chez nous)</li>
            </ul>
            <h3 className="text-xl font-semibold text-gray-800 mb-2 mt-4">2.2 Données collectées automatiquement</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Logs techniques :</strong> adresse IP, navigateur, système d&apos;exploitation</li>
              <li><strong>Cookies :</strong> préférences, session, analytics (voir section Cookies)</li>
              <li><strong>Usage :</strong> pages visitées, fonctionnalités utilisées, temps passé</li>
              <li><strong>Performance :</strong> erreurs, temps de chargement, métriques techniques</li>
            </ul>
            <h3 className="text-xl font-semibold text-gray-800 mb-2 mt-4">2.3 Données tierces</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Instagram/Facebook :</strong> tokens d&apos;accès, ID de compte, statistiques de posts</li>
              <li><strong>TikTok :</strong> tokens d&apos;accès, ID de compte (si connecté)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">3. Utilisation des données</h2>
            <p className="text-gray-600 mb-4">Nous utilisons vos données pour :</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Fournir le Service :</strong> analyser photos, générer captions, publier posts</li>
              <li><strong>Améliorer le Service :</strong> analytics, bug fixes, nouvelles fonctionnalités</li>
              <li><strong>Communication :</strong> emails transactionnels, support client, updates importants</li>
              <li><strong>Facturation :</strong> gérer abonnements, générer factures</li>
              <li><strong>Sécurité :</strong> détecter fraudes, protéger contre abus</li>
              <li><strong>Légal :</strong> respecter obligations légales, résoudre litiges</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">4. Base légale du traitement (RGPD)</h2>
            <div className="bg-violet-50/50 rounded-xl p-6 space-y-4 border border-violet-100">
              <div>
                <h4 className="font-semibold text-violet-700">Exécution du contrat</h4>
                <p className="text-gray-600 text-sm">Traitement nécessaire pour fournir le Service (Article 6.1.b RGPD)</p>
              </div>
              <div>
                <h4 className="font-semibold text-violet-700">Consentement</h4>
                <p className="text-gray-600 text-sm">Cookies analytics, marketing emails (Article 6.1.a RGPD)</p>
              </div>
              <div>
                <h4 className="font-semibold text-violet-700">Intérêt légitime</h4>
                <p className="text-gray-600 text-sm">Amélioration du Service, sécurité, analytics (Article 6.1.f RGPD)</p>
              </div>
              <div>
                <h4 className="font-semibold text-violet-700">Obligation légale</h4>
                <p className="text-gray-600 text-sm">Facturation, déclarations fiscales (Article 6.1.c RGPD)</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">5. Partage des données</h2>
            <p className="text-gray-600 mb-4">Nous ne vendons JAMAIS vos données. Nous partageons uniquement avec :</p>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">5.1 Sous-traitants</h3>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Hébergement :</strong> serveurs sécurisés (Docker, PostgreSQL)</li>
              <li><strong>Stripe :</strong> traitement paiements</li>
              <li><strong>OpenAI/Anthropic :</strong> génération IA (données anonymisées)</li>
              <li><strong>Sentry :</strong> monitoring erreurs</li>
            </ul>
            <h3 className="text-xl font-semibold text-gray-800 mb-2 mt-4">5.2 Plateformes sociales</h3>
            <p className="text-gray-600">Instagram, Facebook, TikTok : uniquement pour publier vos posts (avec votre autorisation explicite)</p>
            <h3 className="text-xl font-semibold text-gray-800 mb-2 mt-4">5.3 Obligations légales</h3>
            <p className="text-gray-600">Autorités compétentes si requis par la loi (ordre judiciaire, enquête)</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">6. Durée de conservation</h2>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li><strong>Compte actif :</strong> tant que votre compte existe</li>
              <li><strong>Compte supprimé :</strong> 30 jours (backup), puis suppression définitive</li>
              <li><strong>Logs techniques :</strong> 90 jours maximum</li>
              <li><strong>Données comptables :</strong> 10 ans (obligation légale France)</li>
              <li><strong>Cookies analytics :</strong> 13 mois maximum</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">7. Vos droits (RGPD)</h2>
            <div className="bg-gradient-to-r from-violet-50 to-purple-50 rounded-xl p-6 border border-violet-100">
              <p className="text-gray-600 mb-4">Vous disposez des droits suivants :</p>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Accès</strong>
                    <p className="text-gray-500 text-sm">Obtenir une copie de vos données</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Rectification</strong>
                    <p className="text-gray-500 text-sm">Corriger des données inexactes</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Suppression</strong>
                    <p className="text-gray-500 text-sm">Supprimer votre compte et données (droit à l&apos;oubli)</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Portabilité</strong>
                    <p className="text-gray-500 text-sm">Recevoir vos données en format exploitable (JSON)</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Opposition</strong>
                    <p className="text-gray-500 text-sm">Refuser le traitement (marketing, analytics)</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Limitation</strong>
                    <p className="text-gray-500 text-sm">Limiter le traitement dans certains cas</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-violet-600 font-bold">→</span>
                  <div>
                    <strong className="text-gray-800">Plainte CNIL</strong>
                    <p className="text-gray-500 text-sm">Déposer une réclamation auprès de la CNIL</p>
                  </div>
                </li>
              </ul>
              <div className="mt-6 pt-6 border-t border-violet-200/60">
                <p className="text-sm text-gray-600">
                  Pour exercer vos droits : <strong className="text-violet-700">privacy@presenceos.com</strong>
                  <br />Nous répondrons sous 30 jours maximum (délai légal RGPD)
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">8. Sécurité des données</h2>
            <p className="text-gray-600 mb-4">Mesures de sécurité mises en place :</p>
            <ul className="list-disc pl-6 text-gray-600 space-y-2">
              <li>Chiffrement HTTPS (TLS 1.3) pour toutes les communications</li>
              <li>Mots de passe hashés avec bcrypt (impossible de les lire)</li>
              <li>Authentification JWT sécurisée</li>
              <li>Backups chiffrés quotidiens</li>
              <li>Accès restreint aux données (principe du moindre privilège)</li>
              <li>Monitoring 24/7 des tentatives d&apos;intrusion</li>
              <li>Audits de sécurité réguliers</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">9. Cookies</h2>
            <p className="text-gray-600 mb-4">Nous utilisons 3 types de cookies :</p>
            <div className="space-y-4">
              <div className="bg-green-50 rounded-lg p-4 border border-green-100">
                <h4 className="font-semibold text-green-700 mb-2">Cookies essentiels (obligatoires)</h4>
                <p className="text-gray-600 text-sm">
                  Session utilisateur, préférences langue, sécurité CSRF
                  <br /><span className="text-gray-400">Durée : session ou 30 jours</span>
                </p>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-100">
                <h4 className="font-semibold text-yellow-700 mb-2">Cookies analytics (optionnels)</h4>
                <p className="text-gray-600 text-sm">
                  Mixpanel : pages vues, engagement
                  <br /><span className="text-gray-400">Durée : 13 mois | Désactivables dans les paramètres</span>
                </p>
              </div>
              <div className="bg-violet-50 rounded-lg p-4 border border-violet-100">
                <h4 className="font-semibold text-violet-700 mb-2">Cookies marketing (optionnels)</h4>
                <p className="text-gray-600 text-sm">
                  Publicité ciblée, retargeting
                  <br /><span className="text-gray-400">Durée : 13 mois | Désactivables dans les paramètres</span>
                </p>
              </div>
            </div>
            <p className="text-gray-600 mt-4">
              Vous pouvez gérer vos préférences cookies à tout moment via notre banner ou vos paramètres.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">10. Transferts internationaux</h2>
            <p className="text-gray-600">
              Vos données sont principalement stockées dans l&apos;UE (serveurs en France/Allemagne).
              Certains sous-traitants (OpenAI, Anthropic) peuvent traiter des données aux USA
              sous clauses contractuelles types (CCT) conformes au RGPD.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">11. Mineurs</h2>
            <p className="text-gray-600">
              Le Service n&apos;est pas destiné aux personnes de moins de 18 ans.
              Nous ne collectons pas sciemment de données de mineurs. Si vous êtes un parent et
              découvrez que votre enfant nous a fourni des données, contactez-nous immédiatement.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">12. Modifications</h2>
            <p className="text-gray-600">
              Nous pouvons modifier cette politique. Les modifications importantes seront notifiées
              par email 30 jours avant leur prise d&apos;effet. La date de dernière mise à jour est
              affichée en haut de cette page.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-violet-700 mb-4">13. Contact &amp; DPO</h2>
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-100">
              <p className="text-gray-600 mb-4">Pour toute question sur vos données :</p>
              <ul className="list-none text-gray-600 space-y-2">
                <li><strong>DPO (Délégué à la Protection des Données) :</strong> dpo@presenceos.com</li>
                <li><strong>Privacy :</strong> privacy@presenceos.com</li>
                <li><strong>Adresse :</strong> Paris, France</li>
                <li><strong>CNIL :</strong>{' '}
                  <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer" className="text-violet-600 hover:text-violet-700">
                    www.cnil.fr
                  </a>
                </li>
              </ul>
            </div>
          </section>

          <section className="border-t border-gray-200 pt-6">
            <p className="text-sm text-gray-400">
              Cette politique est conforme au RGPD (UE 2016/679), à la loi Informatique et Libertés,
              et aux directives ePrivacy.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
