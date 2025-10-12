interface KpiCardProps {
  title: string;
  value: string;
}

export function KpiCard({ title, value }: KpiCardProps) {
  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h3 className="text-sm font-medium text-gray-400">{title}</h3>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
    </div>
  );
}
