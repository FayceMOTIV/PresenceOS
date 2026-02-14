"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Save, Loader2, Building2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { workspacesApi } from "@/lib/api";
import { Workspace, UserRole } from "@/types";

interface WorkspaceTabProps {
  workspaceId: string | null;
  userRole: UserRole;
}

export function WorkspaceTab({ workspaceId, userRole }: WorkspaceTabProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const canEdit = userRole === "owner" || userRole === "admin";

  useEffect(() => {
    if (!workspaceId) {
      setIsLoading(false);
      return;
    }
    workspacesApi.get(workspaceId)
      .then((res) => {
        setWorkspace(res.data);
      })
      .catch(() => {
        toast({
          title: "Erreur",
          description: "Impossible de charger l'espace de travail",
          variant: "destructive"
        });
      })
      .finally(() => setIsLoading(false));
  }, [workspaceId]);

  const handleSave = async () => {
    if (!workspace || !workspaceId) return;

    setIsSaving(true);
    try {
      await workspacesApi.update(workspaceId, {
        name: workspace.name,
        logo_url: workspace.logo_url || undefined
      });
      toast({ title: "Espace de travail mis a jour" });
    } catch (error: any) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de mettre a jour",
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-48" />
          <Skeleton className="h-4 w-96" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!workspace) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Espace de travail</CardTitle>
          <CardDescription>Aucun espace de travail selectionne</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="w-5 h-5" />
            Espace de travail
          </CardTitle>
          <CardDescription>
            Gerez les informations de votre espace de travail
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="workspaceName">Nom de l&apos;espace</Label>
            <Input
              id="workspaceName"
              value={workspace.name}
              onChange={(e) => setWorkspace({ ...workspace, name: e.target.value })}
              placeholder="Mon Espace"
              disabled={!canEdit}
              className={!canEdit ? "bg-muted" : ""}
            />
            {!canEdit && (
              <p className="text-xs text-muted-foreground">
                Seuls les proprietaires et administrateurs peuvent modifier ce champ
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="workspaceSlug">Slug (identifiant unique)</Label>
            <Input
              id="workspaceSlug"
              value={workspace.slug}
              disabled
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              Le slug ne peut pas etre modifie
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="logoUrl">URL du logo (optionnel)</Label>
            <Input
              id="logoUrl"
              type="url"
              value={workspace.logo_url || ""}
              onChange={(e) => setWorkspace({ ...workspace, logo_url: e.target.value })}
              placeholder="https://example.com/logo.png"
              disabled={!canEdit}
              className={!canEdit ? "bg-muted" : ""}
            />
          </div>

          {workspace.logo_url && (
            <div className="space-y-2">
              <Label>Apercu du logo</Label>
              <div className="flex items-center gap-4">
                <img
                  src={workspace.logo_url}
                  alt={workspace.name}
                  className="w-16 h-16 rounded object-cover border-2"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            </div>
          )}

          <Separator />

          <div className="space-y-2">
            <Label>Plan de facturation</Label>
            <div>
              <Badge variant="outline" className="text-base px-3 py-1">
                {workspace.billing_plan}
              </Badge>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Fuseau horaire</Label>
            <Input
              value={workspace.timezone}
              disabled
              className="bg-muted"
            />
          </div>

          <div className="space-y-2">
            <Label>Langue par defaut</Label>
            <Input
              value={workspace.default_language}
              disabled
              className="bg-muted"
            />
          </div>

          <Separator />

          {canEdit && (
            <div className="flex justify-end">
              <Button
                onClick={handleSave}
                disabled={isSaving}
                className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Enregistrement...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Enregistrer
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
