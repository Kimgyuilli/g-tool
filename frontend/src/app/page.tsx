"use client";

import { useState } from "react";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { useMessages } from "@/features/mail/hooks/useMessages";
import { useCategoryCounts } from "@/features/mail/hooks/useCategoryCounts";
import { useFeedbackStats } from "@/features/mail/hooks/useFeedbackStats";
import { useMailActions } from "@/features/mail/hooks/useMailActions";
import { useNaverConnect } from "@/features/auth/hooks/useNaverConnect";
import { useDragAndDrop } from "@/features/mail/hooks/useDragAndDrop";
import { LoginScreen } from "@/features/auth/components/LoginScreen";
import { MailDetailView } from "@/features/mail/components/MailDetailView";
import { AppHeader } from "@/components/AppHeader";
import { NaverConnectModal } from "@/features/auth/components/NaverConnectModal";
import { CategorySidebar } from "@/features/mail/components/CategorySidebar";
import { MailListView } from "@/features/mail/components/MailListView";
import { CalendarPage } from "@/features/calendar/CalendarPage";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";

const LIMIT = 20;

export default function Home() {
  const { userId, hydrated, userInfo, setUserInfo, categories, handleLogin, handleLogout } = useAuth();
  const [activePage, setActivePage] = useState<"mail" | "calendar">("mail");
  const [sourceFilter, setSourceFilter] = useState<"all" | "gmail" | "naver">("all");
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null);
  const [showSenderRules, setShowSenderRules] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const { messages, setMessages, total, setTotal, offset, setOffset, loading, loadMessages } =
    useMessages({ userId, sourceFilter, categoryFilter, limit: LIMIT });

  const { categoryCounts, loadCategoryCounts } = useCategoryCounts({ userId, sourceFilter });
  const { feedbackStats, loadFeedbackStats } = useFeedbackStats({ userId });

  const {
    syncing,
    classifying,
    applyingLabels,
    selectedMail,
    setSelectedMail,
    handleSync,
    handleClassify,
    handleApplyLabels,
    handleUpdateCategory,
    handleSelectMail,
  } = useMailActions({
    userId,
    userInfo,
    sourceFilter,
    messages,
    setMessages,
    loadMessages,
    loadCategoryCounts,
    loadFeedbackStats,
  });

  const {
    showNaverConnect,
    setShowNaverConnect,
    naverEmail,
    setNaverEmail,
    naverPassword,
    setNaverPassword,
    connectingNaver,
    handleConnectNaver,
    closeNaverConnect,
  } = useNaverConnect({ userId, setUserInfo, loadCategoryCounts });

  const { dragOverCategory, setDragOverCategory, handleDrop } = useDragAndDrop({
    userId,
    sourceFilter,
    categoryFilter,
    offset,
    limit: LIMIT,
    handleUpdateCategory,
    setMessages,
    setTotal,
    loadMessages,
    loadCategoryCounts,
  });

  const handleCategoryFilter = (cat: string | null) => {
    setCategoryFilter(cat);
    setOffset(0);
  };

  const onLogout = () => {
    handleLogout();
    setMessages([]);
    setSelectedMail(null);
  };

  const handleSourceFilterChange = (src: "all" | "gmail" | "naver") => {
    setSourceFilter(src);
    setOffset(0);
  };

  const handleDragStart = (e: React.DragEvent, mailId: number, classificationId: number | null) => {
    e.dataTransfer.setData("mailId", String(mailId));
    e.dataTransfer.setData("classificationId", classificationId ? String(classificationId) : "");
    e.dataTransfer.effectAllowed = "move";
  };

  // Wait for client-side hydration
  if (!hydrated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Skeleton className="h-8 w-48" />
      </div>
    );
  }

  if (!userId) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  const totalPages = Math.ceil(total / LIMIT);
  const currentPage = Math.floor(offset / LIMIT) + 1;
  const classifiedCount = messages.filter((m) => m.classification).length;

  const sidebarContent = (
    <CategorySidebar
      categoryCounts={categoryCounts}
      categoryFilter={categoryFilter}
      feedbackStats={feedbackStats}
      showSenderRules={showSenderRules}
      dragOverCategory={dragOverCategory}
      onCategoryFilter={(cat) => {
        handleCategoryFilter(cat);
        setMobileMenuOpen(false);
      }}
      onToggleSenderRules={() => setShowSenderRules(!showSenderRules)}
      onDragOver={(cat) => setDragOverCategory(cat)}
      onDragLeave={() => setDragOverCategory(null)}
      onDrop={handleDrop}
    />
  );

  return (
    <div className="flex h-screen flex-col bg-background">
      <AppHeader
        activePage={activePage}
        onPageChange={setActivePage}
        userInfo={userInfo}
        sourceFilter={sourceFilter}
        syncing={syncing}
        classifying={classifying}
        applyingLabels={applyingLabels}
        classifiedCount={classifiedCount}
        onSync={handleSync}
        onClassify={handleClassify}
        onApplyLabels={handleApplyLabels}
        onLogout={onLogout}
        onNaverConnect={() => setShowNaverConnect(true)}
        onSourceFilterChange={handleSourceFilterChange}
        onMobileMenuToggle={() => setMobileMenuOpen(true)}
      />

      {activePage === "mail" && (
        <>
          {/* Mobile sidebar sheet */}
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetContent side="left" className="w-64 p-0">
              <SheetTitle className="sr-only">카테고리 메뉴</SheetTitle>
              {sidebarContent}
            </SheetContent>
          </Sheet>

          <NaverConnectModal
            open={showNaverConnect}
            naverEmail={naverEmail}
            naverPassword={naverPassword}
            connecting={connectingNaver}
            onEmailChange={setNaverEmail}
            onPasswordChange={setNaverPassword}
            onConnect={handleConnectNaver}
            onClose={closeNaverConnect}
          />

          {/* 3-panel layout */}
          <div className="flex-1 overflow-hidden flex">
            {/* Sidebar - separate from ResizablePanelGroup to avoid className issues */}
            <aside className="hidden md:flex w-56 shrink-0 border-r overflow-auto">
              {sidebarContent}
            </aside>

            <ResizablePanelGroup orientation="horizontal" className="flex-1">

              {/* Mail list panel */}
              <ResizablePanel
                defaultSize={selectedMail ? 50 : 100}
                minSize={30}
              >
                <MailListView
                  loading={loading}
                  messages={messages}
                  total={total}
                  categories={categories}
                  selectedMailId={selectedMail?.id ?? null}
                  classifiedCount={classifiedCount}
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onSelectMail={handleSelectMail}
                  onDragStart={handleDragStart}
                  onUpdateCategory={handleUpdateCategory}
                  onPrevPage={() => setOffset(Math.max(0, offset - LIMIT))}
                  onNextPage={() => setOffset(offset + LIMIT)}
                />
              </ResizablePanel>

              {/* Detail panel - shown when mail selected */}
              {selectedMail && (
                <>
                  <ResizableHandle withHandle />
                  <ResizablePanel defaultSize={50} minSize={30}>
                    <MailDetailView
                      mail={selectedMail}
                      categories={categories}
                      onBack={() => setSelectedMail(null)}
                      onUpdateCategory={handleUpdateCategory}
                    />
                  </ResizablePanel>
                </>
              )}
            </ResizablePanelGroup>
          </div>
        </>
      )}

      {activePage === "calendar" && (
        <CalendarPage userId={userId} />
      )}
    </div>
  );
}
