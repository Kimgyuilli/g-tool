import { MailMessage } from "@/features/mail/types";
import { CategoryBadge } from "@/features/mail/components/CategoryBadge";
import { SourceBadge } from "@/features/mail/components/SourceBadge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { formatDate } from "@/utils/date";
import { cn } from "@/lib/utils";

interface MailListItemProps {
  mail: MailMessage;
  categories: string[];
  isSelected?: boolean;
  onSelect: (mail: MailMessage) => void;
  onDragStart: (e: React.DragEvent, mailId: number, classificationId: number | null) => void;
  onUpdateCategory: (classificationId: number, category: string, mailId: number) => void;
}

export function MailListItem({
  mail,
  categories,
  isSelected,
  onSelect,
  onDragStart,
  onUpdateCategory,
}: MailListItemProps) {
  return (
    <div
      draggable
      onDragStart={(e) =>
        onDragStart(e, mail.id, mail.classification?.classification_id ?? null)
      }
      onClick={() => onSelect(mail)}
      className={cn(
        "group flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors border-b last:border-b-0",
        isSelected
          ? "bg-accent"
          : "hover:bg-accent/50",
        !mail.is_read && "font-medium"
      )}
    >
      {/* Unread indicator */}
      <span
        className={cn(
          "h-2 w-2 shrink-0 rounded-full",
          !mail.is_read ? "bg-blue-500" : "bg-transparent"
        )}
      />

      {/* Source */}
      <span className="shrink-0">
        <SourceBadge source={mail.source} small />
      </span>

      {/* Content */}
      <div className="flex flex-1 items-center gap-3 min-w-0">
        {/* Sender */}
        <span className="w-36 truncate text-sm">
          {mail.from_name || mail.from_email || "(알 수 없음)"}
        </span>

        {/* Subject */}
        <span className={cn(
          "flex-1 truncate text-sm",
          mail.is_read && "text-muted-foreground"
        )}>
          {mail.subject || "(제목 없음)"}
        </span>
      </div>

      {/* Category badge with dropdown */}
      <span className="shrink-0" onClick={(e) => e.stopPropagation()}>
        {mail.classification ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="focus:outline-none" title="클릭하여 분류 수정">
                <CategoryBadge
                  category={mail.classification.category}
                  confidence={mail.classification.confidence}
                  userFeedback={mail.classification.user_feedback}
                  small
                />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel className="text-xs">분류 변경</DropdownMenuLabel>
              <DropdownMenuSeparator />
              {categories.map((cat) => (
                <DropdownMenuItem
                  key={cat}
                  onClick={() =>
                    onUpdateCategory(
                      mail.classification!.classification_id,
                      cat,
                      mail.id
                    )
                  }
                  className={cn(
                    "text-xs",
                    mail.classification?.category === cat && "font-semibold"
                  )}
                >
                  {cat}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <span className="text-xs text-muted-foreground">-</span>
        )}
      </span>

      {/* Date */}
      <span className="shrink-0 text-xs text-muted-foreground w-16 text-right">
        {formatDate(mail.received_at)}
      </span>
    </div>
  );
}
