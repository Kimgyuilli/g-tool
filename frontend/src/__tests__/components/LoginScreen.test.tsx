import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { LoginScreen } from "@/features/auth/components/LoginScreen";

describe("LoginScreen", () => {
  it("renders Mail Organizer title", () => {
    const onLogin = vi.fn();
    render(<LoginScreen onLogin={onLogin} />);

    expect(screen.getByText("Mail Organizer")).toBeInTheDocument();
  });

  it("renders login button", () => {
    const onLogin = vi.fn();
    render(<LoginScreen onLogin={onLogin} />);

    const button = screen.getByRole("button", { name: /Google 계정으로 로그인/i });
    expect(button).toBeInTheDocument();
  });

  it("calls onLogin when button is clicked", () => {
    const onLogin = vi.fn();
    render(<LoginScreen onLogin={onLogin} />);

    const button = screen.getByRole("button", { name: /Google 계정으로 로그인/i });
    fireEvent.click(button);

    expect(onLogin).toHaveBeenCalledTimes(1);
  });
});
