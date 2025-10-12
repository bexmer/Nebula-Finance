import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ChartData {
  labels: string[];
  income_data: number[];
  expense_data: number[];
}

interface ChartProps {
  data: ChartData;
}

export function IncomeExpenseChart({ data }: ChartProps) {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: "Ingresos",
        data: data.income_data,
        borderColor: "rgb(54, 162, 235)",
        backgroundColor: "rgba(54, 162, 235, 0.5)",
        tension: 0.2,
      },
      {
        label: "Gastos",
        data: data.expense_data,
        borderColor: "rgb(255, 99, 132)",
        backgroundColor: "rgba(255, 99, 132, 0.5)",
        tension: 0.2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
        labels: { color: "#ccc" },
      },
      title: {
        display: false,
      },
    },
    scales: {
      x: {
        ticks: { color: "#ccc" },
        grid: { color: "rgba(255, 255, 255, 0.1)" },
      },
      y: {
        ticks: { color: "#ccc" },
        grid: { color: "rgba(255, 255, 255, 0.1)" },
      },
    },
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg h-96">
      <h3 className="text-lg font-semibold mb-4">
        Ingresos vs. Gastos (Últimos 12 Meses)
      </h3>
      <div className="h-full pb-8">
        <Line options={options} data={chartData} />
      </div>
    </div>
  );
}
