export interface ClassificationInfo {
  classification_id: number;
  category: string;
  confidence: number | null;
  user_feedback: string | null;
}

export interface MailMessage {
  id: number;
  source: "gmail" | "naver";
  external_id: string;
  from_email: string | null;
  from_name: string | null;
  subject: string | null;
  to_email: string | null;
  folder: string | null;
  received_at: string | null;
  is_read: boolean;
  classification: ClassificationInfo | null;
}

export interface MailListResponse {
  total: number;
  offset: number;
  limit: number;
  messages: MailMessage[];
}

export interface MailDetail {
  id: number;
  source: "gmail" | "naver";
  from_email: string | null;
  from_name: string | null;
  subject: string | null;
  body_text: string | null;
  body_html: string | null;
  to_email: string | null;
  folder: string | null;
  received_at: string | null;
  is_read: boolean;
  classification: ClassificationInfo | null;
}

export interface CategoryCount {
  name: string;
  count: number;
  color: string | null;
}

export interface CategoryCountsResponse {
  total: number;
  unclassified: number;
  categories: CategoryCount[];
}

export interface FeedbackStats {
  total_feedbacks: number;
  sender_rules: { from_email: string; category: string; count: number }[];
  recent_feedbacks: { subject: string; original: string; corrected: string; date: string }[];
}
