import { useState, useEffect } from "react";
import { Command } from "@tauri-apps/plugin-shell";
import axios from "axios";
import "./App.css";

interface Transaction {
  id: number;
  date: string;
  description: string;
  amount: number;
  type: string;
  category: string;
}

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    // Función para iniciar el backend de Python como un "sidecar"
    const startBackend = async () => {
      try {
        console.log("Iniciando el backend de Python...");
        const command = Command.sidecar("run-backend"); // El nombre del scope de tauri.conf.json

        // Escuchamos la salida del backend para saber qué está pasando
        command.stdout.on("data", (line) => console.log(`[backend]: ${line}`));
        command.stderr.on("data", (line) =>
          console.error(`[backend error]: ${line}`)
        );

        await command.spawn();
        console.log("Comando de inicio del backend enviado.");
      } catch (e) {
        console.error("Error al intentar iniciar el sidecar del backend:", e);
      }
    };

    const fetchTransactions = async (retries = 5) => {
      try {
        console.log("Pidiendo transacciones al backend...");
        const response = await axios.get(
          "http://127.0.0.1:8000/api/transactions"
        );
        setTransactions(response.data);
        console.log("Transacciones recibidas con éxito:", response.data);
      } catch (error) {
        console.error("Error al obtener las transacciones:", error);
        if (retries > 0) {
          console.log(
            `Reintentando en 2 segundos... (${retries} intentos restantes)`
          );
          setTimeout(() => fetchTransactions(retries - 1), 2000);
        }
      }
    };

    startBackend();
    // Damos un tiempo prudencial para que el servidor de Python se levante
    setTimeout(fetchTransactions, 2000);
  }, []);

  return (
    <div className="container">
      <h1>Mis Transacciones</h1>
      <table>
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Descripción</th>
            <th>Monto</th>
            <th>Tipo</th>
            <th>Categoría</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((t) => (
            <tr key={t.id}>
              <td>{t.date}</td>
              <td>{t.description}</td>
              <td
                style={{
                  color: t.type.includes("Gasto") ? "#ff6b6b" : "#69db7c",
                }}
              >
                {t.amount.toFixed(2)}
              </td>
              <td>{t.type}</td>
              <td>{t.category}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
