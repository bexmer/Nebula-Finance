import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface CategoryData {
  category: string;
  amount: number;
}

interface ChartProps {
  title: string;
  data: CategoryData[];
  barColor: string;
}

export function CategoryBarChart({ title, data, barColor }: ChartProps) {
  const chartData = {
    labels: data.map((d) => d.category),
    datasets: [
      {
        label: title,
        data: data.map((d) => d.amount),
        backgroundColor: barColor,
      },
    ],
  };

  const options = {
    indexAxis: "y" as const, // Hace que el gráfico sea horizontal
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: {
        ticks: { color: "#ccc" },
        grid: { color: "rgba(255, 255, 255, 0.1)" },
      },
      y: { ticks: { color: "#ccc" }, grid: { display: false } },
    },
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg h-96">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="h-full pb-8">
        <Bar options={options} data={chartData} />
      </div>
    </div>
  );
}
