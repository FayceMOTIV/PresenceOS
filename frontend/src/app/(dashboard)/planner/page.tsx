"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import { format, setHours, setMinutes } from "date-fns";
import { fr } from "date-fns/locale";
import { Loader2, Plus } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { postsApi, connectorsApi } from "@/lib/api";
import { CalendarDay, ScheduledPost, SocialConnector, Platform, PostStatus } from "@/types";
import { toast } from "@/hooks/use-toast";

import { CalendarHeader, ViewMode } from "./components/calendar-header";
import { CalendarGrid } from "./components/calendar-grid";
import { WeekView } from "./components/week-view";
import { QuickCreateDialog, QuickCreateData } from "./components/quick-create-dialog";
import { CalendarFiltersComponent, CalendarFilters } from "./components/calendar-filters";

export default function PlannerPage() {
  const router = useRouter();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState<ViewMode>("month");
  const [calendarDays, setCalendarDays] = useState<CalendarDay[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedPost, setSelectedPost] = useState<ScheduledPost | null>(null);

  // Quick create dialog state
  const [quickCreateOpen, setQuickCreateOpen] = useState(false);
  const [selectedDateForCreate, setSelectedDateForCreate] = useState<Date | null>(null);
  const [connectors, setConnectors] = useState<SocialConnector[]>([]);

  // Filters state
  const [filters, setFilters] = useState<CalendarFilters>({
    platforms: [],
    statuses: [],
  });

  // Fetch calendar data
  const fetchCalendarData = useCallback(async () => {
    const brandId = localStorage.getItem("brand_id");
    if (!brandId) return;

    setIsLoading(true);
    try {
      const month = format(currentDate, "yyyy-MM");
      const response = await postsApi.getCalendar(brandId, { month });
      setCalendarDays(response.data.days || []);
    } catch (error) {
      console.error("Error fetching calendar:", error);
      toast({
        title: "Erreur",
        description: "Impossible de charger le calendrier",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [currentDate]);

  useEffect(() => {
    fetchCalendarData();
  }, [fetchCalendarData]);

  // Fetch connectors for quick create dialog
  useEffect(() => {
    const fetchConnectors = async () => {
      const brandId = localStorage.getItem("brand_id");
      if (!brandId) return;

      try {
        const response = await connectorsApi.list(brandId);
        setConnectors(response.data || []);
      } catch (error) {
        console.error("Error fetching connectors:", error);
      }
    };

    fetchConnectors();
  }, []);

  // Platform mapping for filtering
  const platformMap: Record<string, Platform[]> = {
    instagram: ["instagram_post", "instagram_story", "instagram_reel"],
    tiktok: ["tiktok"],
    linkedin: ["linkedin"],
    facebook: ["facebook"],
  };

  // Filter calendar days based on selected filters
  const filteredCalendarDays = useMemo(() => {
    if (filters.platforms.length === 0 && filters.statuses.length === 0) {
      return calendarDays;
    }

    return calendarDays.map((day) => ({
      ...day,
      scheduled_posts: day.scheduled_posts.filter((post) => {
        // Check platform filter
        let platformMatch = true;
        if (filters.platforms.length > 0) {
          // Get the platform from content_snapshot or connector
          const postPlatform = post.content_snapshot?.media_type
            ? filters.platforms.some((p) => {
                // Match against common platform patterns
                const connector = connectors.find((c) => c.id === post.connector_id);
                if (connector) {
                  const connectorPlatforms = platformMap[connector.platform] || [];
                  return filters.platforms.some((fp) => connectorPlatforms.includes(fp) || fp === connector.platform);
                }
                return false;
              })
            : filters.platforms.some((p) => {
                const connector = connectors.find((c) => c.id === post.connector_id);
                if (connector) {
                  const connectorPlatforms = platformMap[connector.platform] || [];
                  return connectorPlatforms.includes(p) || p === connector.platform;
                }
                return false;
              });
          platformMatch = postPlatform;
        }

        // Check status filter
        let statusMatch = true;
        if (filters.statuses.length > 0) {
          statusMatch = filters.statuses.includes(post.status as PostStatus);
        }

        return platformMatch && statusMatch;
      }),
    }));
  }, [calendarDays, filters, connectors]);

  // Handle day click (quick create)
  const handleDayClick = (date: Date) => {
    // Set default time to 10:00 AM
    const dateWithTime = setMinutes(setHours(date, 10), 0);
    setSelectedDateForCreate(dateWithTime);
    setQuickCreateOpen(true);
  };

  // Handle post click
  const handlePostClick = (post: ScheduledPost) => {
    setSelectedPost(post);
    // TODO: Open detail panel or modal in next iteration
  };

  // Handle date change with animation
  const handleDateChange = (date: Date) => {
    setCurrentDate(date);
  };

  // Handle post move with optimistic update and rollback
  const handlePostMove = useCallback(
    async (postId: string, newDate: Date, post: ScheduledPost): Promise<boolean> => {
      // Store original state for rollback
      const originalCalendarDays = [...calendarDays];
      const originalScheduledAt = post.scheduled_at;

      // Calculate new scheduled time (keep the same time, change the date)
      const originalDate = new Date(post.scheduled_at);
      const newScheduledAt = setMinutes(
        setHours(newDate, originalDate.getHours()),
        originalDate.getMinutes()
      );

      // Optimistic update: move the post immediately in UI
      setCalendarDays((prevDays) => {
        return prevDays.map((day) => {
          const dayDate = format(new Date(day.date), "yyyy-MM-dd");
          const originalDayDate = format(new Date(originalScheduledAt), "yyyy-MM-dd");
          const newDayDate = format(newDate, "yyyy-MM-dd");

          // Remove from original day
          if (dayDate === originalDayDate) {
            return {
              ...day,
              scheduled_posts: day.scheduled_posts.filter((p) => p.id !== postId),
            };
          }

          // Add to new day
          if (dayDate === newDayDate) {
            const updatedPost: ScheduledPost = {
              ...post,
              scheduled_at: newScheduledAt.toISOString(),
            };
            return {
              ...day,
              scheduled_posts: [...day.scheduled_posts, updatedPost].sort(
                (a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime()
              ),
            };
          }

          return day;
        });
      });

      // Show optimistic toast
      const formattedDate = format(newDate, "d MMMM yyyy", { locale: fr });
      toast({
        title: "Deplacement en cours...",
        description: `Post deplace au ${formattedDate}`,
      });

      try {
        // Call API to update the post
        await postsApi.bulkSchedule({
          items: [
            {
              scheduled_post_id: postId,
              new_scheduled_at: newScheduledAt.toISOString(),
            },
          ],
        });

        // Success toast
        toast({
          title: "Post deplace",
          description: `Le post a ete deplace au ${formattedDate}`,
        });

        return true;
      } catch (error) {
        console.error("Error moving post:", error);

        // ROLLBACK: Restore original state
        setCalendarDays(originalCalendarDays);

        // Error toast
        toast({
          title: "Erreur",
          description: "Impossible de deplacer le post. Il a ete remis a sa position d'origine.",
          variant: "destructive",
        });

        return false;
      }
    },
    [calendarDays]
  );

  // Handle quick create submission with optimistic update
  const handleQuickCreate = useCallback(
    async (data: QuickCreateData) => {
      const brandId = localStorage.getItem("brand_id");
      if (!brandId) {
        toast({
          title: "Erreur",
          description: "Marque non trouvee",
          variant: "destructive",
        });
        return;
      }

      // Create optimistic post for immediate UI feedback
      const tempId = `temp-${Date.now()}`;
      const optimisticPost: ScheduledPost = {
        id: tempId,
        brand_id: brandId,
        connector_id: data.connectorId,
        scheduled_at: data.scheduledDate.toISOString(),
        timezone: "Europe/Paris",
        status: "scheduled",
        content_snapshot: {
          caption: data.caption,
          hashtags: [],
          media_urls: [],
          media_type: data.mediaType,
        },
        retry_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      // Optimistic update: add the post immediately
      const dateKey = format(data.scheduledDate, "yyyy-MM-dd");
      setCalendarDays((prevDays) => {
        const dayExists = prevDays.some(
          (day) => format(new Date(day.date), "yyyy-MM-dd") === dateKey
        );

        if (dayExists) {
          return prevDays.map((day) => {
            if (format(new Date(day.date), "yyyy-MM-dd") === dateKey) {
              return {
                ...day,
                scheduled_posts: [...day.scheduled_posts, optimisticPost].sort(
                  (a, b) =>
                    new Date(a.scheduled_at).getTime() -
                    new Date(b.scheduled_at).getTime()
                ),
              };
            }
            return day;
          });
        } else {
          // Create new day entry
          return [
            ...prevDays,
            {
              date: dateKey,
              scheduled_posts: [optimisticPost],
              ideas: [],
            },
          ].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
        }
      });

      const formattedDate = format(data.scheduledDate, "d MMMM yyyy", { locale: fr });
      toast({
        title: "Creation en cours...",
        description: `Post planifie pour le ${formattedDate}`,
      });

      try {
        // Call API to create the draft and schedule it
        const response = await postsApi.quickCreate(brandId, {
          title: data.title,
          caption: data.caption,
          platform: data.platform,
          media_type: data.mediaType,
          scheduled_at: data.scheduledDate.toISOString(),
          connector_id: data.connectorId,
        });

        // Replace temp post with real post from API
        const apiResponse = response.data;
        const realPost: ScheduledPost = {
          id: apiResponse.id,
          brand_id: brandId,
          connector_id: apiResponse.connector_id,
          scheduled_at: apiResponse.scheduled_at,
          timezone: "Europe/Paris",
          status: apiResponse.status,
          content_snapshot: {
            caption: apiResponse.caption,
            hashtags: [],
            media_urls: [],
            media_type: apiResponse.media_type,
          },
          retry_count: 0,
          created_at: apiResponse.created_at,
          updated_at: apiResponse.updated_at,
        };
        setCalendarDays((prevDays) =>
          prevDays.map((day) => {
            if (format(new Date(day.date), "yyyy-MM-dd") === dateKey) {
              return {
                ...day,
                scheduled_posts: day.scheduled_posts.map((p) =>
                  p.id === tempId ? realPost : p
                ),
              };
            }
            return day;
          })
        );

        toast({
          title: "Post cree",
          description: `Votre post a ete planifie pour le ${formattedDate}`,
        });
      } catch (error) {
        console.error("Error creating post:", error);

        // ROLLBACK: Remove the optimistic post
        setCalendarDays((prevDays) =>
          prevDays.map((day) => {
            if (format(new Date(day.date), "yyyy-MM-dd") === dateKey) {
              return {
                ...day,
                scheduled_posts: day.scheduled_posts.filter((p) => p.id !== tempId),
              };
            }
            return day;
          })
        );

        toast({
          title: "Erreur",
          description: "Impossible de creer le post. Veuillez reessayer.",
          variant: "destructive",
        });

        throw error;
      }
    },
    []
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
          <h1 className="text-3xl font-bold">Calendrier</h1>
          <p className="text-muted-foreground">
            Planifiez et visualisez vos publications
          </p>
        </div>
        <Button variant="gradient" onClick={() => router.push("/studio")}>
          <Plus className="w-4 h-4 mr-2" />
          Nouveau post
        </Button>
      </div>

      {/* Calendar controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <CalendarHeader
          currentDate={currentDate}
          viewMode={viewMode}
          onDateChange={handleDateChange}
          onViewModeChange={setViewMode}
        />
        <CalendarFiltersComponent
          filters={filters}
          onFiltersChange={setFilters}
        />
      </div>

      {/* Calendar content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          {/* Desktop: Show grid or week based on view mode */}
          <div className="hidden md:block">
            {viewMode === "month" ? (
              <CalendarGrid
                currentDate={currentDate}
                calendarDays={filteredCalendarDays}
                onDayClick={handleDayClick}
                onPostClick={handlePostClick}
                onPostMove={handlePostMove}
              />
            ) : (
              <WeekView
                currentDate={currentDate}
                calendarDays={filteredCalendarDays}
                onDayClick={handleDayClick}
                onPostClick={handlePostClick}
              />
            )}
          </div>

          {/* Mobile: Always show week/list view (no drag & drop) */}
          <div className="md:hidden">
            <WeekView
              currentDate={currentDate}
              calendarDays={filteredCalendarDays}
              onDayClick={handleDayClick}
              onPostClick={handlePostClick}
            />
          </div>
        </>
      )}

      {/* Empty state */}
      {!isLoading && filteredCalendarDays.every((day) => day.scheduled_posts.length === 0) && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-12"
        >
          <div className="w-16 h-16 rounded-2xl bg-muted mx-auto mb-4 flex items-center justify-center">
            <Plus className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="font-semibold mb-2">Aucun post planifie</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mb-4">
            Commencez a planifier votre contenu en creant votre premier post.
          </p>
          <Button variant="gradient" onClick={() => router.push("/studio")}>
            <Plus className="w-4 h-4 mr-2" />
            Creer mon premier post
          </Button>
        </motion.div>
      )}

      {/* Quick create dialog */}
      <QuickCreateDialog
        open={quickCreateOpen}
        onOpenChange={setQuickCreateOpen}
        selectedDate={selectedDateForCreate}
        connectors={connectors}
        onSubmit={handleQuickCreate}
      />
    </motion.div>
  );
}
