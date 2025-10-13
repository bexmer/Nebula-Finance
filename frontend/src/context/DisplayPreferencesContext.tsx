import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import axios from "axios";

import { API_BASE_URL } from "../utils/api";

type DisplayPreferencesState = {
  abbreviateNumbers: boolean;
  threshold: number;
};

type FormatOptions = {
  currency?: string;
  minimumFractionDigits?: number;
  maximumFractionDigits?: number;
  abbreviate?: boolean;
};

type DisplayPreferencesContextValue = {
  preferences: DisplayPreferencesState;
  loading: boolean;
  refresh: () => Promise<void>;
  setPreferences: (prefs: DisplayPreferencesState) => void;
  formatCurrency: (value: number, options?: FormatOptions) => string;
  formatNumber: (value: number, options?: FormatOptions) => string;
};

const DEFAULT_PREFERENCES: DisplayPreferencesState = {
  abbreviateNumbers: false,
  threshold: 1_000_000,
};

const DisplayPreferencesContext = createContext<DisplayPreferencesContextValue>({
  preferences: DEFAULT_PREFERENCES,
  loading: true,
  refresh: async () => undefined,
  setPreferences: () => undefined,
  formatCurrency: (value: number) =>
    new Intl.NumberFormat("es-MX", {
      style: "currency",
      currency: "MXN",
      minimumFractionDigits: 2,
    }).format(value || 0),
  formatNumber: (value: number) =>
    new Intl.NumberFormat("es-MX", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(value || 0),
});

const abbreviateValue = (value: number) => {
  const absolute = Math.abs(value);
  if (absolute >= 1_000_000_000_000) {
    return { value: value / 1_000_000_000_000, suffix: "B" };
  }
  if (absolute >= 1_000_000_000) {
    return { value: value / 1_000_000_000, suffix: "B" };
  }
  if (absolute >= 1_000_000) {
    return { value: value / 1_000_000, suffix: "M" };
  }
  if (absolute >= 1_000) {
    return { value: value / 1_000, suffix: "K" };
  }
  return { value, suffix: "" };
};

export function DisplayPreferencesProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [preferences, setPreferences] = useState<DisplayPreferencesState>(
    DEFAULT_PREFERENCES,
  );
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/config/display`);
      const data = response.data as {
        abbreviate_numbers?: boolean;
        threshold?: number;
      };
      setPreferences({
        abbreviateNumbers: Boolean(data.abbreviate_numbers),
        threshold: Number(data.threshold ?? DEFAULT_PREFERENCES.threshold),
      });
    } catch (error) {
      console.error("No se pudieron cargar las preferencias de visualización:", error);
      setPreferences(DEFAULT_PREFERENCES);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const formatCurrency = useCallback(
    (input: number, options?: FormatOptions) => {
      const value = Number.isFinite(input) ? input : 0;
      const shouldAbbreviate =
        (options?.abbreviate ?? true) &&
        preferences.abbreviateNumbers &&
        Math.abs(value) >= preferences.threshold;

      if (shouldAbbreviate) {
        const { value: abbreviated, suffix } = abbreviateValue(value);
        const formatted = new Intl.NumberFormat("es-MX", {
          style: "currency",
          currency: options?.currency ?? "MXN",
          minimumFractionDigits: options?.minimumFractionDigits ?? 2,
          maximumFractionDigits: options?.maximumFractionDigits ?? 2,
        }).format(abbreviated);
        return `${formatted}${suffix}`;
      }

      return new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency: options?.currency ?? "MXN",
        minimumFractionDigits: options?.minimumFractionDigits ?? 2,
        maximumFractionDigits: options?.maximumFractionDigits ?? 2,
      }).format(value || 0);
    },
    [preferences.abbreviateNumbers, preferences.threshold],
  );

  const formatNumber = useCallback(
    (input: number, options?: FormatOptions) => {
      const value = Number.isFinite(input) ? input : 0;
      const shouldAbbreviate =
        (options?.abbreviate ?? true) &&
        preferences.abbreviateNumbers &&
        Math.abs(value) >= preferences.threshold;

      if (shouldAbbreviate) {
        const { value: abbreviated, suffix } = abbreviateValue(value);
        const formatted = new Intl.NumberFormat("es-MX", {
          minimumFractionDigits: options?.minimumFractionDigits ?? 0,
          maximumFractionDigits: options?.maximumFractionDigits ?? 2,
        }).format(abbreviated);
        return `${formatted}${suffix}`;
      }

      return new Intl.NumberFormat("es-MX", {
        minimumFractionDigits: options?.minimumFractionDigits ?? 0,
        maximumFractionDigits: options?.maximumFractionDigits ?? 2,
      }).format(value || 0);
    },
    [preferences.abbreviateNumbers, preferences.threshold],
  );

  const value = useMemo(
    () => ({
      preferences,
      loading,
      refresh,
      setPreferences,
      formatCurrency,
      formatNumber,
    }),
    [preferences, loading, refresh, formatCurrency, formatNumber],
  );

  return (
    <DisplayPreferencesContext.Provider value={value}>
      {children}
    </DisplayPreferencesContext.Provider>
  );
}

export const useDisplayPreferences = () => useContext(DisplayPreferencesContext);

export const useNumberFormatter = () => {
  const { formatCurrency, formatNumber } = useDisplayPreferences();

  const formatPercent = useCallback((value: number | null | undefined) => {
    if (value === null || value === undefined || !Number.isFinite(value)) {
      return "-";
    }
    const rounded = Number(value.toFixed(1));
    const sign = rounded > 0 ? "+" : "";
    return `${sign}${rounded}%`;
  }, []);

  return { formatCurrency, formatNumber, formatPercent };
};
