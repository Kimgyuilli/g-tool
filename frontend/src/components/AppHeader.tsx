import { UserInfo } from "@/features/auth/types";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import {
  RefreshCw,
  Sparkles,
  Tag,
  User,
  LogOut,
  Link,
  Menu,
  Mail,
  Calendar,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AppHeaderProps {
  activePage: "mail" | "calendar";
  onPageChange: (page: "mail" | "calendar") => void;
  userInfo: UserInfo | null;
  sourceFilter: "all" | "gmail" | "naver";
  syncing: boolean;
  classifying: boolean;
  applyingLabels: boolean;
  classifiedCount: number;
  onSync: () => void;
  onClassify: () => void;
  onApplyLabels: () => void;
  onLogout: () => void;
  onNaverConnect: () => void;
  onSourceFilterChange: (source: "all" | "gmail" | "naver") => void;
  onMobileMenuToggle?: () => void;
}

const SOURCE_TABS = [
  { key: "all" as const, label: "전체" },
  { key: "gmail" as const, label: "Gmail" },
  { key: "naver" as const, label: "네이버" },
];

export function AppHeader({
  activePage,
  onPageChange,
  userInfo,
  sourceFilter,
  syncing,
  classifying,
  applyingLabels,
  classifiedCount,
  onSync,
  onClassify,
  onApplyLabels,
  onLogout,
  onNaverConnect,
  onSourceFilterChange,
  onMobileMenuToggle,
}: AppHeaderProps) {
  return (
    <header className="flex h-14 items-center border-b px-4 gap-3">
      {/* Mobile menu button */}
      {onMobileMenuToggle && (
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onMobileMenuToggle}
        >
          <Menu className="h-5 w-5" />
        </Button>
      )}

      {/* Logo */}
      <h1 className="text-base font-semibold tracking-tight hidden sm:block">
        Mail Organizer
      </h1>

      {/* Page navigation */}
      <nav className="flex items-center gap-1 ml-2">
        <Button
          variant={activePage === "mail" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onPageChange("mail")}
        >
          <Mail className="h-4 w-4" />
          <span className="hidden sm:inline">메일</span>
        </Button>
        <Button
          variant={activePage === "calendar" ? "secondary" : "ghost"}
          size="sm"
          onClick={() => onPageChange("calendar")}
        >
          <Calendar className="h-4 w-4" />
          <span className="hidden sm:inline">캘린더</span>
        </Button>
      </nav>

      {/* Source filter tabs - only for mail page */}
      {activePage === "mail" && (
        <div className="flex items-center rounded-lg bg-muted p-0.5 ml-2">
          {SOURCE_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => onSourceFilterChange(tab.key)}
              className={cn(
                "rounded-md px-3 py-1 text-xs font-medium transition-colors",
                sourceFilter === tab.key
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Action buttons - only for mail page */}
      {activePage === "mail" && (
        <div className="flex items-center gap-1.5">
        <Button
          variant="ghost"
          size="sm"
          onClick={onSync}
          disabled={syncing}
        >
          <RefreshCw className={cn("h-4 w-4", syncing && "animate-spin")} />
          <span className="hidden sm:inline">
            {syncing ? "동기화 중" : "동기화"}
          </span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onClassify}
          disabled={classifying}
        >
          <Sparkles className="h-4 w-4" />
          <span className="hidden sm:inline">
            {classifying ? "분류 중" : "AI 분류"}
          </span>
        </Button>

          {sourceFilter === "gmail" && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onApplyLabels}
              disabled={applyingLabels || classifiedCount === 0}
            >
              <Tag className="h-4 w-4" />
              <span className="hidden sm:inline">
                {applyingLabels ? "적용 중" : "라벨 적용"}
              </span>
            </Button>
          )}
        </div>
      )}

      {/* User menu */}
      <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full">
              <User className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <p className="text-sm font-medium">{userInfo?.email}</p>
              <p className="text-xs text-muted-foreground">
                {userInfo?.google_connected ? "Google 연결됨" : ""}
                {userInfo?.naver_connected ? " · 네이버 연결됨" : ""}
              </p>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {userInfo && !userInfo.naver_connected && (
              <>
                <DropdownMenuItem onClick={onNaverConnect}>
                  <Link className="h-4 w-4" />
                  네이버 메일 연결
                </DropdownMenuItem>
                <DropdownMenuSeparator />
              </>
            )}
            <DropdownMenuItem onClick={onLogout}>
              <LogOut className="h-4 w-4" />
              로그아웃
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
    </header>
  );
}
