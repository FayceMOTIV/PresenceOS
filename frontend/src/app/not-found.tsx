import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-mesh-gradient-strong relative overflow-hidden">
      <div className="text-center space-y-6 px-4">
        <h1 className="text-7xl font-bold gradient-text">404</h1>
        <h2 className="text-2xl font-semibold text-gray-900">
          Page introuvable
        </h2>
        <p className="text-gray-500 max-w-md mx-auto">
          La page que vous cherchez n&apos;existe pas ou a ete deplacee.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl gradient-bg text-white font-medium shadow-md shadow-purple-500/20 hover:opacity-90 transition-opacity"
        >
          Retour au dashboard
        </Link>
      </div>
    </div>
  );
}
