"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  BarChart3,
  TrendingUp,
  Eye,
  Heart,
  Users,
  Sparkles,
  CheckCircle,
  ArrowUpRight,
  Target,
} from "lucide-react";
import { metricsApi } from "@/lib/api";
import { DashboardMetrics, PlatformBreakdown } from "@/types";
import { formatNumber, cn } from "@/lib/utils";

// Dynamically import chart components with no SSR
const PlatformChart = dynamic(
  () => import("./components/PlatformChart"),
  { ssr: false, loading: () => <Skeleton className="h-[300px] w-full" /> }
);

const ContentMixChart = dynamic(
  () => import("./components/ContentMixChart"),
  { ssr: false, loading: () => <Skeleton className="h-[300px] w-full" /> }
);

interface TopPost {
  id: string;
  caption: string;
  platform: string;
  impressions: number;
  likes: number;
  comments: number;
  engagement_rate: number;
  published_at: string;
}

interface LearningData {
  summary: string;
  what_works: string[];
  recommendations: string[];
  content_mix_suggestion: {
    education: number;
    entertainment: number;
    engagement: number;
    promotion: number;
    behind_scenes: number;
  };
}

const PLATFORM_COLORS = ["#8b5cf6", "#06b6d4", "#f97316", "#10b981", "#f43f5e"];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<number>(30);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [platforms, setPlatforms] = useState<PlatformBreakdown[]>([]);
  const [topPosts, setTopPosts] = useState<TopPost[]>([]);
  const [learning, setLearning] = useState<LearningData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsLoading(true);
    Promise.all([
      metricsApi.getDashboard(brandId, period),
      metricsApi.getPlatforms(brandId, period),
      metricsApi.getTopPosts(brandId, { metric: "engagement_rate", limit: 5 }),
      metricsApi.getLearning(brandId),
    ])
      .then(([metricsRes, platformsRes, topPostsRes, learningRes]) => {
        setMetrics(metricsRes.data);
        setPlatforms(platformsRes.data);
        setTopPosts(topPostsRes.data.posts || []);
        setLearning(learningRes.data);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [period]);

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
      title: "Engagement total",
      value: formatNumber(metrics?.total_engagement || 0),
      icon: Heart,
      color: "from-orange-500 to-red-500",
    },
    {
      title: "Taux d'engagement moyen",
      value: `${(metrics?.average_engagement_rate || 0).toFixed(1)}%`,
      icon: TrendingUp,
      color: "from-green-500 to-emerald-500",
    },
  ];

  const platformChartData = platforms.map((p) => ({
    name: p.platform,
    impressions: p.total_impressions,
    engagement: p.total_engagement,
  }));

  const contentMixData = learning?.content_mix_suggestion
    ? [
        { name: "Éducation", value: learning.content_mix_suggestion.education },
        { name: "Divertissement", value: learning.content_mix_suggestion.entertainment },
        { name: "Engagement", value: learning.content_mix_suggestion.engagement },
        { name: "Promotion", value: learning.content_mix_suggestion.promotion },
        { name: "Coulisses", value: learning.content_mix_suggestion.behind_scenes },
      ]
    : [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Analysez vos performances et optimisez votre stratégie
          </p>
        </div>
        <Tabs value={period.toString()} onValueChange={(v) => setPeriod(parseInt(v))}>
          <TabsList>
            <TabsTrigger value="7">7j</TabsTrigger>
            <TabsTrigger value="30">30j</TabsTrigger>
            <TabsTrigger value="90">90j</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* KPI Cards */}
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
                {isLoading ? (
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-8 w-16" />
                  </div>
                ) : (
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
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Platform Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Performance par plateforme</CardTitle>
              <CardDescription>Impressions et engagement par réseau social</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <Skeleton className="h-[300px] w-full" />
              ) : platformChartData.length > 0 ? (
                <PlatformChart data={platformChartData} />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-center">
                  <div>
                    <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Aucune donnée disponible pour cette période
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Statistiques détaillées</CardTitle>
              <CardDescription>Métriques par plateforme</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : platforms.length > 0 ? (
                <div className="space-y-3">
                  {platforms.map((platform, index) => (
                    <div
                      key={platform.platform}
                      className="p-4 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: PLATFORM_COLORS[index % PLATFORM_COLORS.length] }}
                          />
                          <span className="font-semibold capitalize">{platform.platform}</span>
                          <Badge variant="secondary">{platform.posts_count} posts</Badge>
                        </div>
                        <div className="flex items-center gap-1 text-green-600">
                          <ArrowUpRight className="w-4 h-4" />
                          <span className="text-sm font-semibold">
                            {platform.average_engagement_rate.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3 mt-2">
                        <div>
                          <p className="text-xs text-muted-foreground">Impressions</p>
                          <p className="text-sm font-semibold">
                            {formatNumber(platform.total_impressions)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Engagement</p>
                          <p className="text-sm font-semibold">
                            {formatNumber(platform.total_engagement)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-center">
                  <div>
                    <Users className="w-12 h-12 mx-auto mb-3 opacity-50 text-muted-foreground" />
                    <p className="text-sm text-muted-foreground">
                      Aucune plateforme connectée
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Top Performing Posts */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>Top posts performants</CardTitle>
            <CardDescription>Vos meilleurs contenus par taux d&apos;engagement</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : topPosts.length > 0 ? (
              <div className="space-y-4">
                {topPosts.map((post, index) => (
                  <div
                    key={post.id}
                    className="p-4 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="capitalize">
                            {post.platform}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(post.published_at).toLocaleDateString("fr-FR", {
                              day: "numeric",
                              month: "short",
                              year: "numeric",
                            })}
                          </span>
                        </div>
                        <p className="text-sm line-clamp-2 mb-3">{post.caption}</p>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="flex items-center gap-1">
                            <Eye className="w-4 h-4 text-muted-foreground" />
                            <span>{formatNumber(post.impressions)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Heart className="w-4 h-4 text-muted-foreground" />
                            <span>{formatNumber(post.likes)}</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="w-4 h-4 text-muted-foreground" />
                            <span>{formatNumber(post.comments)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-1 text-green-600">
                          <TrendingUp className="w-4 h-4" />
                          <span className="text-lg font-bold">
                            {post.engagement_rate.toFixed(1)}%
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground">Engagement</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-[200px] flex items-center justify-center text-center">
                <div>
                  <TrendingUp className="w-12 h-12 mx-auto mb-3 opacity-50 text-muted-foreground" />
                  <p className="text-sm text-muted-foreground">
                    Aucun post publié pour cette période
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* AI Learning Section */}
      {learning && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card className="glass-card border-primary/20 bg-gradient-to-br from-primary/5 to-purple-600/5">
            <CardHeader>
              <div className="flex items-center gap-2">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <CardTitle>Apprentissage IA</CardTitle>
                  <CardDescription>
                    Insights et recommandations basés sur vos performances
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-20 w-full" />
                  <Skeleton className="h-32 w-full" />
                </div>
              ) : (
                <>
                  {/* Summary */}
                  {learning.summary && (
                    <div className="p-4 rounded-lg bg-background/50">
                      <p className="text-muted-foreground">{learning.summary}</p>
                    </div>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* What Works */}
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <h3 className="font-semibold">Ce qui marche</h3>
                      </div>
                      {learning.what_works && learning.what_works.length > 0 ? (
                        <ul className="space-y-2">
                          {learning.what_works.map((item, index) => (
                            <li
                              key={index}
                              className="flex items-start gap-2 text-sm text-muted-foreground"
                            >
                              <div className="w-1.5 h-1.5 rounded-full bg-green-600 mt-2 flex-shrink-0" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-muted-foreground italic">
                          Aucune donnée disponible
                        </p>
                      )}
                    </div>

                    {/* Recommendations */}
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <Target className="w-5 h-5 text-primary" />
                        <h3 className="font-semibold">Recommandations</h3>
                      </div>
                      {learning.recommendations && learning.recommendations.length > 0 ? (
                        <ul className="space-y-2">
                          {learning.recommendations.map((item, index) => (
                            <li
                              key={index}
                              className="flex items-start gap-2 text-sm text-muted-foreground"
                            >
                              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 flex-shrink-0" />
                              <span>{item}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-sm text-muted-foreground italic">
                          Aucune recommandation disponible
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Content Mix Suggestion */}
                  {contentMixData.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-4">Mix de contenu suggéré</h3>
                      <div className="flex items-center justify-center">
                        <ContentMixChart data={contentMixData} colors={PLATFORM_COLORS} />
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  );
}
