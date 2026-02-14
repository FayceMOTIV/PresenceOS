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
import { SkeletonDashboard } from '@/components/loading/skeleton-dashboard';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 }
  }
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" } }
};

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
      gradient: "from-blue-500 to-cyan-400",
      bg: "from-blue-50 to-cyan-50/50",
      iconBg: "bg-blue-500/10",
      iconColor: "text-blue-600",
    },
    {
      title: "Vues",
      value: formatNumber(metrics?.total_impressions || 0),
      icon: Eye,
      gradient: "from-violet-500 to-purple-400",
      bg: "from-violet-50 to-purple-50/50",
      iconBg: "bg-violet-500/10",
      iconColor: "text-violet-600",
    },
    {
      title: "Interactions",
      value: formatNumber(metrics?.total_engagement || 0),
      icon: Heart,
      gradient: "from-rose-500 to-pink-400",
      bg: "from-rose-50 to-pink-50/50",
      iconBg: "bg-rose-500/10",
      iconColor: "text-rose-600",
    },
    {
      title: "Taux d'interaction",
      value: `${(metrics?.average_engagement_rate || 0).toFixed(1)}%`,
      icon: TrendingUp,
      gradient: "from-emerald-500 to-green-400",
      bg: "from-emerald-50 to-green-50/50",
      iconBg: "bg-emerald-500/10",
      iconColor: "text-emerald-600",
    },
  ];

  if (isLoading) {
    return <SkeletonDashboard />;
  }

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="space-y-8"
    >
      {/* Header */}
      <motion.div variants={item} className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Accueil</h1>
          <p className="text-muted-foreground mt-1">
            Vue d&apos;ensemble de vos performances
          </p>
        </div>
        <Link href="/studio">
          <Button variant="gradient" className="group">
            <Plus className="w-4 h-4 mr-2" />
            Créer du contenu
            <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
          </Button>
        </Link>
      </motion.div>

      {/* Agent Activity Card */}
      <motion.div variants={item}>
        <Card className="overflow-hidden border-violet-200/40 bg-gradient-to-r from-violet-50/80 via-purple-50/40 to-fuchsia-50/30">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-violet-500/10 flex items-center justify-center">
                <Bot className="w-6 h-6 text-violet-600" />
              </div>
              <div>
                <h3 className="font-semibold">Agents IA</h3>
                <p className="text-sm text-muted-foreground">
                  Générez du contenu avec votre équipe IA autonome
                </p>
              </div>
            </div>
            <Link href="/agents">
              <Button variant="outline" size="sm" className="group border-violet-200/60 hover:bg-violet-50 hover:border-violet-300/60">
                Démarrer
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* Autopilot Card */}
      <motion.div variants={item}>
        <Card className="overflow-hidden border-emerald-200/40 bg-gradient-to-r from-emerald-50/80 via-green-50/40 to-teal-50/30">
          <CardContent className="flex items-center justify-between p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
                <Zap className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold">Pilote automatique</h3>
                <p className="text-sm text-muted-foreground">
                  Création automatique + approbation WhatsApp
                </p>
              </div>
            </div>
            <Link href="/autopilot">
              <Button variant="outline" size="sm" className="group border-emerald-200/60 hover:bg-emerald-50 hover:border-emerald-300/60 text-emerald-700">
                Configurer
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </motion.div>

      {/* KPI Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiCards.map((card, index) => (
          <motion.div
            key={card.title}
            variants={item}
          >
            <Card className={cn("bento-card overflow-hidden border-transparent bg-gradient-to-br", card.bg)}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{card.title}</p>
                    <p className="text-3xl font-bold mt-2 tracking-tight">{card.value}</p>
                  </div>
                  <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center", card.iconBg)}>
                    <card.icon className={cn("w-6 h-6", card.iconColor)} />
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
            variants={item}
            className="lg:col-span-2"
          >
            <Card className="border-violet-200/40 bg-gradient-to-br from-violet-50/60 to-purple-50/30 overflow-hidden">
              <CardHeader>
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-violet-500/10 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-violet-600" />
                  </div>
                  <CardTitle className="text-lg">Conseil IA</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground leading-relaxed">{metrics.ai_insight}</p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Daily Ideas */}
        <motion.div
          variants={item}
          className={cn(!metrics?.ai_insight && "lg:col-span-2")}
        >
          <Card className="h-full card-interactive">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Idées du jour</CardTitle>
                <CardDescription>Suggestions IA pour aujourd&apos;hui</CardDescription>
              </div>
              <Link href="/ideas">
                <Button variant="ghost" size="sm" className="group text-violet-600 hover:text-violet-700 hover:bg-violet-50">
                  Voir tout
                  <ArrowRight className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent className="space-y-3">
              {dailyIdeas.length > 0 ? (
                dailyIdeas.slice(0, 3).map((idea) => (
                  <div
                    key={idea.id}
                    className="p-3 rounded-xl bg-gradient-to-r from-gray-50/80 to-transparent hover:from-violet-50/50 hover:to-transparent transition-colors cursor-pointer border border-transparent hover:border-violet-100"
                  >
                    <p className="font-medium text-sm">{idea.title}</p>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {idea.description}
                    </p>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <div className="w-12 h-12 rounded-2xl bg-violet-50 mx-auto mb-3 flex items-center justify-center">
                    <Sparkles className="w-6 h-6 text-violet-400" />
                  </div>
                  <p className="text-sm">Aucune idée générée aujourd&apos;hui</p>
                  <Link href="/ideas">
                    <Button variant="link" size="sm" className="mt-2 text-violet-600">
                      Générer des idées
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Upcoming Posts */}
        <motion.div variants={item}>
          <Card className="h-full card-interactive">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Posts à venir</CardTitle>
                <CardDescription>Prochaines publications</CardDescription>
              </div>
              <Link href="/planner">
                <Button variant="ghost" size="sm" className="group text-violet-600 hover:text-violet-700 hover:bg-violet-50">
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
                    className="flex items-center gap-3 p-3 rounded-xl bg-gradient-to-r from-gray-50/80 to-transparent"
                  >
                    <div
                      className={cn(
                        "w-2.5 h-2.5 rounded-full ring-2 ring-offset-2",
                        post.status === "scheduled"
                          ? "bg-amber-400 ring-amber-200"
                          : "bg-emerald-400 ring-emerald-200"
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
                  <div className="w-12 h-12 rounded-2xl bg-gray-50 mx-auto mb-3 flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-gray-400" />
                  </div>
                  <p className="text-sm">Aucun post programmé</p>
                  <Link href="/studio">
                    <Button variant="link" size="sm" className="mt-2 text-violet-600">
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
      <motion.div variants={item}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Nouveau post", href: "/studio", icon: Plus, color: "text-violet-600", bg: "bg-violet-50" },
            { label: "Voir le calendrier", href: "/planner", icon: Calendar, color: "text-blue-600", bg: "bg-blue-50" },
            { label: "Générer des idées", href: "/ideas", icon: Sparkles, color: "text-fuchsia-600", bg: "bg-fuchsia-50" },
            { label: "Statistiques", href: "/analytics", icon: BarChart3, color: "text-emerald-600", bg: "bg-emerald-50" },
          ].map((action) => (
            <Link key={action.label} href={action.href}>
              <Card className="bento-card hover:border-violet-200/60 cursor-pointer group">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110", action.bg)}>
                    <action.icon className={cn("w-5 h-5", action.color)} />
                  </div>
                  <span className="font-medium text-sm">{action.label}</span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
