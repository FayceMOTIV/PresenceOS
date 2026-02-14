"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Plus,
  Search,
  Star,
  Snowflake,
  Edit,
  Trash2,
  Loader2,
} from "lucide-react";
import { HelpTooltip } from "@/components/ui/help-tooltip";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

import { knowledgeApi } from "@/lib/api";
import { KnowledgeItem, KnowledgeType } from "@/types";
import { BrandInterviewChat } from "@/components/brain/BrandInterviewChat";
import { ContentAnalysisDialog } from "@/components/brain/ContentAnalysisDialog";

const knowledgeTypeLabels: Record<KnowledgeType, string> = {
  menu: "Menu",
  product: "Produit",
  offer: "Offre",
  faq: "FAQ",
  proof: "Preuve sociale",
  script: "Script",
  event: "Événement",
  process: "Process",
  team: "Equipe",
  other: "Autre",
};

const knowledgeTypeColors: Record<KnowledgeType, string> = {
  menu: "bg-orange-100/80 text-orange-700 border-orange-200/60",
  product: "bg-blue-100/80 text-blue-700 border-blue-200/60",
  offer: "bg-emerald-100/80 text-emerald-700 border-emerald-200/60",
  faq: "bg-violet-100/80 text-violet-700 border-violet-200/60",
  proof: "bg-pink-100/80 text-pink-700 border-pink-200/60",
  script: "bg-cyan-100/80 text-cyan-700 border-cyan-200/60",
  event: "bg-amber-100/80 text-amber-700 border-amber-200/60",
  process: "bg-indigo-100/80 text-indigo-700 border-indigo-200/60",
  team: "bg-rose-100/80 text-rose-700 border-rose-200/60",
  other: "bg-gray-100/80 text-gray-700 border-gray-200/60",
};

const knowledgeTypes: KnowledgeType[] = [
  "menu",
  "product",
  "offer",
  "faq",
  "proof",
  "script",
  "event",
  "process",
  "team",
  "other",
];

interface KnowledgeFormData {
  title: string;
  knowledge_type: KnowledgeType;
  category: string;
  content: string;
  is_featured: boolean;
  is_seasonal: boolean;
}

const emptyFormData: KnowledgeFormData = {
  title: "",
  knowledge_type: "other",
  category: "",
  content: "",
  is_featured: false,
  is_seasonal: false,
};

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06 }
  }
};

const cardItem = {
  hidden: { opacity: 0, y: 12, scale: 0.97 },
  show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.3, ease: "easeOut" } }
};

