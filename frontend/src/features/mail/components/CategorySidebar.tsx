import { CategoryCountsResponse, FeedbackStats } from "@/features/mail/types";
import { CATEGORY_COLORS, CATEGORY_DOT_COLORS, DEFAULT_BADGE } from "@/features/mail/constants";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Inbox, ChevronDown, ChevronUp, Brain } from "lucide-react";

interface CategorySidebarProps {
  categoryCounts: CategoryCountsResponse | null;
  categoryFilter: string | null;
  feedbackStats: FeedbackStats | null;
  showSenderRules: boolean;
  dragOverCategory: string | null;
  onCategoryFilter: (category: string | null) => void;
  onToggleSenderRules: () => void;
  onDragOver: (category: string) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent, category: string) => void;
}

export function CategorySidebar({
  categoryCounts,
  categoryFilter,
  feedbackStats,
  showSenderRules,
  dragOverCategory,
  onCategoryFilter,
  onToggleSenderRules,
  onDragOver,
  onDragLeave,
  onDrop,
}: CategorySidebarProps) {
  return (
    <div className="flex h-full flex-col py-3">
      <div className="px-4 mb-2">
        <h2 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          카테고리
        </h2>
      </div>

      <nav className="flex-1 space-y-0.5 px-2 overflow-auto">
        {/* All */}
        <button
          onClick={() => onCategoryFilter(null)}
          className={cn(
            "flex items-center justify-between w-full px-3 py-1.5 rounded-md text-sm text-left transition-colors",
            categoryFilter === null
              ? "bg-accent font-medium"
              : "hover:bg-accent/50"
          )}
        >
          <span className="flex items-center gap-2">
            <Inbox className="h-4 w-4 text-muted-foreground" />
            전체
          </span>
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5 min-w-6 justify-center">
            {categoryCounts?.total || 0}
          </Badge>
        </button>

        {/* Categories - drop targets */}
        {categoryCounts?.categories.map((cat) => (
          <button
            key={cat.name}
            onClick={() => onCategoryFilter(cat.name)}
            onDragOver={(e) => {
              e.preventDefault();
              onDragOver(cat.name);
            }}
            onDragLeave={onDragLeave}
            onDrop={(e) => {
              onDrop(e, cat.name);
              onDragLeave();
            }}
            className={cn(
              "flex items-center justify-between w-full px-3 py-1.5 rounded-md text-sm text-left transition-colors",
              dragOverCategory === cat.name && "ring-2 ring-ring",
              categoryFilter === cat.name
                ? "bg-accent font-medium"
                : "hover:bg-accent/50"
            )}
          >
            <span className="flex items-center gap-2">
              <span
                className={cn(
                  "w-2 h-2 rounded-full",
                  CATEGORY_DOT_COLORS[cat.name] || "bg-muted-foreground"
                )}
              />
              {cat.name}
            </span>
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5 min-w-6 justify-center">
              {cat.count}
            </Badge>
          </button>
        ))}

        {/* Unclassified */}
        <button
          onClick={() => onCategoryFilter("unclassified")}
          className={cn(
            "flex items-center justify-between w-full px-3 py-1.5 rounded-md text-sm text-left transition-colors",
            categoryFilter === "unclassified"
              ? "bg-accent font-medium"
              : "hover:bg-accent/50"
          )}
        >
          <span className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-muted-foreground/40" />
            미분류
          </span>
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0 h-5 min-w-6 justify-center">
            {categoryCounts?.unclassified || 0}
          </Badge>
        </button>
      </nav>

      {/* Feedback Stats Section */}
      <Separator className="my-3" />
      <div className="px-4">
        <h2 className="flex items-center gap-1.5 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          <Brain className="h-3 w-3" />
          학습 현황
        </h2>

        {feedbackStats && feedbackStats.total_feedbacks > 0 ? (
          <div className="space-y-2">
            <div className="px-2 py-2 bg-muted/50 rounded-md space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">피드백</span>
                <span className="font-medium">{feedbackStats.total_feedbacks}건</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">발신자 규칙</span>
                <span className="font-medium">{feedbackStats.sender_rules.length}건</span>
              </div>
            </div>

            {feedbackStats.sender_rules.length > 0 && (
              <div>
                <button
                  onClick={onToggleSenderRules}
                  className="flex items-center justify-between w-full px-2 py-1.5 text-xs text-left text-muted-foreground hover:text-foreground rounded-md transition-colors"
                >
                  <span>발신자 규칙 상세</span>
                  {showSenderRules ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </button>

                {showSenderRules && (
                  <div className="mt-1 space-y-1.5 px-1">
                    {feedbackStats.sender_rules.slice(0, 5).map((rule) => (
                      <div key={rule.from_email} className="text-xs text-muted-foreground">
                        <div className="truncate font-medium text-foreground">
                          {rule.from_email}
                        </div>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span>&rarr;</span>
                          <span
                            className={cn(
                              "inline-block px-1.5 py-0.5 rounded-full text-[10px]",
                              CATEGORY_COLORS[rule.category] || DEFAULT_BADGE
                            )}
                          >
                            {rule.category}
                          </span>
                          <span className="text-muted-foreground">({rule.count}건)</span>
                        </div>
                      </div>
                    ))}
                    {feedbackStats.sender_rules.length > 5 && (
                      <div className="text-[10px] text-muted-foreground text-center pt-1">
                        외 {feedbackStats.sender_rules.length - 5}건
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="px-2 py-3 text-xs text-muted-foreground text-center">
            분류를 수정하면 AI가 학습합니다
          </div>
        )}
      </div>
    </div>
  );
}
