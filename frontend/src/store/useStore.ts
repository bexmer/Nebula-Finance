import { create } from "zustand";
import axios from "axios";

import { apiPath } from "../utils/api";

// Define la "forma" de una transacción para usarla en toda la app
export interface TransactionSplit {
  category: string;
  amount: number;
}

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
  goal_name?: string | null;
  debt_name?: string | null;
  budget_entry_id?: number | null;
  budget_entry_name?: string | null;
  is_transfer?: boolean;
  transfer_account_id?: number | null;
  transfer_account_name?: string | null;
  splits?: TransactionSplit[];
  tags?: string[];
}

export interface TransactionPrefill {
  description?: string;
  amount?: number;
  date?: string;
  type?: string;
  category?: string;
  account_id?: number;
  goal_id?: number | null;
  debt_id?: number | null;
  budget_entry_id?: number | null;
}

export interface TransactionFilters {
  search: string;
  start_date: string;
  end_date: string;
  type: string;
  category: string;
  sort_by: string;
  tags: string[];
}

// Define la "forma" de nuestro almacén de estado global
interface AppState {
  transactions: Transaction[];
  filters: TransactionFilters;
  isTransactionModalOpen: boolean;
  editingTransaction: Transaction | null;
  transactionPrefill: TransactionPrefill | null;
  transactionSuccessHandler: (() => Promise<void> | void) | null;
  theme: "light" | "dark";
  sidebarCollapsed: boolean;
  fetchTransactions: (filters?: TransactionFilters) => Promise<void>;
  setFilters: (filters: Partial<TransactionFilters>) => void;
  openTransactionModal: (
    transaction: Transaction | null,
    prefill?: TransactionPrefill | null,
    onSuccess?: (() => Promise<void> | void) | null
  ) => void;
  closeTransactionModal: () => void;
  toggleTheme: () => void;
  setTheme: (theme: "light" | "dark") => void;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

const defaultFilters: TransactionFilters = {
  search: "",
  start_date: "",
  end_date: "",
  type: "",
  category: "",
  sort_by: "date_desc",
  tags: [],
};

export const useStore = create<AppState>((set, get) => ({
  // --- ESTADO INICIAL ---
  transactions: [],
  filters: { ...defaultFilters },
  isTransactionModalOpen: false,
  editingTransaction: null,
  transactionPrefill: null,
  transactionSuccessHandler: null,
  theme:
    (typeof window !== "undefined" &&
      (localStorage.getItem("nebula-theme") as "light" | "dark" | null)) ||
    "dark",
  sidebarCollapsed:
    (typeof window !== "undefined" &&
      localStorage.getItem("nebula-sidebar-collapsed") === "true") ||
    false,

  // --- ACCIONES (funciones que modifican el estado) ---
  fetchTransactions: async (filters) => {
    const currentFilters = filters ?? get().filters;
    const filtersForRequest = { ...currentFilters };

    try {
      const params = Object.fromEntries(
        Object.entries(filtersForRequest)
          .filter(([key, value]) => {
            if (key === "tags") {
              return Array.isArray(value) && value.length > 0;
            }
            return value !== "";
          })
          .map(([key, value]) => {
            if (key === "tags" && Array.isArray(value)) {
              return [key, value.join(",")];
            }
            return [key, value];
          })
      );

      const response = await axios.get<Transaction[]>(apiPath("/transactions"), {
        params,
      });

      const updates: Partial<AppState> = {
        transactions: response.data,
      };

      if (filters) {
        updates.filters = filtersForRequest;
      }

      set(updates);

      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("nebula:transactions-updated"));
      }
    } catch (error) {
      console.error("Error al obtener las transacciones:", error);
    }
  },

  setFilters: (filters) => {
    const newFilters = { ...get().filters, ...filters };
    set({ filters: newFilters });
  },

  openTransactionModal: (transaction, prefill = null, onSuccess = null) => {
    set({
      isTransactionModalOpen: true,
      editingTransaction: transaction,
      transactionPrefill: prefill,
      transactionSuccessHandler: onSuccess,
    });
  },

  closeTransactionModal: () => {
    set({
      isTransactionModalOpen: false,
      editingTransaction: null,
      transactionPrefill: null,
      transactionSuccessHandler: null,
    });
  },
  toggleTheme: () => {
    const nextTheme = get().theme === "dark" ? "light" : "dark";
    if (typeof window !== "undefined") {
      localStorage.setItem("nebula-theme", nextTheme);
    }
    set({ theme: nextTheme });
  },
  setTheme: (theme) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("nebula-theme", theme);
    }
    set({ theme });
  },
  toggleSidebar: () => {
    set((state) => {
      const next = !state.sidebarCollapsed;
      if (typeof window !== "undefined") {
        localStorage.setItem("nebula-sidebar-collapsed", String(next));
      }
      return { sidebarCollapsed: next };
    });
  },
  setSidebarCollapsed: (collapsed) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("nebula-sidebar-collapsed", String(collapsed));
    }
    set({ sidebarCollapsed: collapsed });
  },
}));
