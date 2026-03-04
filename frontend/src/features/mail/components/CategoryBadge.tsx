import { Badge } from "@/components/ui/badge";
import { CATEGORY_COLORS, DEFAULT_BADGE } from "@/features/mail/constants";

interface CategoryBadgeProps {
  category: string;
  confidence: number | null;
  userFeedback: string | null;
  small?: boolean;
}

export function CategoryBadge({
  category,
  confidence,
  userFeedback,
  small,
}: CategoryBadgeProps) {
  const colors = CATEGORY_COLORS[category] || DEFAULT_BADGE;
  return (
    <Badge
      variant="secondary"
      className={`${colors} border-0 ${small ? "px-1.5 py-0 text-[10px]" : "px-2.5 py-0.5 text-xs"}`}
    >
      {userFeedback && (
        <span title="수동 수정됨" className="opacity-60 mr-0.5">
          *
        </span>
      )}
      {category}
      {confidence !== null && (
        <span className={`opacity-60 ${small ? "ml-0.5" : "ml-1"}`}>
          {Math.round(confidence * 100)}%
        </span>
      )}
    </Badge>
  );
}
