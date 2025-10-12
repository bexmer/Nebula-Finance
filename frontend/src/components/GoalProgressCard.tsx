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

const formatCurrency = (value: number) => {
  const formatter = new Intl.NumberFormat("es-MX", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const sign = value < 0 ? "-" : "";
  return `${sign}$${formatter.format(Math.abs(value))}`;
};

export function GoalProgressCard({ goal, onEdit, onDelete }: CardProps) {
  const progress = Math.min(100, Math.max(0, goal.percentage));

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{goal.name}</p>
          <p className="mt-1 text-xs text-slate-400">
            {formatCurrency(goal.current_amount)} / {formatCurrency(goal.target_amount)}
          </p>
        </div>
        <div className="flex gap-2 text-xs">
          {onEdit && (
            <button
              onClick={onEdit}
              className="rounded-full bg-slate-800 px-3 py-1 font-medium text-sky-400 transition hover:bg-slate-700"
            >
              Editar
            </button>
          )}
          {onDelete && (
            <button
              onClick={onDelete}
              className="rounded-full bg-slate-800 px-3 py-1 font-medium text-rose-400 transition hover:bg-slate-700"
            >
              Eliminar
            </button>
          )}
        </div>
      </div>
      <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-sky-500"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="mt-2 text-right text-xs font-medium text-slate-300">
        {progress.toFixed(1)}%
      </div>
    </div>
  );
}
