import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { CalendarInfo } from "@/features/calendar/types";

interface CalendarSidebarProps {
  calendars: CalendarInfo[];
  selectedCalendarIds: Set<string>;
  currentDate: Date;
  onToggleCalendar: (calendarId: string) => void;
  onPrevMonth: () => void;
  onNextMonth: () => void;
  onToday: () => void;
}

export function CalendarSidebar({
  calendars,
  selectedCalendarIds,
  currentDate,
  onToggleCalendar,
  onPrevMonth,
  onNextMonth,
  onToday,
}: CalendarSidebarProps) {
  const monthLabel = currentDate.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
  });

  return (
    <div className="flex flex-col h-full p-3 gap-4">
      {/* Month navigation */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="icon" onClick={onPrevMonth} className="h-7 w-7">
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-sm font-medium">{monthLabel}</span>
          <Button variant="ghost" size="icon" onClick={onNextMonth} className="h-7 w-7">
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
        <Button variant="outline" size="sm" className="w-full" onClick={onToday}>
          오늘
        </Button>
      </div>

      {/* Calendar list */}
      <div className="space-y-1">
        <h3 className="text-xs font-medium text-muted-foreground px-1 mb-2">내 캘린더</h3>
        {calendars.map((cal) => (
          <label
            key={cal.id}
            className="flex items-center gap-2 px-1 py-1 rounded hover:bg-muted cursor-pointer text-sm"
          >
            <input
              type="checkbox"
              checked={selectedCalendarIds.has(cal.id)}
              onChange={() => onToggleCalendar(cal.id)}
              className="rounded"
              style={{
                accentColor: cal.background_color || undefined,
              }}
            />
            <span
              className="w-2 h-2 rounded-full shrink-0"
              style={{ backgroundColor: cal.background_color || "#4285f4" }}
            />
            <span className="truncate">{cal.summary}</span>
            {cal.primary && (
              <span className="text-[10px] text-muted-foreground ml-auto shrink-0">기본</span>
            )}
          </label>
        ))}
      </div>
    </div>
  );
}
