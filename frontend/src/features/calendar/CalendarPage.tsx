"use client";

import { useState } from "react";
import { useCalendar } from "@/features/calendar/hooks/useCalendar";
import { CalendarMonthView } from "@/features/calendar/components/CalendarMonthView";
import { CalendarEventDetail } from "@/features/calendar/components/CalendarEventDetail";
import { CalendarSidebar } from "@/features/calendar/components/CalendarSidebar";
import { EventCreateModal } from "@/features/calendar/components/EventCreateModal";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { Skeleton } from "@/components/ui/skeleton";
import type { CalendarEvent, CreateEventRequest } from "@/features/calendar/types";
import { toast } from "sonner";

interface CalendarPageProps {
  userId: number | null;
}

export function CalendarPage({ userId }: CalendarPageProps) {
  const {
    calendars,
    events,
    selectedCalendarIds,
    loading,
    currentDate,
    toggleCalendar,
    goToPrevMonth,
    goToNextMonth,
    goToToday,
    createEvent,
  } = useCalendar({ userId, enabled: true });

  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createDefaultDate, setCreateDefaultDate] = useState<Date | undefined>();

  const handleSelectDate = (date: Date) => {
    setCreateDefaultDate(date);
    setShowCreateModal(true);
  };

  const handleCreateEvent = async (req: CreateEventRequest) => {
    try {
      await createEvent(req);
      toast.success("일정이 추가되었습니다");
    } catch {
      toast.error("일정 추가에 실패했습니다");
    }
  };

  if (loading && events.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-hidden flex">
      {/* Calendar sidebar */}
      <aside className="hidden md:flex w-56 shrink-0 border-r overflow-auto">
        <div className="flex flex-col h-full">
          <div className="p-3">
            <Button
              className="w-full"
              onClick={() => {
                setCreateDefaultDate(new Date());
                setShowCreateModal(true);
              }}
            >
              <Plus className="h-4 w-4 mr-1" />
              일정 추가
            </Button>
          </div>
          <CalendarSidebar
            calendars={calendars}
            selectedCalendarIds={selectedCalendarIds}
            currentDate={currentDate}
            onToggleCalendar={toggleCalendar}
            onPrevMonth={goToPrevMonth}
            onNextMonth={goToNextMonth}
            onToday={goToToday}
          />
        </div>
      </aside>

      <ResizablePanelGroup orientation="horizontal" className="flex-1">
        {/* Month view */}
        <ResizablePanel defaultSize={selectedEvent ? 65 : 100} minSize={40}>
          <CalendarMonthView
            currentDate={currentDate}
            events={events}
            selectedEventId={selectedEvent?.id ?? null}
            onSelectEvent={setSelectedEvent}
            onSelectDate={handleSelectDate}
          />
        </ResizablePanel>

        {/* Event detail panel */}
        {selectedEvent && (
          <>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={35} minSize={25}>
              <CalendarEventDetail
                event={selectedEvent}
                onClose={() => setSelectedEvent(null)}
              />
            </ResizablePanel>
          </>
        )}
      </ResizablePanelGroup>

      {/* Event create modal */}
      <EventCreateModal
        open={showCreateModal}
        calendars={calendars}
        defaultDate={createDefaultDate}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateEvent}
      />
    </div>
  );
}
