import { create } from 'zustand';
import axios from 'axios';

// Define la "forma" de una transacción para usarla en toda la app
export interface Transaction {
    id: number;
    date: string;
    description: string;
    amount: number;
    type: string;
    category: string;
    account_id: number;
    goal_id?: number | null;
    debt_id?: number | null;
}

// Define la "forma" de nuestro almacén de estado global
interface AppState {
    transactions: Transaction[];
    isTransactionModalOpen: boolean;
    editingTransaction: Transaction | null;
    fetchTransactions: () => Promise<void>;
    openTransactionModal: (transaction: Transaction | null) => void;
    closeTransactionModal: () => void;
}

export const useStore = create<AppState>((set) => ({
    // --- ESTADO INICIAL ---
    transactions: [],
    isTransactionModalOpen: false,
    editingTransaction: null,

    // --- ACCIONES (funciones que modifican el estado) ---
    fetchTransactions: async () => {
        try {
            const response = await axios.get('http://127.0.0.1:8000/api/transactions');
            set({ transactions: response.data });
        } catch (error) {
            console.error("Error al obtener las transacciones:", error);
        }
    },

    openTransactionModal: (transaction) => {
        set({ isTransactionModalOpen: true, editingTransaction: transaction });
    },

    closeTransactionModal: () => {
        set({ isTransactionModalOpen: false, editingTransaction: null });
    },
}));