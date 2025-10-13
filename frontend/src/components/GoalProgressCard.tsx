import { Pencil, Trash2 } from "lucide-react";
import { useNumberFormatter } from "../context/DisplayPreferencesContext";

export interface GoalData {
  id: number;
  name: string;
  current_amount: number;
  target_amount: number;
  percentage: number;
}

interface CardProps {
  goal: GoalData;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function GoalProgressCard({ goal, onEdit, onDelete }: CardProps) {
  const progress = Math.min(100, Math.max(0, goal.percentage));
  const { formatCurrency, formatPercent } = useNumberFormatter();

  return (
    <div className="app-card flex h-full flex-col justify-between p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{goal.name}</p>
          <p className="mt-1 text-xs text-muted">
            {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2 text-xs">
          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              aria-label="Editar meta"
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-sky-200 bg-sky-50 text-sky-600 transition hover:bg-sky-100 dark:border-sky-500/50 dark:bg-sky-500/15 dark:text-sky-200"
            >
              <Pencil className="h-4 w-4" />
              <span className="sr-only">Editar meta</span>
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              aria-label="Eliminar meta"
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-rose-200 bg-rose-50 text-rose-600 transition hover:bg-rose-100 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200"
            >
              <Trash2 className="h-4 w-4" />
              <span className="sr-only">Eliminar meta</span>
            </button>
          )}
        </div>
      </div>
      <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-500 to-indigo-500"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="mt-2 text-right text-xs font-medium text-muted">
        {formatPercent(progress)}
      </div>
    </div>
  );
}
