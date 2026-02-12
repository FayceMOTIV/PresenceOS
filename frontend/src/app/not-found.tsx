"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-6 px-4">
        <h1 className="text-7xl font-bold text-primary">404</h1>
        <h2 className="text-2xl font-semibold text-foreground">
          Page introuvable
        </h2>
        <p className="text-muted-foreground max-w-md mx-auto">
          La page que vous cherchez n&apos;existe pas ou a été déplacée.
        </p>
        <Button asChild>
          <Link href="/dashboard">
            <Home className="w-4 h-4 mr-2" />
            Retour au dashboard
          </Link>
        </Button>
      </div>
    </div>
  );
}
