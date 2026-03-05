import { useState } from "react";
import { CalendarEvent } from "@/features/calendar/types";
import { Button } from "@/components/ui/button";
import { X, MapPin, Clock, Users, ExternalLink, Trash2, Loader2 } from "lucide-react";

interface CalendarEventDetailProps {
  event: CalendarEvent;
  onClose: () => void;
  onDelete: (eventId: string, calendarId: string) => Promise<void>;
}

function formatEventTime(event: CalendarEvent): string {
  if (event.all_day) {
    const start = new Date(event.start);
    const end = new Date(event.end);
    // 종일 이벤트: end는 exclusive이므로 하루 빼기
    end.setDate(end.getDate() - 1);
    if (start.toDateString() === end.toDateString()) {
      return start.toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric" }) + " (종일)";
    }
    return `${start.toLocaleDateString("ko-KR", { month: "long", day: "numeric" })} ~ ${end.toLocaleDateString("ko-KR", { month: "long", day: "numeric" })} (종일)`;
  }

  const start = new Date(event.start);
  const end = new Date(event.end);
  const dateStr = start.toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "short" });
  const startTime = start.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: true });
  const endTime = end.toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit", hour12: true });
  return `${dateStr} ${startTime} ~ ${endTime}`;
}

export function CalendarEventDetail({ event, onClose, onDelete }: CalendarEventDetailProps) {
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await onDelete(event.id, event.calendar_id);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="h-full flex flex-col overflow-auto">
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b">
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold truncate">{event.summary}</h2>
          {event.status === "cancelled" && (
            <span className="text-xs text-red-500 font-medium">취소됨</span>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleDelete}
            disabled={deleting}
            className="text-muted-foreground hover:text-destructive"
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Time */}
        <div className="flex items-start gap-3">
          <Clock className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
          <span className="text-sm">{formatEventTime(event)}</span>
        </div>

        {/* Location */}
        {event.location && (
          <div className="flex items-start gap-3">
            <MapPin className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
            <span className="text-sm">{event.location}</span>
          </div>
        )}

        {/* Attendees */}
        {event.attendees && event.attendees.length > 0 && (
          <div className="flex items-start gap-3">
            <Users className="h-4 w-4 mt-0.5 text-muted-foreground shrink-0" />
            <div className="text-sm space-y-1">
              {event.attendees.map((a) => (
                <div key={a.email} className="flex items-center gap-2">
                  <span>{a.email}</span>
                  <span className="text-xs text-muted-foreground">
                    {a.response_status === "accepted" ? "수락" :
                     a.response_status === "declined" ? "거절" :
                     a.response_status === "tentative" ? "미정" : "응답 대기"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Description */}
        {event.description && (
          <div className="border-t pt-4">
            <p className="text-sm whitespace-pre-wrap">{event.description}</p>
          </div>
        )}

        {/* Google Calendar link */}
        {event.html_link && (
          <div className="border-t pt-4">
            <a
              href={event.html_link}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline inline-flex items-center gap-1"
            >
              <ExternalLink className="h-3 w-3" />
              Google Calendar에서 보기
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
