import { ReactNode } from "react";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

type KpiCardVariant = "slate" | "emerald" | "rose" | "indigo";

interface KpiCardProps {
  title: string;
  value: string;
  comparison?: number | null;
  comparisonLabel?: string;
  inverse?: boolean;
  icon: ReactNode;
  variant?: KpiCardVariant;
}

const VARIANT_STYLES: Record<
  KpiCardVariant,
  {
    card: string;
    title: string;
    value: string;
    iconWrapper: string;
    neutral: string;
    positive: string;
    negative: string;
    badgeBg: string;
    badgeText: string;
  }
> = {
  slate: {
    card: "app-card relative overflow-hidden p-6",
    title: "text-sm font-medium text-muted",
    value: "mt-3 text-3xl font-semibold text-slate-900 dark:text-slate-100",
    iconWrapper:
      "flex h-12 w-12 items-center justify-center rounded-full bg-sky-100 text-sky-500 dark:bg-sky-500/15 dark:text-sky-300",
    neutral: "text-muted",
    positive: "text-emerald-500 dark:text-emerald-400",
    negative: "text-rose-500 dark:text-rose-400",
    badgeBg: "bg-white/50 dark:bg-white/10",
    badgeText: "text-slate-900 dark:text-slate-100",
  },
  emerald: {
    card:
      "relative overflow-hidden rounded-2xl border border-emerald-200/70 bg-gradient-to-br from-emerald-400 via-emerald-500 to-emerald-600 p-6 text-emerald-50 shadow-xl shadow-emerald-500/30 dark:border-emerald-500/40",
    title: "text-sm font-semibold uppercase tracking-wide text-emerald-50/80",
    value: "mt-3 text-3xl font-semibold text-white",
    iconWrapper:
      "flex h-12 w-12 items-center justify-center rounded-full bg-white/20 text-white",
    neutral: "text-emerald-50/80",
    positive: "text-white",
    negative: "text-white",
    badgeBg: "bg-white/20",
    badgeText: "text-white",
  },
  rose: {
    card:
      "relative overflow-hidden rounded-2xl border border-rose-200/70 bg-gradient-to-br from-rose-400 via-orange-400 to-rose-500 p-6 text-rose-50 shadow-xl shadow-rose-500/30 dark:border-rose-500/40",
    title: "text-sm font-semibold uppercase tracking-wide text-rose-50/80",
    value: "mt-3 text-3xl font-semibold text-white",
    iconWrapper:
      "flex h-12 w-12 items-center justify-center rounded-full bg-white/20 text-white",
    neutral: "text-rose-50/80",
    positive: "text-white",
    negative: "text-white",
    badgeBg: "bg-white/20",
    badgeText: "text-white",
  },
  indigo: {
    card:
      "relative overflow-hidden rounded-2xl border border-indigo-200/70 bg-gradient-to-br from-sky-400 via-indigo-500 to-indigo-600 p-6 text-indigo-50 shadow-xl shadow-indigo-500/30 dark:border-indigo-500/40",
    title: "text-sm font-semibold uppercase tracking-wide text-indigo-50/80",
    value: "mt-3 text-3xl font-semibold text-white",
    iconWrapper:
      "flex h-12 w-12 items-center justify-center rounded-full bg-white/20 text-white",
    neutral: "text-indigo-50/80",
    positive: "text-white",
    negative: "text-white",
    badgeBg: "bg-white/20",
    badgeText: "text-white",
  },
};

export function KpiCard({
  title,
  value,
  comparison,
  comparisonLabel = "vs. período anterior",
  inverse = false,
  icon,
  variant = "slate",
}: KpiCardProps) {
  const { formatPercent } = useNumberFormatter();
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

  const styles = VARIANT_STYLES[variant];
  const trendColorClass = !hasComparison
    ? styles.neutral
    : isImprovement === null
    ? styles.neutral
    : isImprovement
    ? styles.positive
    : styles.negative;

  const trendIcon = !hasComparison ? (
    <Minus className="h-4 w-4" />
  ) : isPositive ? (
    <ArrowUpRight className="h-4 w-4" />
  ) : (
    <ArrowDownRight className="h-4 w-4" />
  );

  return (
    <div className={styles.card}>
      <div className="flex items-start justify-between">
        <div>
          <p className={styles.title}>{title}</p>
          <p className={styles.value}>{value}</p>
        </div>
        <div className={styles.iconWrapper}>
          {icon}
        </div>
      </div>
      <div className="mt-5 flex items-center gap-3 text-sm">
        <span
          className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold ${styles.badgeBg} ${styles.badgeText} ${trendColorClass}`}
        >
          {trendIcon}
          {formatPercent(comparison ?? null)}
        </span>
        <span className={`text-xs ${styles.neutral}`}>{comparisonLabel}</span>
      </div>
    </div>
  );
}
