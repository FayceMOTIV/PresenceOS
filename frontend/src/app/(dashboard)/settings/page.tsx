"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Settings as SettingsIcon,
  User as UserIcon,
  Palette,
  Link2,
  Instagram,
  Linkedin,
  Facebook,
  RefreshCw,
  Trash2,
  ExternalLink,
  Save,
  Loader2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { toast } from "@/hooks/use-toast";
import { authApi, brandsApi, connectorsApi } from "@/lib/api";
import { Brand, BrandVoice, User, SocialConnector, BrandType } from "@/types";
import { cn } from "@/lib/utils";
import Link from "next/link";

const brandTypeOptions: { value: BrandType; label: string }[] = [
  { value: "restaurant", label: "Restaurant" },
  { value: "saas", label: "SaaS" },
  { value: "ecommerce", label: "E-commerce" },
  { value: "service", label: "Service" },
  { value: "personal", label: "Personnel" },
  { value: "other", label: "Autre" },
];

const platformIcons: Record<string, React.ElementType> = {
  instagram: Instagram,
  linkedin: Linkedin,
  facebook: Facebook,
};

const platformColors: Record<string, string> = {
  instagram: "bg-gradient-to-br from-purple-500 to-pink-500",
  linkedin: "bg-[#0077B5]",
  facebook: "bg-[#1877F2]",
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "connected":
      return "bg-green-500";
    case "expired":
      return "bg-yellow-500";
    case "error":
      return "bg-red-500";
    default:
      return "bg-gray-500";
  }
};

