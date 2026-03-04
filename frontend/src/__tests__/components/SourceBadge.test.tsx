import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { SourceBadge } from "@/features/mail/components/SourceBadge";

describe("SourceBadge", () => {
  it("displays G for gmail source", () => {
    render(<SourceBadge source="gmail" small={false} />);

    expect(screen.getByText("G")).toBeInTheDocument();
  });

  it("renders gmail badge with correct styling", () => {
    render(<SourceBadge source="gmail" small={false} />);

    const badge = screen.getByText("G");
    expect(badge).toHaveClass("bg-blue-100");
  });

  it("displays N for naver source", () => {
    render(<SourceBadge source="naver" small={false} />);

    expect(screen.getByText("N")).toBeInTheDocument();
  });

  it("renders naver badge with correct styling", () => {
    render(<SourceBadge source="naver" small={false} />);

    const badge = screen.getByText("N");
    expect(badge).toHaveClass("bg-green-100");
  });

  it("renders in small mode", () => {
    render(<SourceBadge source="gmail" small={true} />);

    expect(screen.getByText("G")).toBeInTheDocument();
    expect(screen.getByText("G")).toHaveClass("w-5", "h-5");
  });
});
