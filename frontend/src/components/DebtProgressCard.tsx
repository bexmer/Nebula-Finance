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
    <div className="flex flex-col justify-between rounded-xl border border-slate-800 bg-slate-900/60 p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">{debt.name}</p>
          <p className="mt-1 text-xs text-slate-400">
            {formatCurrency(debt.current_balance)} restante
          </p>
        </div>
        <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-emerald-300">
          {progress.toFixed(1)}% pagado
        </span>
      </div>
      <div className="mt-4 h-2 w-full overflow-hidden rounded-full bg-slate-800">
        <div
          className="h-full rounded-full bg-emerald-500"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-slate-300">
        <div>
          <p className="font-semibold text-slate-200">Acumulado</p>
          <p>{formatCurrency(paidAmount)}</p>
        </div>
        <div>
          <p className="font-semibold text-slate-200">Total</p>
          <p>{formatCurrency(debt.total_amount)}</p>
        </div>
        {typeof debt.minimum_payment === "number" && (
          <div>
            <p className="font-semibold text-slate-200">Pago mínimo</p>
            <p>{formatCurrency(debt.minimum_payment)}</p>
          </div>
        )}
        {typeof debt.interest_rate === "number" && (
          <div>
            <p className="font-semibold text-slate-200">Tasa anual</p>
            <p>{debt.interest_rate.toFixed(2)}%</p>
          </div>
        )}
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-end gap-3 text-xs">
        <button
          onClick={onEdit}
          className="rounded-full bg-slate-800 px-3 py-1 font-medium text-sky-400 transition hover:bg-slate-700"
        >
          Editar
        </button>
        <button
          onClick={onDelete}
          className="rounded-full bg-slate-800 px-3 py-1 font-medium text-rose-400 transition hover:bg-slate-700"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
