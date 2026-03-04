import { MailDetail } from "@/features/mail/types";
import { CategoryBadge } from "@/features/mail/components/CategoryBadge";
import { SourceBadge } from "@/features/mail/components/SourceBadge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { X, ChevronDown } from "lucide-react";
import { HtmlEmailRenderer } from "@/features/mail/components/HtmlEmailRenderer";

interface MailDetailViewProps {
  mail: MailDetail;
  categories: string[];
  onBack: () => void;
  onUpdateCategory: (classificationId: number, category: string, mailId: number) => void;
}

export function MailDetailView({
  mail,
  categories,
  onBack,
  onUpdateCategory,
}: MailDetailViewProps) {
  const cls = mail.classification;

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2 min-w-0">
          <SourceBadge source={mail.source} />
          {cls && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="flex items-center gap-1 focus:outline-none">
                  <CategoryBadge
                    category={cls.category}
                    confidence={cls.confidence}
                    userFeedback={cls.user_feedback}
                  />
                  <ChevronDown className="h-3 w-3 text-muted-foreground" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuLabel className="text-xs">분류 변경</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {categories.map((cat) => (
                  <DropdownMenuItem
                    key={cat}
                    onClick={() => onUpdateCategory(cls.classification_id, cat, mail.id)}
                    className="text-xs"
                  >
                    {cat}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {mail.folder && mail.source === "naver" && (
            <span className="text-xs text-muted-foreground">{mail.folder}</span>
          )}
        </div>
        <Button variant="ghost" size="icon" onClick={onBack} className="shrink-0">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Subject & meta */}
      <div className="px-6 py-4 space-y-3">
        <h2 className="text-lg font-semibold leading-tight">
          {mail.subject || "(제목 없음)"}
        </h2>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">
            {mail.from_name || mail.from_email}
          </span>
          {mail.from_name && (
            <span className="text-xs">&lt;{mail.from_email}&gt;</span>
          )}
          <span className="ml-auto text-xs">
            {mail.received_at
              ? new Date(mail.received_at).toLocaleString("ko-KR")
              : ""}
          </span>
        </div>
      </div>

      <Separator />

      {/* Body */}
      <div className="flex-1 overflow-auto px-6 py-4">
        {mail.body_html ? (
          <HtmlEmailRenderer html={mail.body_html} />
        ) : (
          <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans">
            {mail.body_text || "(본문 없음)"}
          </pre>
        )}
      </div>
    </div>
  );
}