export default function BrainPage() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<KnowledgeType | "all">("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [categories, setCategories] = useState<string[]>([]);

  // Dialog states
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<KnowledgeFormData>(emptyFormData);
  const [isSaving, setIsSaving] = useState(false);

  // Delete confirmation
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingItem, setDeletingItem] = useState<KnowledgeItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch knowledge items
  const fetchItems = useCallback(async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsLoading(true);
    try {
      const params: any = {};
      if (typeFilter !== "all") {
        params.knowledge_type = typeFilter;
      }
      if (categoryFilter !== "all") {
        params.category = categoryFilter;
      }
      if (searchQuery) {
        params.search = searchQuery;
      }

      const response = await knowledgeApi.list(brandId, params);
      setItems(response.data || []);
    } catch (error) {
      console.error("Error fetching knowledge items:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les éléments",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [typeFilter, categoryFilter, searchQuery]);

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    try {
      const response = await knowledgeApi.getCategories(brandId);
      setCategories(response.data || []);
    } catch (error) {
      console.error("Error fetching categories:", error);
    }
  }, []);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  // Handle add
  const handleAdd = () => {
    setIsEditing(false);
    setEditingId(null);
    setFormData(emptyFormData);
    setDialogOpen(true);
  };

  // Handle edit
  const handleEdit = (item: KnowledgeItem) => {
    setIsEditing(true);
    setEditingId(item.id);
    setFormData({
      title: item.title,
      knowledge_type: item.knowledge_type,
      category: item.category || "",
      content: item.content,
      is_featured: item.is_featured,
      is_seasonal: item.is_seasonal,
    });
    setDialogOpen(true);
  };

  // Handle save
  const handleSave = async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    if (!formData.title.trim()) {
      toast({
        title: "Erreur",
        description: "Le titre est requis",
        variant: "destructive",
      });
      return;
    }

    if (!formData.content.trim()) {
      toast({
        title: "Erreur",
        description: "Le contenu est requis",
        variant: "destructive",
      });
      return;
    }

    setIsSaving(true);
    try {
      const payload = {
        title: formData.title.trim(),
        knowledge_type: formData.knowledge_type,
        category: formData.category.trim() || undefined,
        content: formData.content.trim(),
        is_featured: formData.is_featured,
        is_seasonal: formData.is_seasonal,
        is_active: true,
      };

      if (isEditing && editingId) {
        const response = await knowledgeApi.update(editingId, payload);
        setItems((prev) =>
          prev.map((item) => (item.id === editingId ? response.data : item))
        );
        toast({
          title: "Élément modifié",
          description: "L'élément a été modifié avec succès",
        });
      } else {
        const response = await knowledgeApi.create(brandId, payload);
        setItems((prev) => [response.data, ...prev]);
        toast({
          title: "Élément ajouté",
          description: "L'élément a été ajouté avec succès",
        });
        // Refresh categories in case a new one was added
        fetchCategories();
      }

      setDialogOpen(false);
      setFormData(emptyFormData);
    } catch (error) {
      console.error("Error saving knowledge item:", error);
      toast({
        title: "Erreur",
        description: "Impossible de sauvegarder l'élément",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle delete
  const handleDeleteClick = (item: KnowledgeItem) => {
    setDeletingItem(item);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingItem) return;

    setIsDeleting(true);
    try {
      await knowledgeApi.delete(deletingItem.id);
      setItems((prev) => prev.filter((item) => item.id !== deletingItem.id));
      toast({
        title: "Élément supprimé",
        description: "L'élément a été supprimé avec succès",
      });
      setDeleteDialogOpen(false);
      setDeletingItem(null);
    } catch (error) {
      console.error("Error deleting knowledge item:", error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer l'élément",
        variant: "destructive",
      });
    } finally {
      setIsDeleting(false);
    }
  };

  // Filter items based on search
  const filteredItems = items.filter((item) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        item.title.toLowerCase().includes(query) ||
        item.content.toLowerCase().includes(query) ||
        item.category?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  // Truncate content for preview
  const truncateContent = (content: string, maxLength: number = 150) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + "...";
  };

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
          <h1 className="text-3xl font-bold tracking-tight">Analyser Instagram <HelpTooltip content="L'ordinateur regarde vos anciens posts pour apprendre votre style d'écriture" /></h1>
          <p className="text-muted-foreground mt-1">
            Informations sur votre marque
          </p>
        </div>
        <Button onClick={handleAdd} variant="gradient" className="group">
          <Plus className="w-4 h-4 mr-2 group-hover:rotate-90 transition-transform duration-300" />
          Ajouter
        </Button>
      </div>

      {/* Brand Interview AI */}
      <BrandInterviewChat onKnowledgeUpdated={fetchItems} />

      {/* Content Analysis (Instagram tone extraction) */}
      <ContentAnalysisDialog onKnowledgeUpdated={fetchItems} />

      {/* Filter bar */}
      <Card className="border-gray-200/60">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/60" />
              <Input
                placeholder="Rechercher..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>

            {/* Type filter */}
            <Select
              value={typeFilter}
              onValueChange={(value) =>
                setTypeFilter(value as KnowledgeType | "all")
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tous les types</SelectItem>
                {knowledgeTypes.map((type) => (
                  <SelectItem key={type} value={type}>
                    {knowledgeTypeLabels[type]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Category filter */}
            <Select
              value={categoryFilter}
              onValueChange={(value) => setCategoryFilter(value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Catégorie" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Toutes les catégories</SelectItem>
                {categories.map((category) => (
                  <SelectItem key={category} value={category}>
                    {category}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Content */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="overflow-hidden">
              <CardHeader>
                <Skeleton className="h-5 w-20 rounded-lg" />
                <Skeleton className="h-6 w-full mt-2 rounded-lg" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-full rounded-lg" />
                <Skeleton className="h-4 w-full mt-2 rounded-lg" />
                <Skeleton className="h-4 w-2/3 mt-2 rounded-lg" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredItems.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16"
        >
          <div className="w-16 h-16 rounded-2xl bg-violet-50 mx-auto mb-4 flex items-center justify-center">
            <Brain className="w-8 h-8 text-violet-400" />
          </div>
          <h3 className="font-semibold mb-2 text-lg">Aucun élément dans votre base</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
            Ajoutez des informations sur vos produits, menus, offres et plus
            encore pour enrichir votre base de connaissances.
          </p>
          <Button onClick={handleAdd} variant="gradient" className="group">
            <Plus className="w-4 h-4 mr-2 group-hover:rotate-90 transition-transform duration-300" />
            Ajouter un élément
          </Button>
        </motion.div>
      ) : (
        <motion.div
          variants={container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <AnimatePresence mode="popLayout">
            {filteredItems.map((item) => (
              <motion.div
                key={item.id}
                variants={cardItem}
                exit={{ opacity: 0, scale: 0.95 }}
              >
                <Card className="group card-interactive overflow-hidden">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2.5">
                          <Badge
                            variant="secondary"
                            className={cn(
                              "text-xs font-medium rounded-lg border",
                              knowledgeTypeColors[item.knowledge_type]
                            )}
                          >
                            {knowledgeTypeLabels[item.knowledge_type]}
                          </Badge>
                          {item.is_featured && (
                            <Star className="w-4 h-4 text-amber-500 fill-amber-500" />
                          )}
                          {item.is_seasonal && (
                            <Snowflake className="w-4 h-4 text-blue-500" />
                          )}
                        </div>
                        <CardTitle className="text-base font-semibold truncate">
                          {item.title}
                        </CardTitle>
                        {item.category && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {item.category}
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all duration-200">
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 rounded-lg hover:bg-violet-50"
                          onClick={() => handleEdit(item)}
                        >
                          <Edit className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 rounded-lg text-destructive hover:text-destructive hover:bg-red-50"
                          onClick={() => handleDeleteClick(item)}
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {truncateContent(item.content)}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {isEditing ? "Modifier l'élément" : "Ajouter un élément"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">Titre *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
                placeholder="Ex: Menu du déjeuner"
              />
            </div>

            {/* Type */}
            <div className="space-y-2">
              <Label htmlFor="type">Type *</Label>
              <Select
                value={formData.knowledge_type}
                onValueChange={(value) =>
                  setFormData({
                    ...formData,
                    knowledge_type: value as KnowledgeType,
                  })
                }
              >
                <SelectTrigger id="type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {knowledgeTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {knowledgeTypeLabels[type]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category">Catégorie</Label>
              <Input
                id="category"
                value={formData.category}
                onChange={(e) =>
                  setFormData({ ...formData, category: e.target.value })
                }
                placeholder="Ex: Plats principaux"
              />
            </div>

            {/* Content */}
            <div className="space-y-2">
              <Label htmlFor="content">Contenu *</Label>
              <Textarea
                id="content"
                value={formData.content}
                onChange={(e) =>
                  setFormData({ ...formData, content: e.target.value })
                }
                placeholder="Décrivez l'élément en détail..."
                rows={6}
                className="resize-none"
              />
            </div>

            {/* Checkboxes */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="featured"
                  checked={formData.is_featured}
                  onCheckedChange={(checked) =>
                    setFormData({
                      ...formData,
                      is_featured: checked as boolean,
                    })
                  }
                />
                <Label
                  htmlFor="featured"
                  className="text-sm font-normal cursor-pointer"
                >
                  Mettre en avant (élément prioritaire)
                </Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="seasonal"
                  checked={formData.is_seasonal}
                  onCheckedChange={(checked) =>
                    setFormData({
                      ...formData,
                      is_seasonal: checked as boolean,
                    })
                  }
                />
                <Label
                  htmlFor="seasonal"
                  className="text-sm font-normal cursor-pointer"
                >
                  Élément saisonnier
                </Label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDialogOpen(false)}
              disabled={isSaving}
            >
              Annuler
            </Button>
            <Button onClick={handleSave} disabled={isSaving} variant="gradient">
              {isSaving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {isEditing ? "Modifier" : "Ajouter"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirmer la suppression</AlertDialogTitle>
            <AlertDialogDescription>
              Êtes-vous sûr de vouloir supprimer &quot;{deletingItem?.title}&quot; ? Cette
              action est irréversible.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>
              Annuler
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </motion.div>
  );
}
