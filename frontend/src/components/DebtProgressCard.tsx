interface DebtData {
  id: number;
  name: string;
  current_balance: number;
  total_amount: number;
  percentage: number;
}

interface CardProps {
  debt: DebtData;
  onEdit: () => void;
  onDelete: () => void;
}

export function DebtProgressCard({ debt, onEdit, onDelete }: CardProps) {
  const paid_amount = debt.total_amount - debt.current_balance;

  return (
    <div className="bg-gray-800 p-4 rounded-lg flex items-center space-x-4">
      <div className="flex-grow">
        <div className="flex justify-between items-center mb-1">
          <span className="font-semibold text-white">{debt.name}</span>
          <span className="text-sm font-medium text-gray-300">
            {debt.percentage.toFixed(1)}% Pagado
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2.5">
          <div
            className="bg-green-500 h-2.5 rounded-full"
            style={{ width: `${debt.percentage}%` }}
          ></div>
        </div>
        <div className="text-right text-xs text-gray-400 mt-1">
          Pagado: ${paid_amount.toFixed(2)} / ${debt.total_amount.toFixed(2)}
        </div>
      </div>
      <div className="flex flex-col space-y-2">
        <button
          onClick={onEdit}
          className="text-blue-400 hover:text-blue-300 text-sm"
        >
          Editar
        </button>
        <button
          onClick={onDelete}
          className="text-red-400 hover:text-red-300 text-sm"
        >
          Eliminar
        </button>
      </div>
    </div>
  );
}
