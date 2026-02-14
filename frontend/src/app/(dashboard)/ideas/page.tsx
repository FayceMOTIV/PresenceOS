"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Plus, Sparkles, Lightbulb } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ideasApi } from "@/lib/api";
import { ContentIdea, IdeaStatus } from "@/types";
import { toast } from "@/hooks/use-toast";
import { fireConfetti } from "@/lib/confetti";

import { IdeasTable } from "./components/ideas-table";
import { GenerateIdeasDialog, IdeasTableSkeleton } from "./components/generate-ideas-dialog";
import { EditIdeaDialog } from "./components/edit-idea-dialog";
import { SkeletonIdea } from '@/components/loading/skeleton-idea';

const statusTabs: { value: IdeaStatus | "all"; label: string }[] = [
  { value: "all", label: "Toutes" },
  { value: "new", label: "Nouvelles" },
  { value: "approved", label: "Approuvées" },
  { value: "in_progress", label: "En cours" },
  { value: "drafted", label: "Rédigées" },
  { value: "rejected", label: "Rejetées" },
];

export default function IdeasPage() {
  const router = useRouter();
  const [ideas, setIdeas] = useState<ContentIdea[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<IdeaStatus | "all">("all");

  // Dialog states
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedIdea, setSelectedIdea] = useState<ContentIdea | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatingCount, setGeneratingCount] = useState(0);

  // Fetch ideas
  const fetchIdeas = useCallback(async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsLoading(true);
    try {
      const params = activeTab !== "all" ? { status: activeTab } : undefined;
      const response = await ideasApi.list(brandId, params);
      setIdeas(response.data || []);
    } catch (error) {
      console.error("Error fetching ideas:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les idées",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    fetchIdeas();
  }, [fetchIdeas]);

  // Handle approve with optimistic update
  const handleApprove = useCallback(async (idea: ContentIdea) => {
    // Optimistic update
    setIdeas((prev) =>
      prev.map((i) =>
        i.id === idea.id ? { ...i, status: "approved" as IdeaStatus } : i
      )
    );

    try {
      await ideasApi.approve(idea.id);
      toast({
        title: "Idée approuvée !",
        description: `« ${idea.title} » a été approuvée`,
      });
    } catch (error) {
      // Rollback
      setIdeas((prev) =>
        prev.map((i) => (i.id === idea.id ? idea : i))
      );
      toast({
        title: "Erreur",
        description: "Impossible d'approuver l'idée",
        variant: "destructive",
      });
    }
  }, []);

  // Handle reject with optimistic update
  const handleReject = useCallback(async (idea: ContentIdea) => {
    // Optimistic update
    setIdeas((prev) =>
      prev.map((i) =>
        i.id === idea.id ? { ...i, status: "rejected" as IdeaStatus } : i
      )
    );

    try {
      await ideasApi.reject(idea.id);
      toast({
        title: "Idée rejetée",
        description: `« ${idea.title} » a été rejetée`,
      });
    } catch (error) {
      // Rollback
      setIdeas((prev) =>
        prev.map((i) => (i.id === idea.id ? idea : i))
      );
      toast({
        title: "Erreur",
        description: "Impossible de rejeter l'idée",
        variant: "destructive",
      });
    }
  }, []);

  // Handle edit
  const handleEdit = useCallback((idea: ContentIdea) => {
    setSelectedIdea(idea);
    setEditDialogOpen(true);
  }, []);

  // Handle idea updated from edit dialog
  const handleIdeaUpdated = useCallback((updatedIdea: ContentIdea) => {
    setIdeas((prev) =>
      prev.map((i) => (i.id === updatedIdea.id ? updatedIdea : i))
    );
  }, []);

  // Handle convert to draft
  const handleConvertToDraft = useCallback(
    (idea: ContentIdea) => {
      // Navigate to studio with idea context
      const params = new URLSearchParams({
        idea_id: idea.id,
        title: idea.title,
      });
      if (idea.target_platforms && idea.target_platforms.length > 0) {
        params.set("platform", idea.target_platforms[0]);
      }
      router.push(`/studio?${params.toString()}`);
    },
    [router]
  );

  // Handle ideas generated from AI
  const handleIdeasGenerated = useCallback((newIdeas: ContentIdea[]) => {
    // Add new ideas at the beginning with animation
    setIdeas((prev) => [...newIdeas, ...prev]);
    fireConfetti();
  }, []);

  // Handle bulk approve
  const handleBulkApprove = useCallback(async (ideasToApprove: ContentIdea[]) => {
    // Optimistic update
    const idsToApprove = ideasToApprove.map((i) => i.id);
    setIdeas((prev) =>
      prev.map((i) =>
        idsToApprove.includes(i.id) ? { ...i, status: "approved" as IdeaStatus } : i
      )
    );

    try {
      // Call API in parallel
      await Promise.all(ideasToApprove.map((idea) => ideasApi.approve(idea.id)));
      toast({
        title: "Idées approuvées !",
        description: `${ideasToApprove.length} idée(s) approuvée(s)`,
      });
    } catch (error) {
      // Rollback all
      setIdeas((prev) =>
        prev.map((i) => {
          const original = ideasToApprove.find((o) => o.id === i.id);
          return original ? original : i;
        })
      );
      toast({
        title: "Erreur",
        description: "Impossible d'approuver certaines idées",
        variant: "destructive",
      });
    }
  }, []);

  // Handle bulk reject
  const handleBulkReject = useCallback(async (ideasToReject: ContentIdea[]) => {
    // Optimistic update
    const idsToReject = ideasToReject.map((i) => i.id);
    setIdeas((prev) =>
      prev.map((i) =>
        idsToReject.includes(i.id) ? { ...i, status: "rejected" as IdeaStatus } : i
      )
    );

    try {
      // Call API in parallel
      await Promise.all(ideasToReject.map((idea) => ideasApi.reject(idea.id)));
      toast({
        title: "Idées rejetées",
        description: `${ideasToReject.length} idée(s) rejetée(s)`,
      });
    } catch (error) {
      // Rollback all
      setIdeas((prev) =>
        prev.map((i) => {
          const original = ideasToReject.find((o) => o.id === i.id);
          return original ? original : i;
        })
      );
      toast({
        title: "Erreur",
        description: "Impossible de rejeter certaines idées",
        variant: "destructive",
      });
    }
  }, []);

  // Filter ideas based on active tab
  const filteredIdeas =
    activeTab === "all"
      ? ideas
      : ideas.filter((idea) => idea.status === activeTab);

  // Count by status
  const countByStatus = ideas.reduce(
    (acc, idea) => {
      acc[idea.status] = (acc[idea.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Idées de posts</h1>
          <p className="text-muted-foreground">
            L&apos;IA vous propose des idées. Vous choisissez celles qui vous plaisent !
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setGenerateDialogOpen(true)}>
            <Sparkles className="w-4 h-4 mr-2" />
            Générer des idées
          </Button>
          <Button variant="gradient" onClick={() => router.push("/ideas/new")}>
            <Plus className="w-4 h-4 mr-2" />
            Nouvelle idée
          </Button>
        </div>
      </div>

      {/* Status tabs */}
      <Tabs
        value={activeTab}
        onValueChange={(value) => setActiveTab(value as IdeaStatus | "all")}
      >
        <TabsList>
          {statusTabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="gap-2">
              {tab.label}
              {tab.value !== "all" && countByStatus[tab.value] > 0 && (
                <span className="text-xs bg-muted-foreground/20 px-1.5 py-0.5 rounded-full">
                  {countByStatus[tab.value]}
                </span>
              )}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {isLoading ? (
            <div className="grid gap-4">
              {Array(5).fill(0).map((_, i) => <SkeletonIdea key={i} />)}
            </div>
          ) : filteredIdeas.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center py-20"
            >
              <div className="text-8xl mb-6">💡</div>
              <h3 className="text-2xl font-bold mb-3">Pas encore d&apos;idées</h3>
              <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
                {activeTab === "all"
                  ? "Cliquez sur « Générer des idées » et l&apos;intelligence artificielle va vous proposer 5 idées de posts pour aujourd&apos;hui !"
                  : `Aucune idée avec le statut « ${statusTabs.find((t) => t.value === activeTab)?.label} ».`}
              </p>
              {activeTab === "all" && (
                <button
                  onClick={() => setGenerateDialogOpen(true)}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
                >
                  ✨ Générer mes premières idées
                </button>
              )}
            </motion.div>
          ) : (
            <IdeasTable
              ideas={filteredIdeas}
              onApprove={handleApprove}
              onReject={handleReject}
              onEdit={handleEdit}
              onConvertToDraft={handleConvertToDraft}
              onBulkApprove={handleBulkApprove}
              onBulkReject={handleBulkReject}
            />
          )}
        </TabsContent>
      </Tabs>

      {/* Generate Ideas Dialog */}
      <GenerateIdeasDialog
        open={generateDialogOpen}
        onOpenChange={setGenerateDialogOpen}
        onIdeasGenerated={handleIdeasGenerated}
      />

      {/* Edit Idea Dialog */}
      <EditIdeaDialog
        idea={selectedIdea}
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        onIdeaUpdated={handleIdeaUpdated}
      />
    </motion.div>
  );
}
