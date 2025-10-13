interface DebtData {
  id: number;
  name: string;
  current_balance: number;
  total_amount: number;
  percentage: number;
  minimum_payment?: number;
  interest_rate?: number;
}

interface CardProps {
  debt: DebtData;
  onEdit: () => void;
  onDelete: () => void;
}

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    minimumFractionDigits: 2,
  }).format(value || 0);

export function DebtProgressCard({ debt, onEdit, onDelete }: CardProps) {
  const paidAmount = Math.max(debt.total_amount - debt.current_balance, 0);
  const progress = Math.min(100, Math.max(0, debt.percentage));

  return (
    <div className="app-card flex flex-col justify-between p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{debt.name}</p>
          <p className="mt-1 text-xs text-muted">
            {formatCurrency(debt.current_balance)} restante
          </p>
        </div>
        <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-600 dark:border-emerald-500/40 dark:bg-emerald-500/10 dark:text-emerald-200">
          {progress.toFixed(1)}% pagado
        </span>
      </div>
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-sky-500"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-muted">
        <div>
          <p className="font-semibold">Acumulado</p>
          <p>{formatCurrency(paidAmount)}</p>
        </div>
        <div>
          <p className="font-semibold">Total</p>
          <p>{formatCurrency(debt.total_amount)}</p>
        </div>
        {typeof debt.minimum_payment === "number" && (
          <div>
            <p className="font-semibold">Pago mínimo</p>
            <p>{formatCurrency(debt.minimum_payment)}</p>
          </div>
        )}
        {typeof debt.interest_rate === "number" && (
          <div>
            <p className="font-semibold">Tasa anual</p>
            <p>{debt.interest_rate.toFixed(2)}%</p>
          </div>
        )}
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-end gap-3 text-xs">
        <button
          onClick={onEdit}
          className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 font-medium text-sky-600 transition hover:bg-sky-100 dark:border-sky-500/50 dark:bg-sky-500/15 dark:text-sky-200"
        >
          Editar
        </button>
        <button
          onClick={onDelete}
          className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 font-medium text-rose-600 transition hover:bg-rose-100 dark:border-rose-500/40 dark:bg-rose-500/10 dark:text-rose-200"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
