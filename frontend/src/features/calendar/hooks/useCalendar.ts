import { useState, useEffect, useCallback } from "react";
import { apiFetch } from "@/lib/api";
import type { CalendarInfo, CalendarEvent, CalendarsResponse, EventsResponse, CreateEventRequest } from "@/features/calendar/types";

interface UseCalendarOptions {
  userId: number | null;
}

export function useCalendar({ userId }: UseCalendarOptions) {
  const [calendars, setCalendars] = useState<CalendarInfo[]>([]);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [selectedCalendarIds, setSelectedCalendarIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());

  // 캘린더 목록 로드
  const loadCalendars = useCallback(async () => {
    if (!userId) return;
    try {
      const data = await apiFetch<CalendarsResponse>(`/api/calendar/calendars?user_id=${userId}`);
      setCalendars(data.calendars);
      // 기본적으로 모든 캘린더 선택
      setSelectedCalendarIds(new Set(data.calendars.map((c) => c.id)));
    } catch {
      // 캘린더 권한 없을 수 있음
      setCalendars([]);
    }
  }, [userId]);

  // 이벤트 로드 (현재 월 기준, 모든 캘린더에서)
  const loadEvents = useCallback(async (date?: Date) => {
    if (!userId || calendars.length === 0) return;
    setLoading(true);
    try {
      const target = date || currentDate;
      const year = target.getFullYear();
      const month = target.getMonth();
      const timeMin = new Date(year, month, 1 - 7).toISOString();
      const timeMax = new Date(year, month + 1, 7).toISOString();

      // 모든 캘린더에서 이벤트를 병렬로 가져옴
      const results = await Promise.allSettled(
        calendars.map((cal) =>
          apiFetch<EventsResponse>(
            `/api/calendar/events?user_id=${userId}&calendar_id=${encodeURIComponent(cal.id)}&time_min=${timeMin}&time_max=${timeMax}`
          )
        )
      );

      const allEvents: CalendarEvent[] = [];
      for (const result of results) {
        if (result.status === "fulfilled") {
          allEvents.push(...result.value.events);
        }
      }
      setEvents(allEvents);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [userId, currentDate, calendars]);

  // 캘린더 목록 로드
  useEffect(() => {
    if (userId) {
      loadCalendars();
    }
  }, [userId, loadCalendars]);

  // 이벤트 로드
  useEffect(() => {
    if (userId) {
      loadEvents();
    }
  }, [userId, currentDate, loadEvents]);

  // 선택된 캘린더로 이벤트 필터링
  const filteredEvents = events.filter((ev) => selectedCalendarIds.has(ev.calendar_id));

  const toggleCalendar = useCallback((calendarId: string) => {
    setSelectedCalendarIds((prev) => {
      const next = new Set(prev);
      if (next.has(calendarId)) {
        next.delete(calendarId);
      } else {
        next.add(calendarId);
      }
      return next;
    });
  }, []);

  const goToMonth = useCallback((date: Date) => {
    setCurrentDate(date);
  }, []);

  const goToPrevMonth = useCallback(() => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  }, []);

  const goToNextMonth = useCallback(() => {
    setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  }, []);

  const goToToday = useCallback(() => {
    setCurrentDate(new Date());
  }, []);

  const createEvent = useCallback(async (req: CreateEventRequest) => {
    if (!userId) return null;
    const event = await apiFetch<CalendarEvent>(`/api/calendar/events?user_id=${userId}`, {
      method: "POST",
      body: JSON.stringify(req),
    });
    // 생성 후 이벤트 목록 새로고침
    await loadEvents();
    return event;
  }, [userId, loadEvents]);

  const deleteEvent = useCallback(async (eventId: string, calendarId: string) => {
    if (!userId) return;
    await apiFetch(`/api/calendar/events/${encodeURIComponent(eventId)}?user_id=${userId}&calendar_id=${encodeURIComponent(calendarId)}`, {
      method: "DELETE",
    });
    await loadEvents();
  }, [userId, loadEvents]);

  return {
    calendars,
    events: filteredEvents,
    allEvents: events,
    selectedCalendarIds,
    loading,
    currentDate,
    loadCalendars,
    loadEvents,
    toggleCalendar,
    goToMonth,
    goToPrevMonth,
    goToNextMonth,
    goToToday,
    createEvent,
    deleteEvent,
  };
}
