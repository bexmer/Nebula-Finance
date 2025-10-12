import { useState, useEffect } from "react";
import axios from "axios";

interface SettingsData {
  currency_symbol: string;
  decimal_places: number;
  theme: string;
}

export function Settings() {
  const [settings, setSettings] = useState<SettingsData | null>(null);
  const [statusMessage, setStatusMessage] = useState("");

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/settings");
        setSettings(response.data);
      } catch (error) {
        console.error("Error al obtener la configuración:", error);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async () => {
    if (!settings) return;
    try {
      const response = await axios.post(
        "http://127.0.0.1:8000/api/settings",
        settings
      );
      setStatusMessage(response.data.message);
      // Ocultar el mensaje después de 3 segundos
      setTimeout(() => setStatusMessage(""), 3000);
    } catch (error) {
      setStatusMessage("Error al guardar.");
      setTimeout(() => setStatusMessage(""), 3000);
      console.error("Error al guardar la configuración:", error);
    }
  };

  if (!settings) {
    return <p>Cargando configuración...</p>;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Configuración</h1>

      <div className="bg-gray-800 p-6 rounded-lg shadow-lg max-w-md">
        <div className="space-y-4">
          <div>
            <label
              htmlFor="currency"
              className="block text-sm font-medium text-gray-300"
            >
              Símbolo de Moneda
            </label>
            <input
              id="currency"
              type="text"
              value={settings.currency_symbol}
              onChange={(e) =>
                setSettings({ ...settings, currency_symbol: e.target.value })
              }
              className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label
              htmlFor="theme"
              className="block text-sm font-medium text-gray-300"
            >
              Tema
            </label>
            <select
              id="theme"
              value={settings.theme}
              onChange={(e) =>
                setSettings({ ...settings, theme: e.target.value })
              }
              className="mt-1 block w-full bg-gray-700 border border-gray-600 rounded-md shadow-sm py-2 px-3 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="dark">Oscuro</option>
              <option value="light">Claro</option>
            </select>
          </div>
        </div>
        <div className="mt-6">
          <button
            onClick={handleSave}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md transition-colors"
          >
            Guardar Cambios
          </button>
          {statusMessage && (
            <p className="text-center mt-4 text-green-400">{statusMessage}</p>
          )}
        </div>
      </div>
    </div>
  );
}
