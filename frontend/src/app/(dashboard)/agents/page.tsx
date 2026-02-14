"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Search,
  PenTool,
  Shield,
  Check,
  Edit,
  X,
  Loader2,
  Sparkles,
} from "lucide-react";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { agentsApi } from "@/lib/api";
import { useAgentTask } from "@/hooks/use-agent-task";
import type { GeneratedPost, ContentCrewResult } from "@/types/agents";
import { fireConfetti } from "@/lib/confetti";

const PLATFORM_COLORS = {
  linkedin: "#0A66C2",
  instagram: "#E4405F",
  tiktok: "#000000",
  facebook: "#1877F2",
} as const;

const agents = [
  {
    id: "veilleur",
    name: "Veilleur",
    description: "Scanne les tendances du secteur",
    icon: Search,
    status: "Prêt",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    id: "redacteur",
    name: "Rédacteur",
    description: "Rédige du contenu adapté",
    icon: PenTool,
    status: "Prêt",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    id: "critique",
    name: "Critique",
    description: "Évalue et corrige le contenu",
    icon: Shield,
    status: "Prêt",
    gradient: "from-green-500 to-emerald-500",
  },
];

const platforms = [
  { id: "linkedin", name: "LinkedIn", color: PLATFORM_COLORS.linkedin },
  { id: "instagram", name: "Instagram", color: PLATFORM_COLORS.instagram },
  { id: "tiktok", name: "TikTok", color: PLATFORM_COLORS.tiktok },
  { id: "facebook", name: "Facebook", color: PLATFORM_COLORS.facebook },
];

