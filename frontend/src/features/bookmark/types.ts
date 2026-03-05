export interface BookmarkCategory {
  id: number;
  name: string;
  color: string;
  position: number;
  bookmark_count: number;
  created_at: string | null;
}

export interface Bookmark {
  id: number;
  user_id: number;
  category_id: number | null;
  title: string;
  url: string;
  description: string | null;
  favicon_url: string | null;
  position: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface BookmarkCreateRequest {
  title: string;
  url: string;
  description?: string;
  category_id?: number | null;
}

export interface BookmarkUpdateRequest {
  title?: string;
  url?: string;
  description?: string;
  category_id?: number | null;
}

export interface CategoryCreateRequest {
  name: string;
  color?: string;
}

export interface CategoriesResponse {
  categories: BookmarkCategory[];
}

export interface BookmarksResponse {
  bookmarks: Bookmark[];
}

// Tailwind color options for categories
export const CATEGORY_COLORS: { value: string; label: string; class: string }[] = [
  { value: "gray", label: "회색", class: "bg-gray-500" },
  { value: "red", label: "빨강", class: "bg-red-500" },
  { value: "orange", label: "주황", class: "bg-orange-500" },
  { value: "yellow", label: "노랑", class: "bg-yellow-500" },
  { value: "green", label: "초록", class: "bg-green-500" },
  { value: "blue", label: "파랑", class: "bg-blue-500" },
  { value: "purple", label: "보라", class: "bg-purple-500" },
  { value: "pink", label: "분홍", class: "bg-pink-500" },
];

export const COLOR_DOT_MAP: Record<string, string> = Object.fromEntries(
  CATEGORY_COLORS.map((c) => [c.value, c.class])
);
