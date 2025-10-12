import { create } from "zustand";
import axios from "axios";

// Define la "forma" de una transacción para usarla en toda la app
export interface Transaction {
  id: number;
  date: string;
  description: string;
  amount: number;
  type: string;
  category: string;
  account_id: number;
  account?: { name: string }; // La cuenta puede ser opcional al crear
  goal_id?: number | null;
  debt_id?: number | null;
}

export interface TransactionFilters {
  search: string;
  start_date: string;
  end_date: string;
  type: string;
  category: string;
  sort_by: string;
}

// Define la "forma" de nuestro almacén de estado global
interface AppState {
  transactions: Transaction[];
  filters: TransactionFilters;
  isTransactionModalOpen: boolean;
  editingTransaction: Transaction | null;
  fetchTransactions: (filters?: TransactionFilters) => Promise<void>;
  setFilters: (filters: Partial<TransactionFilters>) => void;
  openTransactionModal: (transaction: Transaction | null) => void;
  closeTransactionModal: () => void;
}

const defaultFilters: TransactionFilters = {
  search: "",
  start_date: "",
  end_date: "",
  type: "",
  category: "",
  sort_by: "date_desc",
};

export const useStore = create<AppState>((set, get) => ({
  // --- ESTADO INICIAL ---
  transactions: [],
  filters: { ...defaultFilters },
  isTransactionModalOpen: false,
  editingTransaction: null,

  // --- ACCIONES (funciones que modifican el estado) ---
  fetchTransactions: async (filters) => {
    const currentFilters = filters ?? get().filters;
    const filtersForRequest = { ...currentFilters };

    try {
      const params = Object.fromEntries(
        Object.entries(filtersForRequest).filter(([, value]) => value !== "")
      );

      const response = await axios.get<Transaction[]>(
        "http://127.0.0.1:8000/api/transactions",
        { params }
      );

      const updates: Partial<AppState> = {
        transactions: response.data,
      };

      if (filters) {
        updates.filters = filtersForRequest;
      }

      set(updates);
    } catch (error) {
      console.error("Error al obtener las transacciones:", error);
    }
  },

  setFilters: (filters) => {
    const newFilters = { ...get().filters, ...filters };
    set({ filters: newFilters });
  },

  openTransactionModal: (transaction) => {
    set({ isTransactionModalOpen: true, editingTransaction: transaction });
  },

  closeTransactionModal: () => {
    set({ isTransactionModalOpen: false, editingTransaction: null });
  },
}));
