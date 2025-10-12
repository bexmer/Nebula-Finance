interface GoalData {
  id: number;
  name: string;
  current_amount: number;
  target_amount: number;
  percentage: number;
}

interface CardProps {
  goal: GoalData;
  onEdit: () => void;
  onDelete: () => void;
}

export function GoalProgressCard({ goal, onEdit, onDelete }: CardProps) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg flex items-center space-x-4">
      <div className="flex-grow">
        <div className="flex justify-between items-center mb-1">
          <span className="font-semibold text-white">{goal.name}</span>
          <span className="text-sm font-medium text-gray-300">
            {goal.percentage.toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2.5">
          <div
            className="bg-blue-500 h-2.5 rounded-full"
            style={{ width: `${goal.percentage}%` }}
          ></div>
        </div>
        <div className="text-right text-xs text-gray-400 mt-1">
          ${goal.current_amount.toFixed(2)} / ${goal.target_amount.toFixed(2)}
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