export default function AgentsPage() {
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([
    "linkedin",
  ]);
  const [numPosts, setNumPosts] = useState(3);
  const [topic, setTopic] = useState("");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const { task: taskData, isPolling } = useAgentTask(taskId);

  const togglePlatform = (platformId: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platformId)
        ? prev.filter((p) => p !== platformId)
        : [...prev, platformId]
    );
  };

  const handleGenerateContent = async () => {
    if (selectedPlatforms.length === 0) {
      alert("Veuillez sélectionner au moins une plateforme");
      return;
    }

    const brandId = localStorage.getItem("brand_id");
    if (!brandId) {
      alert("Brand ID non trouvé. Veuillez vous reconnecter.");
      return;
    }

    setIsGenerating(true);
    try {
      const { data: response } = await agentsApi.generateContent({
        brand_id: brandId,
        platforms: selectedPlatforms,
        num_posts: numPosts,
        topic: topic || undefined,
      });

      fireConfetti();
      setTaskId(response.task_id);
    } catch (error) {
      console.error("Erreur lors du lancement du crew:", error);
      alert("Erreur lors du lancement du crew");
      setIsGenerating(false);
    }
  };

  const handleApprove = (post: GeneratedPost) => {
    console.log("Approving post:", post);
    // TODO: Implement approval logic
  };

  const handleEdit = (post: GeneratedPost) => {
    console.log("Editing post:", post);
    // TODO: Implement edit logic
  };

  const handleReject = (post: GeneratedPost) => {
    console.log("Rejecting post:", post);
    // TODO: Implement rejection logic
  };

  const results = taskData?.status === "completed" ? (taskData.result as ContentCrewResult | null) : null;
  const taskFailed = taskData?.status === "failed";
  const isTaskRunning =
    taskData?.status === "pending" || taskData?.status === "running";

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
      },
    },
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="space-y-2"
      >
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-500 to-pink-500 bg-clip-text text-transparent">
          Mes assistants <HelpTooltip content="Des robots intelligents qui créent vos posts automatiquement pendant que vous cuisinez" />
        </h1>
        <p className="text-muted-foreground text-lg">
          Vos assistants de création
        </p>
      </motion.div>

      {/* Agent Cards */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-3 gap-6"
      >
        {agents.map((agent) => {
          const Icon = agent.icon;
          return (
            <motion.div key={agent.id} variants={itemVariants}>
              <Card className="glass-card relative overflow-hidden group hover:shadow-xl transition-shadow duration-300">
                <div
                  className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${agent.gradient}`}
                />
                <CardHeader className="space-y-4">
                  <div
                    className={`w-16 h-16 rounded-full bg-gradient-to-r ${agent.gradient} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}
                  >
                    <Icon className="w-8 h-8 text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-xl mb-2">{agent.name}</CardTitle>
                    <CardDescription className="text-sm">
                      {agent.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
                  <Badge
                    variant="outline"
                    className="bg-green-500/10 text-green-500 border-green-500/20"
                  >
                    {agent.status}
                  </Badge>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </motion.div>

      {/* Workflow Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-500" />
              Générer du contenu
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Platform Selection */}
            <div className="space-y-3">
              <label className="text-sm font-medium">Plateformes</label>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {platforms.map((platform) => (
                  <button
                    key={platform.id}
                    onClick={() => togglePlatform(platform.id)}
                    className={`p-4 rounded-lg border-2 transition-all duration-200 ${
                      selectedPlatforms.includes(platform.id)
                        ? "border-purple-500 bg-purple-500/10"
                        : "border-border bg-card hover:border-purple-500/50"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: platform.color }}
                      />
                      <span className="text-sm font-medium">
                        {platform.name}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Number of Posts */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Nombre de posts (1-10)
              </label>
              <Input
                type="number"
                min="1"
                max="10"
                value={numPosts}
                onChange={(e) =>
                  setNumPosts(
                    Math.min(10, Math.max(1, parseInt(e.target.value) || 1))
                  )
                }
                className="max-w-xs"
              />
            </div>

            {/* Optional Topic */}
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Sujet (optionnel)
              </label>
              <Textarea
                placeholder="Ex: Lancement de notre nouveau produit eco-responsable..."
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                className="min-h-[100px]"
              />
            </div>

            {/* Generate Button */}
            <Button
              onClick={handleGenerateContent}
              disabled={isGenerating || isTaskRunning}
              className="w-full md:w-auto bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              size="lg"
            >
              {isGenerating || isTaskRunning ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Crew en cours...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Démarrer la création
                </>
              )}
            </Button>

            {/* Loading Progress */}
            {isTaskRunning && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    Génération en cours...
                  </span>
                  <span className="text-purple-500 font-medium">
                    {taskData?.status === "pending" ? "En attente" : "En cours"}
                  </span>
                </div>
                <Progress value={45} className="h-2" />
              </motion.div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Error State */}
      {taskFailed && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-red-500/50 bg-red-500/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 text-red-500">
                <X className="w-5 h-5" />
                <p>
                  Erreur lors de la génération du contenu. Veuillez réessayer.
                </p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Results Section */}
      {results && results.posts && results.posts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-4"
        >
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Résultats</h2>
            <Badge variant="outline" className="text-sm">
              {results.posts.length} post(s) généré(s)
            </Badge>
          </div>

          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="grid grid-cols-1 lg:grid-cols-2 gap-6"
          >
            {results.posts.map((post: GeneratedPost, index: number) => {
              const platformColor =
                PLATFORM_COLORS[
                  post.platform as keyof typeof PLATFORM_COLORS
                ] || "#6B7280";

              return (
                <motion.div key={index} variants={itemVariants}>
                  <Card className="glass-card hover:shadow-lg transition-shadow duration-300">
                    <CardHeader>
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <Badge
                            style={{
                              backgroundColor: `${platformColor}20`,
                              color: platformColor,
                              borderColor: `${platformColor}40`,
                            }}
                            className="mb-3 capitalize"
                          >
                            {post.platform}
                          </Badge>
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">
                            {post.content}
                          </p>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Hashtags */}
                      {post.hashtags && post.hashtags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {post.hashtags.map((hashtag, idx) => (
                            <span
                              key={idx}
                              className="text-xs text-purple-500 bg-purple-500/10 px-2 py-1 rounded"
                            >
                              #{hashtag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Virality Score */}
                      {post.virality_score !== undefined && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            Chance de succès:
                          </span>
                          <Badge
                            variant="outline"
                            className={`text-xs ${
                              post.virality_score >= 8
                                ? "bg-green-500/10 text-green-500 border-green-500/20"
                                : post.virality_score >= 6
                                ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                                : "bg-red-500/10 text-red-500 border-red-500/20"
                            }`}
                          >
                            {post.virality_score}/10
                          </Badge>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex gap-2 pt-2">
                        <Button
                          onClick={() => handleApprove(post)}
                          size="sm"
                          variant="outline"
                          className="flex-1 border-green-500/50 hover:bg-green-500/10 hover:text-green-500"
                        >
                          <Check className="w-4 h-4 mr-1" />
                          Approuver
                        </Button>
                        <Button
                          onClick={() => handleEdit(post)}
                          size="sm"
                          variant="outline"
                          className="flex-1 border-blue-500/50 hover:bg-blue-500/10 hover:text-blue-500"
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Modifier
                        </Button>
                        <Button
                          onClick={() => handleReject(post)}
                          size="sm"
                          variant="outline"
                          className="flex-1 border-red-500/50 hover:bg-red-500/10 hover:text-red-500"
                        >
                          <X className="w-4 h-4 mr-1" />
                          Rejeter
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}
