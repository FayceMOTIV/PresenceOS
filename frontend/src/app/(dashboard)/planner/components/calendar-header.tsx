"use client";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight, Calendar, List } from "lucide-react";
import { format, addMonths, subMonths } from "date-fns";
import { fr } from "date-fns/locale";

export type ViewMode = "month" | "week";

interface CalendarHeaderProps {
  currentDate: Date;
  viewMode: ViewMode;
  onDateChange: (date: Date) => void;
  onViewModeChange: (mode: ViewMode) => void;
}

export function CalendarHeader({
  currentDate,
  viewMode,
  onDateChange,
  onViewModeChange,
}: CalendarHeaderProps) {
  const handlePrevious = () => {
    onDateChange(subMonths(currentDate, 1));
  };

  const handleNext = () => {
    onDateChange(addMonths(currentDate, 1));
  };

  const handleToday = () => {
    onDateChange(new Date());
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
      <div className="flex items-center gap-4">
        {/* Navigation */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={handlePrevious}
            className="h-9 w-9"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={handleNext}
            className="h-9 w-9"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Current month/year */}
        <h2 className="text-xl font-semibold capitalize">
          {format(currentDate, "MMMM yyyy", { locale: fr })}
        </h2>

        <Button variant="ghost" size="sm" onClick={handleToday}>
          Aujourd&apos;hui
        </Button>
      </div>

      {/* View mode toggle */}
      <div className="flex items-center gap-2">
        <div className="flex rounded-lg border p-1">
          <Button
            variant={viewMode === "month" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onViewModeChange("month")}
            className="h-8 px-3"
          >
            <Calendar className="h-4 w-4 mr-2" />
            Mois
          </Button>
          <Button
            variant={viewMode === "week" ? "secondary" : "ghost"}
            size="sm"
            onClick={() => onViewModeChange("week")}
            className="h-8 px-3"
          >
            <List className="h-4 w-4 mr-2" />
            Semaine
          </Button>
        </div>
      </div>
    </div>
  );
}
