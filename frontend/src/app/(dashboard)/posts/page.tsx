"use client";

import { useState, useEffect, useCallback } from "react";
import { Plus, Calendar, LayoutGrid, List, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { toast } from "@/hooks/use-toast";

import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { postsApi, connectorsApi } from "@/lib/api";
import { ScheduledPost, SocialConnector, PostStatus } from "@/types";

import { PostsTable } from "./components/posts-table";
import { PostsFilters } from "./components/posts-filters";
import { PostPreviewDialog } from "./components/post-preview-dialog";
import { PostsMobileList } from "./components/posts-mobile-card";
import { SkeletonPost } from '@/components/loading/skeleton-post';

type ViewMode = "list" | "grid";
type StatusTab = "all" | PostStatus;

const statusTabs: { id: StatusTab; label: string }[] = [
  { id: "all", label: "Tous" },
  { id: "scheduled", label: "Programmés" },
  { id: "queued", label: "En cours" },
  { id: "published", label: "Publiés" },
  { id: "failed", label: "Échoués" },
];

export default function PostsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [posts, setPosts] = useState<ScheduledPost[]>([]);
  const [connectors, setConnectors] = useState<SocialConnector[]>([]);
  const [activeTab, setActiveTab] = useState<StatusTab>("all");
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [filters, setFilters] = useState<PostsFilters>({
    platforms: [],
    statuses: [],
    dateFrom: undefined,
    dateTo: undefined,
  });
  const [selectedPost, setSelectedPost] = useState<ScheduledPost | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);

  const brandId = typeof window !== "undefined" ? localStorage.getItem("brand_id") : null;

  const fetchPosts = useCallback(async () => {
    if (!brandId) return;

    try {
      const response = await postsApi.list(brandId);
      setPosts(response.data);
    } catch (error) {
      console.error("Failed to fetch posts:", error);
      toast({
        title: "Erreur",
        description: "Erreur lors du chargement des posts",
        variant: "destructive",
      });
    }
  }, [brandId]);

  const fetchConnectors = useCallback(async () => {
    if (!brandId) return;

    try {
      const response = await connectorsApi.list(brandId);
      setConnectors(response.data);
    } catch (error) {
      console.error("Failed to fetch connectors:", error);
    }
  }, [brandId]);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchPosts(), fetchConnectors()]);
      setLoading(false);
    };
    init();
  }, [fetchPosts, fetchConnectors]);

  // Filter posts based on active tab and filters
  const filteredPosts = posts.filter((post) => {
    // Status tab filter
    if (activeTab !== "all" && post.status !== activeTab) {
      return false;
    }

    // Platform filter
    if (filters.platforms.length > 0) {
      const connector = connectors.find((c) => c.id === post.connector_id);
      if (!connector || !filters.platforms.includes(connector.platform)) {
        return false;
      }
    }

    // Status filter
    if (filters.statuses.length > 0 && !filters.statuses.includes(post.status)) {
      return false;
    }

    // Date range filter
    const postDate = new Date(post.scheduled_at);
    if (filters.dateFrom && postDate < filters.dateFrom) {
      return false;
    }
    if (filters.dateTo) {
      const endOfDay = new Date(filters.dateTo);
      endOfDay.setHours(23, 59, 59, 999);
      if (postDate > endOfDay) {
        return false;
      }
    }

    return true;
  });

  const handleView = (post: ScheduledPost) => {
    setSelectedPost(post);
    setPreviewOpen(true);
  };

  const handleEdit = (post: ScheduledPost) => {
    // Navigate to studio with post ID for editing
    router.push(`/studio?edit=${post.id}`);
  };

  const handleDuplicate = async (post: ScheduledPost) => {
    if (!brandId) return;

    try {
      // Create a new post with the same content
      const newScheduledAt = new Date();
      newScheduledAt.setDate(newScheduledAt.getDate() + 1);
      newScheduledAt.setHours(12, 0, 0, 0);

      await postsApi.schedule(brandId, {
        connector_id: post.connector_id,
        draft_id: post.draft_id,
        scheduled_at: newScheduledAt.toISOString(),
        content_snapshot: post.content_snapshot,
      });

      toast({
        title: "Post dupliqué !",
        description: "Le post a été dupliqué avec succès",
      });
      fetchPosts();
    } catch (error) {
      console.error("Failed to duplicate post:", error);
      toast({
        title: "Erreur",
        description: "Erreur lors de la duplication",
        variant: "destructive",
      });
    }
  };

  const handleDelete = async (post: ScheduledPost) => {
    try {
      // Optimistic update
      setPosts((prev) => prev.filter((p) => p.id !== post.id));

      await postsApi.cancel(post.id);
      toast({
        title: "Post supprimé",
        description: "Le post a été supprimé",
      });
    } catch (error) {
      console.error("Failed to delete post:", error);
      toast({
        title: "Erreur",
        description: "Erreur lors de la suppression",
        variant: "destructive",
      });
      fetchPosts(); // Rollback
    }
  };

  const handlePublishNow = async (post: ScheduledPost) => {
    try {
      // Optimistic update
      setPosts((prev) =>
        prev.map((p) =>
          p.id === post.id ? { ...p, status: "queued" as PostStatus } : p
        )
      );

      await postsApi.update(post.id, {
        scheduled_at: new Date().toISOString(),
        status: "queued",
      });

      toast({
        title: "Publication lancée !",
        description: "Votre post va être publié dans quelques instants",
      });
    } catch (error) {
      console.error("Failed to publish post:", error);
      toast({
        title: "Erreur",
        description: "Erreur lors de la publication",
        variant: "destructive",
      });
      fetchPosts(); // Rollback
    }
  };

  const handleBulkDelete = async (postsToDelete: ScheduledPost[]) => {
    const ids = postsToDelete.map((p) => p.id);

    try {
      // Optimistic update
      setPosts((prev) => prev.filter((p) => !ids.includes(p.id)));

      await Promise.all(ids.map((id) => postsApi.cancel(id)));
      toast({
        title: "Posts supprimés",
        description: `${ids.length} post${ids.length > 1 ? "s" : ""} supprimé${ids.length > 1 ? "s" : ""}`,
      });
    } catch (error) {
      console.error("Failed to bulk delete posts:", error);
      toast({
        title: "Erreur",
        description: "Erreur lors de la suppression",
        variant: "destructive",
      });
      fetchPosts(); // Rollback
    }
  };

  const handleBulkPublish = async (postsToPublish: ScheduledPost[]) => {
    const ids = postsToPublish.map((p) => p.id);

    try {
      // Optimistic update
      setPosts((prev) =>
        prev.map((p) =>
          ids.includes(p.id) ? { ...p, status: "queued" as PostStatus } : p
        )
      );

      await Promise.all(
        ids.map((id) =>
          postsApi.update(id, {
            scheduled_at: new Date().toISOString(),
            status: "queued",
          })
        )
      );
      toast({
        title: "Publications lancées !",
        description: `${ids.length} post${ids.length > 1 ? "s" : ""} en cours de publication`,
      });
    } catch (error) {
      console.error("Failed to bulk publish posts:", error);
      toast({
        title: "Erreur",
        description: "Erreur lors de la publication",
        variant: "destructive",
      });
      fetchPosts(); // Rollback
    }
  };

  const selectedConnector = selectedPost
    ? connectors.find((c) => c.id === selectedPost.connector_id) || null
    : null;

  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <Skeleton className="h-8 w-48" />
              <Skeleton className="h-4 w-72" />
            </div>
            <Skeleton className="h-10 w-32" />
          </div>
          <Skeleton className="h-10 w-full max-w-md" />
          <div className="grid gap-6">
            {Array(6).fill(0).map((_, i) => <SkeletonPost key={i} />)}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Mes posts</h1>
            <p className="text-muted-foreground mt-1">
              Retrouvez tous vos posts : programmés, en cours et publiés
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => router.push("/planner")}
              className="gap-2"
            >
              <Calendar className="w-4 h-4" />
              Calendrier
            </Button>
            <Button onClick={() => router.push("/studio")} className="gap-2">
              <Plus className="w-4 h-4" />
              Nouveau post
            </Button>
          </div>
        </div>

        {/* Status Tabs */}
        <Tabs
          value={activeTab}
          onValueChange={(v) => setActiveTab(v as StatusTab)}
        >
          <div className="flex items-center justify-between">
            <TabsList>
              {statusTabs.map((tab) => (
                <TabsTrigger key={tab.id} value={tab.id}>
                  {tab.label}
                  {tab.id !== "all" && (
                    <span className="ml-1.5 text-xs text-muted-foreground">
                      ({posts.filter((p) => p.status === tab.id).length})
                    </span>
                  )}
                </TabsTrigger>
              ))}
            </TabsList>

            {/* View Mode Toggle - Desktop Only */}
            <div className="hidden md:flex items-center gap-1 bg-muted p-1 rounded-lg">
              <Button
                variant={viewMode === "list" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("list")}
                className="h-8 px-3"
              >
                <List className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "grid" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setViewMode("grid")}
                className="h-8 px-3"
              >
                <LayoutGrid className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </Tabs>

        {/* Content */}
        <AnimatePresence mode="wait">
          {filteredPosts.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-20"
            >
              <div className="text-8xl mb-6">📝</div>
              <h3 className="text-2xl font-bold mb-3">Aucun post encore</h3>
              <p className="text-lg text-gray-600 mb-8 max-w-md mx-auto">
                {activeTab === "all"
                  ? "Vous n&apos;avez pas encore créé de posts. Commencez par prendre une photo de votre meilleur plat !"
                  : `Aucun post avec le statut « ${statusTabs.find((t) => t.id === activeTab)?.label} ».`}
              </p>
              {activeTab === "all" && (
                <button
                  onClick={() => router.push("/studio")}
                  className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-medium hover:opacity-90 transition-opacity"
                >
                  ✨ Créer mon premier post
                </button>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="content"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Desktop Table View */}
              <div className="hidden md:block">
                <PostsTable
                  posts={filteredPosts}
                  connectors={connectors}
                  filters={filters}
                  onFiltersChange={setFilters}
                  onView={handleView}
                  onEdit={handleEdit}
                  onDuplicate={handleDuplicate}
                  onDelete={handleDelete}
                  onPublishNow={handlePublishNow}
                  onBulkDelete={handleBulkDelete}
                  onBulkPublish={handleBulkPublish}
                />
              </div>

              {/* Mobile Card View */}
              <div className="md:hidden">
                <PostsMobileList
                  posts={filteredPosts}
                  connectors={connectors}
                  onView={handleView}
                  onEdit={handleEdit}
                  onDuplicate={handleDuplicate}
                  onDelete={handleDelete}
                  onPublishNow={handlePublishNow}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Preview Dialog */}
        <PostPreviewDialog
          post={selectedPost}
          connector={selectedConnector}
          open={previewOpen}
          onOpenChange={setPreviewOpen}
          onEdit={handleEdit}
          onPublishNow={handlePublishNow}
        />
      </motion.div>
    </div>
  );
}
