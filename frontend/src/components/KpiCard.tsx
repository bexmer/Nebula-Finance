import { ReactNode } from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string;
  comparison?: number | null;
  comparisonLabel?: string;
  inverse?: boolean;
  icon: ReactNode;
}

const formatPercentage = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "Sin datos";
  }
  const rounded = Number(value.toFixed(1));
  const sign = rounded > 0 ? "+" : "";
  return `${sign}${rounded}%`;
};

export function KpiCard({
  title,
  value,
  comparison,
  comparisonLabel = "vs. período anterior",
  inverse = false,
  icon,
}: KpiCardProps) {
  const hasComparison = comparison !== null && comparison !== undefined && !Number.isNaN(comparison);
  const isPositive = hasComparison && (comparison as number) > 0;
  const isNegative = hasComparison && (comparison as number) < 0;

  let isImprovement: boolean | null = null;
  if (hasComparison) {
    if (inverse) {
      isImprovement = isNegative;
    } else {
      isImprovement = isPositive;
    }
  }

  const iconColorClass = !hasComparison
    ? "text-muted"
    : isImprovement === null
    ? "text-muted"
    : isImprovement
    ? "text-emerald-500 dark:text-emerald-400"
    : "text-rose-500 dark:text-rose-400";

  const trendIcon = !hasComparison ? (
    <Minus className="h-4 w-4" />
  ) : isPositive ? (
    <ArrowUpRight className="h-4 w-4" />
  ) : (
    <ArrowDownRight className="h-4 w-4" />
  );

  return (
    <div className="app-card relative overflow-hidden p-6">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-muted">{title}</p>
          <p className="mt-3 text-3xl font-semibold">{value}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sky-100 text-sky-500 dark:bg-sky-500/15 dark:text-sky-300">
          {icon}
        </div>
      </div>
      <div className="mt-5 flex items-center gap-3 text-sm">
        <span className={`inline-flex items-center gap-1 font-medium ${iconColorClass}`}>
          {trendIcon}
          {formatPercentage(comparison)}
        </span>
        <span className="text-muted">{comparisonLabel}</span>
      </div>
    </div>
  );
}
