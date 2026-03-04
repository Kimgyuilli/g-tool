import { MailMessage } from "@/features/mail/types";
import { MailListItem } from "@/features/mail/components/MailListItem";
import { Pagination } from "@/components/Pagination";
import { Skeleton } from "@/components/ui/skeleton";
import { Inbox } from "lucide-react";

interface MailListViewProps {
  loading: boolean;
  messages: MailMessage[];
  total: number;
  categories: string[];
  selectedMailId: number | null;
  classifiedCount: number;
  currentPage: number;
  totalPages: number;
  onSelectMail: (mail: MailMessage) => void;
  onDragStart: (e: React.DragEvent, mailId: number, classificationId: number | null) => void;
  onUpdateCategory: (classificationId: number, category: string, mailId: number) => void;
  onPrevPage: () => void;
  onNextPage: () => void;
}

function MailListSkeleton() {
  return (
    <div className="divide-y">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3">
          <Skeleton className="h-2 w-2 rounded-full" />
          <Skeleton className="h-5 w-5 rounded-full" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-5 w-14 rounded-full" />
          <Skeleton className="h-3 w-12" />
        </div>
      ))}
    </div>
  );
}

export function MailListView({
  loading,
  messages,
  total,
  categories,
  selectedMailId,
  classifiedCount,
  currentPage,
  totalPages,
  onSelectMail,
  onDragStart,
  onUpdateCategory,
  onPrevPage,
  onNextPage,
}: MailListViewProps) {
  return (
    <div className="flex h-full flex-col">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2 border-b text-xs text-muted-foreground">
        <span>총 {total}개</span>
        <span>분류됨 {classifiedCount}/{messages.length}</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <MailListSkeleton />
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-20 text-muted-foreground">
            <Inbox className="h-10 w-10" />
            <p className="text-sm">메일이 없습니다.</p>
            <p className="text-xs">
              &quot;동기화&quot; 버튼을 눌러 메일을 가져오세요.
            </p>
          </div>
        ) : (
          <div>
            {messages.map((mail) => (
              <MailListItem
                key={mail.id}
                mail={mail}
                categories={categories}
                isSelected={selectedMailId === mail.id}
                onSelect={onSelectMail}
                onDragStart={onDragStart}
                onUpdateCategory={onUpdateCategory}
              />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && messages.length > 0 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPrev={onPrevPage}
          onNext={onNextPage}
        />
      )}
    </div>
  );
}
