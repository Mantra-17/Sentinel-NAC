import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "ALLOWED" | "BLOCKED" | "QUARANTINED" | "UNKNOWN" | string;
  className?: string;
}

export default function StatusBadge({ status, className }: StatusBadgeProps) {
  const normalizedStatus = status.toUpperCase();

  const styles = {
    ALLOWED: "status-badge-allowed",
    BLOCKED: "status-badge-blocked",
    QUARANTINED: "status-badge-quarantined",
    UNKNOWN: "status-badge-unknown",
  };

  const currentStyle = styles[normalizedStatus as keyof typeof styles] || styles.UNKNOWN;

  return (
    <span className={cn("status-badge inline-flex items-center", currentStyle, className)}>
      <span className={cn("w-1 h-1 rounded-full mr-1.5", 
        normalizedStatus === 'ALLOWED' ? 'bg-cipher' :
        normalizedStatus === 'BLOCKED' ? 'bg-crimson' :
        normalizedStatus === 'QUARANTINED' ? 'bg-amber' : 'bg-white/40'
      )} />
      {normalizedStatus}
    </span>
  );
}
