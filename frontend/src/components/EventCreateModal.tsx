"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import type { CalendarInfo, CreateEventRequest } from "@/types/calendar";

interface EventCreateModalProps {
  open: boolean;
  calendars: CalendarInfo[];
  defaultDate?: Date;
  onClose: () => void;
  onSubmit: (req: CreateEventRequest) => Promise<void>;
}

export function EventCreateModal({
  open,
  calendars,
  defaultDate,
  onClose,
  onSubmit,
}: EventCreateModalProps) {
  const primaryCalendar = calendars.find((c) => c.primary);

  const [summary, setSummary] = useState("");
  const [allDay, setAllDay] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endDate, setEndDate] = useState("");
  const [endTime, setEndTime] = useState("10:00");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [calendarId, setCalendarId] = useState(primaryCalendar?.id || calendars[0]?.id || "primary");
  const [saving, setSaving] = useState(false);

  // 모달이 열릴 때 defaultDate로 날짜 초기화
  useEffect(() => {
    if (open) {
      const dateStr = (defaultDate || new Date()).toISOString().slice(0, 10);
      setStartDate(dateStr);
      setEndDate(dateStr);
    }
  }, [open, defaultDate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!summary.trim()) return;

    setSaving(true);
    try {
      let start: string;
      let end: string;

      if (allDay) {
        start = startDate;
        // 종일 이벤트의 end는 exclusive이므로 다음날
        const endD = new Date(endDate);
        endD.setDate(endD.getDate() + 1);
        end = endD.toISOString().slice(0, 10);
      } else {
        start = new Date(`${startDate}T${startTime}`).toISOString();
        end = new Date(`${endDate}T${endTime}`).toISOString();
      }

      await onSubmit({
        summary: summary.trim(),
        start,
        end,
        all_day: allDay,
        calendar_id: calendarId,
        description: description.trim() || undefined,
        location: location.trim() || undefined,
      });

      // 폼 초기화
      setSummary("");
      setDescription("");
      setLocation("");
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>일정 추가</DialogTitle>
          <DialogDescription className="sr-only">Google Calendar에 새 일정을 추가합니다</DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* 제목 */}
          <div>
            <input
              type="text"
              placeholder="제목 추가"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="w-full border-b border-border bg-transparent pb-2 text-lg focus:border-primary focus:outline-none"
              autoFocus
              required
            />
          </div>

          {/* 종일 이벤트 */}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={allDay}
              onChange={(e) => setAllDay(e.target.checked)}
              className="rounded"
            />
            종일
          </label>

          {/* 날짜/시간 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-muted-foreground">시작</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded border border-border bg-background px-2 py-1.5 text-sm"
              />
              {!allDay && (
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="mt-1 w-full rounded border border-border bg-background px-2 py-1.5 text-sm"
                />
              )}
            </div>
            <div>
              <label className="text-xs text-muted-foreground">종료</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded border border-border bg-background px-2 py-1.5 text-sm"
              />
              {!allDay && (
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className="mt-1 w-full rounded border border-border bg-background px-2 py-1.5 text-sm"
                />
              )}
            </div>
          </div>

          {/* 장소 */}
          <div>
            <input
              type="text"
              placeholder="장소 추가"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm"
            />
          </div>

          {/* 설명 */}
          <div>
            <textarea
              placeholder="설명 추가"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="w-full rounded border border-border bg-background px-3 py-2 text-sm resize-none"
            />
          </div>

          {/* 캘린더 선택 */}
          {calendars.length > 1 && (
            <div>
              <label className="text-xs text-muted-foreground">캘린더</label>
              <select
                value={calendarId}
                onChange={(e) => setCalendarId(e.target.value)}
                className="w-full rounded border border-border bg-background px-3 py-2 text-sm"
              >
                {calendars.map((cal) => (
                  <option key={cal.id} value={cal.id}>
                    {cal.summary}{cal.primary ? " (기본)" : ""}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 버튼 */}
          <DialogFooter>
            <Button type="button" variant="ghost" onClick={onClose}>
              취소
            </Button>
            <Button type="submit" disabled={saving || !summary.trim()}>
              {saving ? "저장 중..." : "저장"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
