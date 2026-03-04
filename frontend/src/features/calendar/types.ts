export interface CalendarInfo {
  id: string;
  summary: string;
  background_color: string | null;
  foreground_color: string | null;
  primary: boolean;
  selected: boolean;
}

export interface CalendarEvent {
  id: string;
  summary: string;
  description: string | null;
  location: string | null;
  start: string;
  end: string;
  all_day: boolean;
  calendar_id: string;
  status: string;
  html_link: string | null;
  color_id: string | null;
  creator: string | null;
  organizer: string | null;
  attendees: { email: string; response_status: string }[] | null;
  recurrence: string[] | null;
  created: string | null;
  updated: string | null;
}

export interface CalendarsResponse {
  calendars: CalendarInfo[];
}

export interface EventsResponse {
  events: CalendarEvent[];
  calendar_id: string;
}

export interface CreateEventRequest {
  summary: string;
  start: string;
  end: string;
  all_day: boolean;
  calendar_id: string;
  description?: string;
  location?: string;
}
