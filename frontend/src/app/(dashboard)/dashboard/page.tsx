"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  BarChart3,
  TrendingUp,
  Users,
  Eye,
  Heart,
  MessageSquare,
  Calendar,
  Sparkles,
  ArrowRight,
  Plus,
  Bot,
  Zap,
} from "lucide-react";
import Link from "next/link";
import { metricsApi, ideasApi, postsApi } from "@/lib/api";
import { DashboardMetrics, ContentIdea, ScheduledPost } from "@/types";
import { formatNumber, formatRelativeTime, getPlatformColor } from "@/lib/utils";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [dailyIdeas, setDailyIdeas] = useState<ContentIdea[]>([]);
  const [upcomingPosts, setUpcomingPosts] = useState<ScheduledPost[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    Promise.all([
      metricsApi.getDashboard(brandId, 30),
      ideasApi.getDaily(brandId),
      postsApi.list(brandId, { status: "scheduled", limit: 5 }),
    ])
      .then(([metricsRes, ideasRes, postsRes]) => {
        setMetrics(metricsRes.data);
        setDailyIdeas(ideasRes.data);
        setUpcomingPosts(postsRes.data);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const kpiCards = [
    {
      title: "Posts publiés",
      value: metrics?.total_posts_published || 0,
      icon: BarChart3,
      color: "from-blue-500 to-cyan-500",
    },
    {
      title: "Impressions",
      value: formatNumber(metrics?.total_impressions || 0),
      icon: Eye,
      color: "from-purple-500 to-pink-500",
    },
    {
      title: "Engagement",
      value: formatNumber(metrics?.total_engagement || 0),
      icon: Heart,
      color: "from-orange-500 to-red-500",
    },
    {
      title: "Taux d'engagement",
      value: `${(metrics?.average_engagement_rate || 0).toFixed(1)}%`,
      icon: TrendingUp,
      color: "from-green-500 to-emerald-500",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Vue d&apos;ensemble de vos performances
          </p>
        </div>
        <Link href="/studio">
          <Button variant="gradient">
            <Plus className="w-4 h-4 mr-2" />
            Créer du contenu
          </Button>
        </Link>
      </div>

      {/* Agent Activity Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Card className="glass-card border-primary/20 bg-gradient-to-r from-primary/5 to-purple-500/5">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Bot className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold">Agents IA</h3>
                <p className="text-sm text-muted-foreground">
                  Generez du contenu avec votre equipe IA autonome
                </p>
              </div>
            </div>
            <Link href="/agents">
              <Button variant="outline" size="sm">
                Lancer un workflow
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* Autopilot Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <Card className="glass-card border-green-500/20 bg-gradient-to-r from-green-500/5 to-emerald-500/5">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center">
                <Zap className="w-6 h-6 text-green-500" />
              </div>
              <div>
                <h3 className="font-semibold">Mode Autopilote</h3>
                <p className="text-sm text-muted-foreground">
                  Generation automatique + approbation WhatsApp
                </p>
              </div>
            </div>
            <Link href="/autopilot">
              <Button variant="outline" size="sm" className="border-green-500/30 hover:bg-green-500/10">
                Configurer
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card, index) => (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="bento-card overflow-hidden">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{card.title}</p>
                    <p className="text-3xl font-bold mt-1">{card.value}</p>
                  </div>
                  <div
                    className={cn(
                      "w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br",
                      card.color
                    )}
                  >
                    <card.icon className="w-6 h-6 text-white" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* AI Insight */}
        {metrics?.ai_insight && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="lg:col-span-2"
          >
            <Card className="glass-card border-primary/20 bg-gradient-to-br from-primary/5 to-purple-600/5">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-primary" />
                  </div>
                  <CardTitle className="text-lg">Insight IA</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{metrics.ai_insight}</p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Daily Ideas */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className={cn(!metrics?.ai_insight && "lg:col-span-2")}
        >
          <Card className="h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Idées du jour</CardTitle>
                <CardDescription>Suggestions IA pour aujourd&apos;hui</CardDescription>
              </div>
              <Link href="/ideas">
                <Button variant="ghost" size="sm">
                  Voir tout
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {dailyIdeas.length > 0 ? (
                dailyIdeas.slice(0, 3).map((idea) => (
                  <div
                    key={idea.id}
                    className="p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors cursor-pointer"
                  >
                    <p className="font-medium text-sm">{idea.title}</p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {idea.description}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Sparkles className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Aucune idée générée aujourd&apos;hui</p>
                  <Link href="/ideas">
                    <Button variant="link" size="sm" className="mt-2">
                      Générer des idées
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Upcoming Posts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card className="h-full">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Posts à venir</CardTitle>
                <CardDescription>Prochaines publications</CardDescription>
              </div>
              <Link href="/planner">
                <Button variant="ghost" size="sm">
                  Calendrier
                  <Calendar className="w-4 h-4 ml-1" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {upcomingPosts.length > 0 ? (
                upcomingPosts.map((post) => (
                  <div
                    key={post.id}
                    className="flex items-center gap-3 p-3 rounded-lg bg-muted/50"
                  >
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full",
                        post.status === "scheduled" ? "bg-yellow-500" : "bg-green-500"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {post.content_snapshot.caption.slice(0, 50)}...
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatRelativeTime(post.scheduled_at)}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Aucun post programmé</p>
                  <Link href="/studio">
                    <Button variant="link" size="sm" className="mt-2">
                      Créer un post
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Nouveau post", href: "/studio", icon: Plus },
          { label: "Voir le calendrier", href: "/planner", icon: Calendar },
          { label: "Générer des idées", href: "/ideas", icon: Sparkles },
          { label: "Analytics", href: "/analytics", icon: BarChart3 },
        ].map((action, index) => (
          <motion.div
            key={action.label}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 + index * 0.05 }}
          >
            <Link href={action.href}>
              <Card className="bento-card hover:border-primary/50 cursor-pointer">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center">
                    <action.icon className="w-5 h-5" />
                  </div>
                  <span className="font-medium text-sm">{action.label}</span>
                </CardContent>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
