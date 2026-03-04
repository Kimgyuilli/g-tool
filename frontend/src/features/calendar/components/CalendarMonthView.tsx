"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import type { CalendarEvent } from "@/features/calendar/types";

interface CalendarMonthViewProps {
  currentDate: Date;
  events: CalendarEvent[];
  selectedEventId: string | null;
  onSelectEvent: (event: CalendarEvent) => void;
  onSelectDate: (date: Date) => void;
}

// 해당 월의 캘린더 그리드 생성 (일~토, 6주)
function getCalendarGrid(year: number, month: number): Date[][] {
  const firstDay = new Date(year, month, 1);
  const startDate = new Date(firstDay);
  startDate.setDate(startDate.getDate() - startDate.getDay()); // 일요일로 이동

  const weeks: Date[][] = [];
  const current = new Date(startDate);
  for (let w = 0; w < 6; w++) {
    const week: Date[] = [];
    for (let d = 0; d < 7; d++) {
      week.push(new Date(current));
      current.setDate(current.getDate() + 1);
    }
    weeks.push(week);
  }
  return weeks;
}

// 이벤트를 날짜별로 그룹핑
function groupEventsByDate(events: CalendarEvent[]): Map<string, CalendarEvent[]> {
  const map = new Map<string, CalendarEvent[]>();
  for (const ev of events) {
    // start에서 날짜 부분만 추출
    const dateStr = ev.start.slice(0, 10); // "YYYY-MM-DD"
    if (!map.has(dateStr)) map.set(dateStr, []);
    map.get(dateStr)!.push(ev);

    // 종일 이벤트가 여러 날에 걸치는 경우 처리
    if (ev.all_day && ev.end) {
      const startD = new Date(ev.start);
      const endD = new Date(ev.end);
      const d = new Date(startD);
      d.setDate(d.getDate() + 1);
      while (d < endD) {
        const ds = d.toISOString().slice(0, 10);
        if (!map.has(ds)) map.set(ds, []);
        map.get(ds)!.push(ev);
        d.setDate(d.getDate() + 1);
      }
    }
  }
  return map;
}

const DAY_NAMES = ["일", "월", "화", "수", "목", "금", "토"];
const MAX_VISIBLE_EVENTS = 3;

export function CalendarMonthView({
  currentDate,
  events,
  selectedEventId,
  onSelectEvent,
  onSelectDate,
}: CalendarMonthViewProps) {
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const weeks = useMemo(() => getCalendarGrid(year, month), [year, month]);
  const eventsByDate = useMemo(() => groupEventsByDate(events), [events]);

  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  return (
    <div className="flex flex-col h-full">
      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 border-b">
        {DAY_NAMES.map((name, i) => (
          <div
            key={name}
            className={cn(
              "py-2 text-center text-xs font-medium text-muted-foreground",
              i === 0 && "text-red-500",
              i === 6 && "text-blue-500"
            )}
          >
            {name}
          </div>
        ))}
      </div>

      {/* 캘린더 그리드 */}
      <div className="grid grid-cols-7 flex-1 auto-rows-fr">
        {weeks.flat().map((date, idx) => {
          const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
          const isCurrentMonth = date.getMonth() === month;
          const isToday = dateStr === todayStr;
          const dayEvents = eventsByDate.get(dateStr) || [];
          const dayOfWeek = idx % 7;

          return (
            <div
              key={dateStr + idx}
              className={cn(
                "border-b border-r p-1 min-h-[80px] cursor-pointer hover:bg-muted/50 transition-colors",
                !isCurrentMonth && "bg-muted/20"
              )}
              onClick={() => onSelectDate(date)}
            >
              <div className="flex justify-center mb-1">
                <span
                  className={cn(
                    "text-xs w-6 h-6 flex items-center justify-center rounded-full",
                    isToday && "bg-primary text-primary-foreground font-bold",
                    !isCurrentMonth && "text-muted-foreground",
                    dayOfWeek === 0 && isCurrentMonth && !isToday && "text-red-500",
                    dayOfWeek === 6 && isCurrentMonth && !isToday && "text-blue-500"
                  )}
                >
                  {date.getDate()}
                </span>
              </div>
              <div className="space-y-0.5">
                {dayEvents.slice(0, MAX_VISIBLE_EVENTS).map((ev) => (
                  <button
                    key={ev.id + dateStr}
                    className={cn(
                      "w-full text-left text-[10px] leading-tight px-1 py-0.5 rounded truncate",
                      ev.all_day
                        ? "bg-primary/10 text-primary font-medium"
                        : "hover:bg-muted",
                      selectedEventId === ev.id && "ring-1 ring-primary"
                    )}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectEvent(ev);
                    }}
                  >
                    {!ev.all_day && (
                      <span className="text-muted-foreground mr-0.5">
                        {new Date(ev.start).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: false })}
                      </span>
                    )}
                    {ev.summary}
                  </button>
                ))}
                {dayEvents.length > MAX_VISIBLE_EVENTS && (
                  <div className="text-[10px] text-muted-foreground px-1">
                    +{dayEvents.length - MAX_VISIBLE_EVENTS}개 더
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
