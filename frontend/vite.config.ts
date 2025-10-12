import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],

  // Previene que Vite limpie la pantalla de la terminal
  // para que podamos ver los logs del backend y de Tauri.
  clearScreen: false,

  // --- INICIO DE LA CORRECCIÓN ---
  // Le decimos a Vite que se ejecute en el puerto 1420, que es el que Tauri buscará.
  server: {
    port: 1420,
    strictPort: true,
  },
  // --- FIN DE LA CORRECCIÓN ---

  // Configuración de entorno para Tauri
  envPrefix: ['VITE_', 'TAURI_'],
})