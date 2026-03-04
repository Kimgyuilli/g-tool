import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { MailListView } from "@/features/mail/components/MailListView";
import { MailMessage } from "@/features/mail/types";

describe("MailListView", () => {
  const mockProps = {
    categories: ["업무", "개인", "광고"],
    selectedMailId: null,
    currentPage: 1,
    totalPages: 1,
    onSelectMail: vi.fn(),
    onDragStart: vi.fn(),
    onUpdateCategory: vi.fn(),
    onPrevPage: vi.fn(),
    onNextPage: vi.fn(),
  };

  it("displays skeleton loading when loading is true", () => {
    const { container } = render(
      <MailListView
        {...mockProps}
        loading={true}
        messages={[]}
        total={0}
        classifiedCount={0}
      />
    );

    // Skeleton loading uses animate-pulse divs
    const skeletons = container.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("displays empty message when messages array is empty", () => {
    render(
      <MailListView
        {...mockProps}
        loading={false}
        messages={[]}
        total={0}
        classifiedCount={0}
      />
    );

    expect(screen.getByText("메일이 없습니다.")).toBeInTheDocument();
  });

  it("displays total count and classified count when messages exist", () => {
    const sampleMessages: MailMessage[] = [
      {
        id: 1,
        source: "gmail",
        external_id: "ext1",
        from_email: "test@gmail.com",
        from_name: "Test User",
        subject: "Test Mail",
        to_email: null,
        folder: null,
        received_at: "2026-03-01T10:00:00Z",
        is_read: false,
        classification: {
          classification_id: 1,
          category: "업무",
          confidence: 0.9,
          user_feedback: null,
        },
      },
      {
        id: 2,
        source: "naver",
        external_id: "ext2",
        from_email: "test2@naver.com",
        from_name: "Test User 2",
        subject: "Test Mail 2",
        to_email: null,
        folder: null,
        received_at: "2026-03-01T09:00:00Z",
        is_read: true,
        classification: null,
      },
    ];

    render(
      <MailListView
        {...mockProps}
        loading={false}
        messages={sampleMessages}
        total={10}
        classifiedCount={1}
      />
    );

    expect(screen.getByText("총 10개")).toBeInTheDocument();
    expect(screen.getByText("분류됨 1/2")).toBeInTheDocument();
  });

  it("renders messages when messages array is not empty", () => {
    const sampleMessages: MailMessage[] = [
      {
        id: 1,
        source: "gmail",
        external_id: "ext1",
        from_email: "test@gmail.com",
        from_name: "Test User",
        subject: "Test Subject",
        to_email: null,
        folder: null,
        received_at: "2026-03-01T10:00:00Z",
        is_read: false,
        classification: {
          classification_id: 1,
          category: "업무",
          confidence: 0.9,
          user_feedback: null,
        },
      },
    ];

    render(
      <MailListView
        {...mockProps}
        loading={false}
        messages={sampleMessages}
        total={1}
        classifiedCount={1}
      />
    );

    expect(screen.getByText("Test Subject")).toBeInTheDocument();
  });

  it("does not render pagination when totalPages is 1", () => {
    const sampleMessages: MailMessage[] = [
      {
        id: 1,
        source: "gmail",
        external_id: "ext1",
        from_email: "test@gmail.com",
        from_name: "Test User",
        subject: "Test Mail",
        to_email: null,
        folder: null,
        received_at: "2026-03-01T10:00:00Z",
        is_read: false,
        classification: null,
      },
    ];

    render(
      <MailListView
        {...mockProps}
        loading={false}
        messages={sampleMessages}
        total={1}
        classifiedCount={0}
        totalPages={1}
      />
    );

    expect(screen.queryByRole("button", { name: /이전/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /다음/i })).not.toBeInTheDocument();
  });

  it("renders pagination when totalPages is greater than 1", () => {
    const sampleMessages: MailMessage[] = [
      {
        id: 1,
        source: "gmail",
        external_id: "ext1",
        from_email: "test@gmail.com",
        from_name: "Test User",
        subject: "Test Mail",
        to_email: null,
        folder: null,
        received_at: "2026-03-01T10:00:00Z",
        is_read: false,
        classification: null,
      },
    ];

    render(
      <MailListView
        {...mockProps}
        loading={false}
        messages={sampleMessages}
        total={30}
        classifiedCount={0}
        currentPage={2}
        totalPages={3}
      />
    );

    expect(screen.getByRole("button", { name: /이전/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /다음/i })).toBeInTheDocument();
    expect(screen.getByText("2 / 3")).toBeInTheDocument();
  });
});
