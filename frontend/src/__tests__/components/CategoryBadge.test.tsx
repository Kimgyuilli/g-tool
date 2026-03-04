import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CategoryBadge } from "@/features/mail/components/CategoryBadge";

describe("CategoryBadge", () => {
  it("displays category name", () => {
    render(
      <CategoryBadge
        category="업무"
        confidence={0.9}
        userFeedback={null}
        small={false}
      />
    );

    expect(screen.getByText("업무")).toBeInTheDocument();
  });

  it("displays confidence percentage when provided", () => {
    render(
      <CategoryBadge
        category="업무"
        confidence={0.85}
        userFeedback={null}
        small={false}
      />
    );

    expect(screen.getByText("85%")).toBeInTheDocument();
  });

  it("does not display confidence when null", () => {
    render(
      <CategoryBadge
        category="업무"
        confidence={null}
        userFeedback={null}
        small={false}
      />
    );

    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("displays asterisk when userFeedback is provided", () => {
    render(
      <CategoryBadge
        category="업무"
        confidence={0.9}
        userFeedback="개인"
        small={false}
      />
    );

    const asterisk = screen.getByTitle("수동 수정됨");
    expect(asterisk).toBeInTheDocument();
    expect(asterisk).toHaveTextContent("*");
  });

  it("does not display asterisk when userFeedback is null", () => {
    render(
      <CategoryBadge
        category="업무"
        confidence={0.9}
        userFeedback={null}
        small={false}
      />
    );

    expect(screen.queryByTitle("수동 수정됨")).not.toBeInTheDocument();
  });

  it("displays confidence in small mode", () => {
    render(
      <CategoryBadge
        category="업무"
        confidence={0.9}
        userFeedback={null}
        small={true}
      />
    );

    expect(screen.getByText("업무")).toBeInTheDocument();
    expect(screen.getByText("90%")).toBeInTheDocument();
  });
});