const getStatusLabel = (status: string) => {
  switch (status) {
    case "connected":
      return "Connecté";
    case "expired":
      return "Expiré";
    case "error":
      return "Erreur";
    default:
      return status;
  }
};

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [brandVoice, setBrandVoice] = useState<BrandVoice | null>(null);
  const [connectors, setConnectors] = useState<SocialConnector[]>([]);
  const [activeTab, setActiveTab] = useState("profile");

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      const brandId = localStorage.getItem("brand_id");
      if (!brandId) {
        toast({
          title: "Erreur",
          description: "Aucune marque sélectionnée",
          variant: "destructive",
        });
        setIsLoading(false);
        return;
      }

      try {
        const [userRes, brandRes, voiceRes, connectorsRes] = await Promise.all([
          authApi.me(),
          brandsApi.get(brandId),
          brandsApi.getVoice(brandId),
          connectorsApi.list(brandId),
        ]);

        setUser(userRes.data);
        setBrand(brandRes.data);
        setBrandVoice(voiceRes.data);
        setConnectors(connectorsRes.data || []);
      } catch (error) {
        console.error("Error fetching settings data:", error);
        toast({
          title: "Erreur",
          description: "Impossible de charger les paramètres",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Handle brand update
  const handleSaveBrand = async () => {
    if (!brand) return;

    setIsSaving(true);
    try {
      const updateData = {
        name: brand.name,
        description: brand.description,
        website_url: brand.website_url,
        brand_type: brand.brand_type,
      };

      await brandsApi.update(brand.id, updateData);
      toast({
        title: "Succès",
        description: "Les informations de la marque ont été mises à jour",
      });
    } catch (error) {
      console.error("Error updating brand:", error);
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour la marque",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle brand voice update
  const handleSaveVoice = async () => {
    if (!brandVoice || !brand) return;

    setIsSaving(true);
    try {
      const updateData = {
        tone_formal: brandVoice.tone_formal,
        tone_playful: brandVoice.tone_playful,
        tone_bold: brandVoice.tone_bold,
        tone_emotional: brandVoice.tone_emotional,
        words_to_avoid: brandVoice.words_to_avoid,
        words_to_prefer: brandVoice.words_to_prefer,
        custom_instructions: brandVoice.custom_instructions,
      };

      await brandsApi.updateVoice(brand.id, updateData);
      toast({
        title: "Succès",
        description: "La voix de marque a été mise à jour",
      });
    } catch (error) {
      console.error("Error updating voice:", error);
      toast({
        title: "Erreur",
        description: "Impossible de mettre à jour la voix de marque",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  // Handle disconnect connector
  const handleDisconnect = async (connectorId: string) => {
    try {
      await connectorsApi.disconnect(connectorId);
      setConnectors((prev) => prev.filter((c) => c.id !== connectorId));
      toast({
        title: "Succès",
        description: "La plateforme a été déconnectée",
      });
    } catch (error) {
      console.error("Error disconnecting connector:", error);
      toast({
        title: "Erreur",
        description: "Impossible de déconnecter la plateforme",
        variant: "destructive",
      });
    }
  };

  // Handle refresh token
  const handleRefresh = async (connectorId: string) => {
    try {
      await connectorsApi.refresh(connectorId);
      const brandId = localStorage.getItem("brand_id");
      if (brandId) {
        const connectorsRes = await connectorsApi.list(brandId);
        setConnectors(connectorsRes.data || []);
      }
      toast({
        title: "Succès",
        description: "Le token a été actualisé",
      });
    } catch (error) {
      console.error("Error refreshing token:", error);
      toast({
        title: "Erreur",
        description: "Impossible d'actualiser le token",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-12 w-full" />
        <div className="space-y-4">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <SettingsIcon className="w-8 h-8" />
          Paramètres
        </h1>
        <p className="text-muted-foreground">
          Gérez votre profil, votre marque et vos connexions
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="profile" className="gap-2">
            <UserIcon className="w-4 h-4" />
            Profil
          </TabsTrigger>
          <TabsTrigger value="brand" className="gap-2">
            <SettingsIcon className="w-4 h-4" />
            Marque
          </TabsTrigger>
          <TabsTrigger value="voice" className="gap-2">
            <Palette className="w-4 h-4" />
            Voix de marque
          </TabsTrigger>
          <TabsTrigger value="platforms" className="gap-2">
            <Link2 className="w-4 h-4" />
            Plateformes
          </TabsTrigger>
        </TabsList>

        {/* Profile Tab */}
        <TabsContent value="profile" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Informations du profil</CardTitle>
              <CardDescription>
                Vos informations personnelles (lecture seule)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {user && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="fullName">Nom complet</Label>
                    <Input
                      id="fullName"
                      value={user.full_name}
                      disabled
                      className="bg-muted"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={user.email}
                      disabled
                      className="bg-muted"
                    />
                  </div>
                  {user.avatar_url && (
                    <div className="space-y-2">
                      <Label>Avatar</Label>
                      <div className="flex items-center gap-4">
                        <img
                          src={user.avatar_url}
                          alt={user.full_name}
                          className="w-16 h-16 rounded-full object-cover"
                        />
                        <span className="text-sm text-muted-foreground">
                          {user.full_name}
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="flex items-center gap-2 pt-2">
                    <Badge variant={user.is_verified ? "default" : "secondary"}>
                      {user.is_verified ? "Vérifié" : "Non vérifié"}
                    </Badge>
                    <Badge variant={user.is_active ? "default" : "destructive"}>
                      {user.is_active ? "Actif" : "Inactif"}
                    </Badge>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Brand Tab */}
        <TabsContent value="brand" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Informations de la marque</CardTitle>
              <CardDescription>
                Configurez les détails de votre marque
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {brand && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="brandName">Nom de la marque</Label>
                    <Input
                      id="brandName"
                      value={brand.name}
                      onChange={(e) =>
                        setBrand({ ...brand, name: e.target.value })
                      }
                      placeholder="Ma Super Marque"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={brand.description || ""}
                      onChange={(e) =>
                        setBrand({ ...brand, description: e.target.value })
                      }
                      placeholder="Description de votre marque..."
                      rows={4}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="websiteUrl">Site web</Label>
                    <Input
                      id="websiteUrl"
                      type="url"
                      value={brand.website_url || ""}
                      onChange={(e) =>
                        setBrand({ ...brand, website_url: e.target.value })
                      }
                      placeholder="https://example.com"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="brandType">Type de marque</Label>
                    <Select
                      value={brand.brand_type}
                      onValueChange={(value: BrandType) =>
                        setBrand({ ...brand, brand_type: value })
                      }
                    >
                      <SelectTrigger id="brandType">
                        <SelectValue placeholder="Sélectionnez un type" />
                      </SelectTrigger>
                      <SelectContent>
                        {brandTypeOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Separator />
                  <div className="flex justify-end">
                    <Button onClick={handleSaveBrand} disabled={isSaving}>
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
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Voice Tab */}
        <TabsContent value="voice" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Voix de marque</CardTitle>
              <CardDescription>
                Configurez le ton et le style de votre contenu
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {brandVoice && (
                <>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Formel</Label>
                        <span className="text-sm text-muted-foreground">
                          {brandVoice.tone_formal}/10
                        </span>
                      </div>
                      <Slider
                        value={[brandVoice.tone_formal]}
                        onValueChange={([value]) =>
                          setBrandVoice({ ...brandVoice, tone_formal: value })
                        }
                        min={0}
                        max={10}
                        step={1}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Ludique</Label>
                        <span className="text-sm text-muted-foreground">
                          {brandVoice.tone_playful}/10
                        </span>
                      </div>
                      <Slider
                        value={[brandVoice.tone_playful]}
                        onValueChange={([value]) =>
                          setBrandVoice({ ...brandVoice, tone_playful: value })
                        }
                        min={0}
                        max={10}
                        step={1}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Audacieux</Label>
                        <span className="text-sm text-muted-foreground">
                          {brandVoice.tone_bold}/10
                        </span>
                      </div>
                      <Slider
                        value={[brandVoice.tone_bold]}
                        onValueChange={([value]) =>
                          setBrandVoice({ ...brandVoice, tone_bold: value })
                        }
                        min={0}
                        max={10}
                        step={1}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Émotionnel</Label>
                        <span className="text-sm text-muted-foreground">
                          {brandVoice.tone_emotional}/10
                        </span>
                      </div>
                      <Slider
                        value={[brandVoice.tone_emotional]}
                        onValueChange={([value]) =>
                          setBrandVoice({ ...brandVoice, tone_emotional: value })
                        }
                        min={0}
                        max={10}
                        step={1}
                      />
                    </div>
                  </div>

                  <Separator />

                  <div className="space-y-2">
                    <Label htmlFor="wordsToAvoid">
                      Mots à éviter (séparés par des virgules)
                    </Label>
                    <Input
                      id="wordsToAvoid"
                      value={brandVoice.words_to_avoid?.join(", ") || ""}
                      onChange={(e) =>
                        setBrandVoice({
                          ...brandVoice,
                          words_to_avoid: e.target.value
                            .split(",")
                            .map((w) => w.trim())
                            .filter(Boolean),
                        })
                      }
                      placeholder="exemple, test, etc"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="wordsToPrefer">
                      Mots à privilégier (séparés par des virgules)
                    </Label>
                    <Input
                      id="wordsToPrefer"
                      value={brandVoice.words_to_prefer?.join(", ") || ""}
                      onChange={(e) =>
                        setBrandVoice({
                          ...brandVoice,
                          words_to_prefer: e.target.value
                            .split(",")
                            .map((w) => w.trim())
                            .filter(Boolean),
                        })
                      }
                      placeholder="qualité, innovation, etc"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="customInstructions">
                      Instructions personnalisées
                    </Label>
                    <Textarea
                      id="customInstructions"
                      value={brandVoice.custom_instructions || ""}
                      onChange={(e) =>
                        setBrandVoice({
                          ...brandVoice,
                          custom_instructions: e.target.value,
                        })
                      }
                      placeholder="Ajoutez des instructions spécifiques pour guider la génération de contenu..."
                      rows={4}
                    />
                  </div>

                  <Separator />

                  <div className="flex justify-end">
                    <Button onClick={handleSaveVoice} disabled={isSaving}>
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
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Platforms Tab */}
        <TabsContent value="platforms" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Plateformes connectées</CardTitle>
              <CardDescription>
                Gérez vos connexions aux réseaux sociaux
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {connectors.length > 0 ? (
                <div className="space-y-3">
                  {connectors.map((connector) => {
                    const PlatformIcon =
                      platformIcons[connector.platform] || Link2;
                    const platformColor =
                      platformColors[connector.platform] || "bg-gray-500";

                    return (
                      <motion.div
                        key={connector.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="flex items-center justify-between p-4 rounded-lg border bg-card"
                      >
                        <div className="flex items-center gap-4">
                          <div
                            className={cn(
                              "w-12 h-12 rounded-lg flex items-center justify-center",
                              platformColor
                            )}
                          >
                            <PlatformIcon className="w-6 h-6 text-white" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium capitalize">
                                {connector.platform}
                              </p>
                              <Badge
                                variant="secondary"
                                className={cn(
                                  "text-white",
                                  getStatusColor(connector.status)
                                )}
                              >
                                {getStatusLabel(connector.status)}
                              </Badge>
                            </div>
                            {connector.account_username && (
                              <p className="text-sm text-muted-foreground">
                                @{connector.account_username}
                              </p>
                            )}
                            {connector.account_name && (
                              <p className="text-xs text-muted-foreground">
                                {connector.account_name}
                              </p>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {connector.status === "expired" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRefresh(connector.id)}
                            >
                              <RefreshCw className="w-4 h-4 mr-2" />
                              Actualiser
                            </Button>
                          )}
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button size="sm" variant="destructive">
                                <Trash2 className="w-4 h-4 mr-2" />
                                Déconnecter
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>
                                  Êtes-vous sûr ?
                                </AlertDialogTitle>
                                <AlertDialogDescription>
                                  Cette action va déconnecter votre compte{" "}
                                  {connector.platform}. Vous devrez vous
                                  reconnecter pour publier du contenu sur cette
                                  plateforme.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Annuler</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDisconnect(connector.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Déconnecter
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-16 h-16 rounded-2xl bg-muted mx-auto mb-4 flex items-center justify-center">
                    <Link2 className="w-8 h-8 text-muted-foreground" />
                  </div>
                  <h3 className="font-semibold mb-2">
                    Aucune plateforme connectée
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Connectez vos réseaux sociaux pour commencer à publier du
                    contenu
                  </p>
                </div>
              )}

              <Separator />

              <div className="flex justify-center">
                <Link href="/onboarding">
                  <Button variant="outline" className="gap-2">
                    <Link2 className="w-4 h-4" />
                    Connecter une plateforme
                    <ExternalLink className="w-4 h-4" />
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
