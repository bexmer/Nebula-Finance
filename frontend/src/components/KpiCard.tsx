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
    ? "text-slate-400"
    : isImprovement === null
    ? "text-slate-400"
    : isImprovement
    ? "text-emerald-400"
    : "text-rose-400";

  const trendIcon = !hasComparison ? (
    <Minus className="h-4 w-4" />
  ) : isPositive ? (
    <ArrowUpRight className="h-4 w-4" />
  ) : (
    <ArrowDownRight className="h-4 w-4" />
  );

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 p-6 backdrop-blur">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
        </div>
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-sky-500/10 text-sky-400">
          {icon}
        </div>
      </div>
      <div className="mt-5 flex items-center gap-3 text-sm">
        <span className={`inline-flex items-center gap-1 font-medium ${iconColorClass}`}>
          {trendIcon}
          {formatPercentage(comparison)}
        </span>
        <span className="text-slate-500">{comparisonLabel}</span>
      </div>
    </div>
  );
}
