import { Tooltip } from "@/components/ui/tooltip";

interface SourceBadgeProps {
  source: "gmail" | "naver";
  small?: boolean;
}

export function SourceBadge({ source, small }: SourceBadgeProps) {
  const isGmail = source === "gmail";
  const bgColor = isGmail
    ? "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300"
    : "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300";
  const sizeClass = small ? "w-5 h-5 text-[10px]" : "w-6 h-6 text-xs";
  const label = isGmail ? "G" : "N";

  return (
    <Tooltip content={isGmail ? "Gmail" : "네이버"}>
      <span
        className={`inline-flex items-center justify-center rounded-full font-bold ${bgColor} ${sizeClass}`}
      >
        {label}
      </span>
    </Tooltip>
  );
}
