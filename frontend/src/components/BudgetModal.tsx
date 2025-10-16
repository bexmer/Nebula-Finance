import { useCallback, useEffect, useMemo, useState } from "react";
import type { ChangeEvent, CSSProperties, FormEvent } from "react";
import Modal from "react-modal";
import axios from "axios";
import {
  AlertCircle,
  CalendarDays,
  Clock,
  FileText,
  Loader2,
  Tag,
  Type as TypeIcon,
} from "lucide-react";

import { apiPath } from "../utils/api";
import {
  getTodayDateInputValue,
  normalizeDateInputValue,
} from "../utils/date";

Modal.setAppElement("#root");

interface BudgetEntry {
  id?: number;
  category: string;
  budgeted_amount: number;
  type: string;
  frequency: string;
  description?: string;
  due_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  month?: number | null;
  year?: number | null;
  goal_id?: number | null;
  goal_name?: string | null;
  debt_id?: number | null;
  debt_name?: string | null;
  is_recurring: boolean;
  use_custom_schedule?: boolean;
}

interface ParameterOption {
  id: number;
  value: string;
}

interface SelectOption {
  id: number;
  name: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: () => void;
  entry: BudgetEntry | null;
}

interface BudgetFormState {
  description: string;
  amount: string;
  referenceMonth: string;
  referenceYear: string;
  start_date: string;
  due_date: string;
  typeId: string;
  typeValue: string;
  categoryValue: string;
  goalId: string;
  debtId: string;
  frequency: string;
  is_recurring: boolean;
  use_custom_schedule: boolean;
}

const createEmptyForm = (): BudgetFormState => {
  const today = new Date();
  const monthValue = String(today.getMonth() + 1).padStart(2, "0");
  const yearValue = String(today.getFullYear());

  return {
    description: "",
    amount: "",
    referenceMonth: monthValue,
    referenceYear: yearValue,
    start_date: getTodayDateInputValue(),
    due_date: getTodayDateInputValue(),
    typeId: "",
    typeValue: "",
    categoryValue: "",
    goalId: "",
    debtId: "",
    frequency: "Mensual",
    is_recurring: true,
    use_custom_schedule: false,
  };
};

const normalizeTypeLabel = (value: string) =>
  value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

const MONTH_OPTIONS = [
  { value: "01", label: "Enero" },
  { value: "02", label: "Febrero" },
  { value: "03", label: "Marzo" },
  { value: "04", label: "Abril" },
  { value: "05", label: "Mayo" },
  { value: "06", label: "Junio" },
  { value: "07", label: "Julio" },
  { value: "08", label: "Agosto" },
  { value: "09", label: "Septiembre" },
  { value: "10", label: "Octubre" },
  { value: "11", label: "Noviembre" },
  { value: "12", label: "Diciembre" },
];

const buildYearOptions = () => {
  const currentYear = new Date().getFullYear();
  const startYear = currentYear - 1;
  return Array.from({ length: 6 }, (_, index) => {
    const value = String(startYear + index);
    return { value, label: value };
  });
};

const computeAutoPeriod = (
  frequency: string,
  monthValue: string,
  yearValue: string
): { start: Date; end: Date } | null => {
  const monthNumber = Number.parseInt(monthValue, 10);
  const yearNumber = Number.parseInt(yearValue, 10);

  if (Number.isNaN(monthNumber) || Number.isNaN(yearNumber)) {
    return null;
  }

  const monthIndex = Math.max(0, Math.min(11, monthNumber - 1));
  const start = new Date(yearNumber, monthIndex, 1);
  const normalizedFrequency = frequency?.toLowerCase?.() ?? "";

  if (normalizedFrequency.includes("única") || normalizedFrequency.includes("unica")) {
    return { start, end: new Date(start) };
  }

  if (normalizedFrequency.includes("semanal")) {
    const end = new Date(start);
    end.setDate(end.getDate() + 6);
    return { start, end };
  }

  if (normalizedFrequency.includes("quincenal")) {
    const end = new Date(start);
    end.setDate(end.getDate() + 13);
    return { start, end };
  }

  if (normalizedFrequency.includes("anual")) {
    const end = new Date(yearNumber + 1, monthIndex, 1);
    end.setDate(end.getDate() - 1);
    return { start, end };
  }

  const end = new Date(yearNumber, monthIndex + 1, 0);
  return { start, end };
};

const formatDateForDisplay = (date: Date) =>
  date.toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

export function BudgetModal({ isOpen, onClose, onSave, entry }: ModalProps) {
  const [formData, setFormData] = useState<BudgetFormState>(createEmptyForm());
  const [initialSnapshot, setInitialSnapshot] = useState<BudgetFormState | null>(
    null
  );
  const [transactionTypes, setTransactionTypes] = useState<ParameterOption[]>([]);
  const [categories, setCategories] = useState<ParameterOption[]>([]);
  const [goals, setGoals] = useState<SelectOption[]>([]);
  const [debts, setDebts] = useState<SelectOption[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogNotice, setCatalogNotice] = useState<string | null>(null);
  const yearOptions = useMemo(buildYearOptions, []);

  const sortedCategories = useMemo(
    () =>
      categories.slice().sort((a, b) => a.value.localeCompare(b.value, "es")),
    [categories]
  );

  const automaticPeriodPreview = useMemo(() => {
    if (formData.use_custom_schedule) {
      return null;
    }
    const period = computeAutoPeriod(
      formData.frequency,
      formData.referenceMonth,
      formData.referenceYear
    );
    if (!period) {
      return null;
    }
    return {
      startLabel: formatDateForDisplay(period.start),
      endLabel: formatDateForDisplay(period.end),
      startInput: normalizeDateInputValue(period.start),
      endInput: normalizeDateInputValue(period.end),
    };
  }, [
    formData.frequency,
    formData.referenceMonth,
    formData.referenceYear,
    formData.use_custom_schedule,
  ]);

  const activeType = useMemo(() => {
    if (!formData.typeId) {
      return null;
    }
    const typeIdNumber = Number(formData.typeId);
    return transactionTypes.find((type) => type.id === typeIdNumber) ?? null;
  }, [formData.typeId, transactionTypes]);

  const normalizedTypeName = useMemo(() => {
    if (!activeType) {
      return "";
    }
    return normalizeTypeLabel(activeType.value);
  }, [activeType]);

  const requiresGoal = normalizedTypeName.includes("ahorro");
  const requiresDebt = normalizedTypeName.includes("deuda");
  const shouldShowGoalSelect = requiresGoal || Boolean(formData.goalId);
  const shouldShowDebtSelect = requiresDebt || Boolean(formData.debtId);

  const fetchCategoriesByType = useCallback(async (typeId: number) => {
    try {
      const response = await axios.get<ParameterOption[]>(
        apiPath(`/parameters/categories/${typeId}`)
      );
      return response.data;
    } catch (categoryError) {
      console.error("No se pudieron cargar las categorías:", categoryError);
      setCatalogNotice(
        "No encontramos categorías para este tipo. Revisa la sección de Configuración."
      );
      return [];
    }
  }, []);

  const resolveStartDate = (record: BudgetEntry | null) => {
    if (!record) {
      return getTodayDateInputValue();
    }
    if (record.start_date) {
      return normalizeDateInputValue(record.start_date);
    }
    if (record.due_date) {
      return normalizeDateInputValue(record.due_date);
    }
    if (record.year && record.month) {
      const normalized = new Date(record.year, record.month - 1, 1);
      return normalizeDateInputValue(normalized);
    }
    return getTodayDateInputValue();
  };

  const resolveDueDate = (record: BudgetEntry | null) => {
    if (!record) {
      return getTodayDateInputValue();
    }
    if (record.due_date) {
      return normalizeDateInputValue(record.due_date);
    }
    if (record.end_date) {
      return normalizeDateInputValue(record.end_date);
    }
    if (record.year && record.month) {
      const normalized = new Date(record.year, record.month - 1, 1);
      return normalizeDateInputValue(normalized);
    }
    return resolveStartDate(record);
  };

  const loadModalData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setCatalogNotice(null);

    try {
      const [typesResponse, goalsResponse, debtsResponse] = await Promise.all([
        axios.get<ParameterOption[]>(apiPath("/parameters/transaction-types")),
        axios.get<SelectOption[]>(apiPath("/goals")),
        axios.get<SelectOption[]>(apiPath("/debts")),
      ]);

      const typeOptions = typesResponse.data;
      const goalOptions = goalsResponse.data.map((goal) => ({
        id: goal.id,
        name: goal.name,
      }));
      const debtOptions = debtsResponse.data.map((debt) => ({
        id: debt.id,
        name: debt.name,
      }));

      if (typeOptions.length === 0) {
        throw new Error("missing-types");
      }

      let selectedType = entry?.type ?? typeOptions[0].value;
      const matchedType = typeOptions.find((type) => type.value === selectedType);
      const fallbackType = matchedType ?? typeOptions[0];

      const categoryOptions = await fetchCategoriesByType(fallbackType.id);
      let nextCategories = categoryOptions;

      if (
        entry?.category &&
        !categoryOptions.some((option) => option.value === entry.category)
      ) {
        nextCategories = [
          ...categoryOptions,
          { id: -1, value: entry.category },
        ];
      }

      setTransactionTypes(typeOptions);
      setGoals(goalOptions);
      setDebts(debtOptions);
      setCategories(nextCategories);

      const amountValue = entry ? String(entry.budgeted_amount ?? 0) : "";
      const startDateValue = resolveStartDate(entry);
      const dueDateValue = resolveDueDate(entry);
      const frequencyValue = entry?.frequency ?? "Mensual";
      const isRecurringValue =
        frequencyValue === "Única vez"
          ? false
          : entry?.is_recurring ?? true;
      const manualSchedule = Boolean(entry?.use_custom_schedule);
      const defaultBlank = createEmptyForm();

      let referenceMonth = defaultBlank.referenceMonth;
      let referenceYear = defaultBlank.referenceYear;

      if (entry?.month && entry?.year) {
        referenceMonth = String(entry.month).padStart(2, "0");
        referenceYear = String(entry.year);
      } else if (dueDateValue) {
        referenceMonth = dueDateValue.slice(5, 7) || defaultBlank.referenceMonth;
        referenceYear = dueDateValue.slice(0, 4) || defaultBlank.referenceYear;
      }

      setFormData({
        description: entry?.description ?? "",
        amount: amountValue,
        referenceMonth,
        referenceYear,
        start_date: startDateValue,
        due_date: dueDateValue,
        typeId: String(fallbackType.id),
        typeValue: fallbackType.value,
        categoryValue: entry?.category ?? (nextCategories[0]?.value ?? ""),
        goalId: entry?.goal_id ? String(entry.goal_id) : "",
        debtId: entry?.debt_id ? String(entry.debt_id) : "",
        frequency: frequencyValue,
        is_recurring: isRecurringValue,
        use_custom_schedule: manualSchedule,
      });
      setInitialSnapshot({
        description: entry?.description ?? "",
        amount: amountValue,
        referenceMonth,
        referenceYear,
        start_date: startDateValue,
        due_date: dueDateValue,
        typeId: String(fallbackType.id),
        typeValue: fallbackType.value,
        categoryValue: entry?.category ?? (nextCategories[0]?.value ?? ""),
        goalId: entry?.goal_id ? String(entry.goal_id) : "",
        debtId: entry?.debt_id ? String(entry.debt_id) : "",
        frequency: frequencyValue,
        is_recurring: isRecurringValue,
        use_custom_schedule: manualSchedule,
      });

      const normalizedDefault = normalizeTypeLabel(fallbackType.value);
      if (normalizedDefault.includes("ahorro") && goalOptions.length === 0) {
        setCatalogNotice(
          "Para planear un ahorro necesitas crear una meta desde la sección Metas y deudas."
        );
      } else if (normalizedDefault.includes("deuda") && debtOptions.length === 0) {
        setCatalogNotice(
          "Para planear un pago de deuda necesitas registrar una deuda en Metas y deudas."
        );
      }

      if (categoryOptions.length === 0) {
        setCatalogNotice(
          "Configura categorías para este tipo de transacción en la sección de Configuración."
        );
      }
    } catch (loadError) {
      console.error("Error al preparar el formulario de presupuesto:", loadError);
      if (loadError instanceof Error && loadError.message === "missing-types") {
        setError(
          "Debes configurar al menos un tipo de transacción antes de crear presupuestos."
        );
      } else {
        setError(
          "No pudimos cargar los catálogos necesarios. Verifica tu conexión e intenta nuevamente."
        );
      }
    } finally {
      setIsLoading(false);
    }
  }, [entry, fetchCategoriesByType]);

  useEffect(() => {
    if (isOpen) {
      loadModalData();
    } else {
      setFormData(createEmptyForm());
      setInitialSnapshot(null);
      setTransactionTypes([]);
      setCategories([]);
      setError(null);
      setCatalogNotice(null);
      setIsSubmitting(false);
      setIsLoading(false);
    }
  }, [isOpen, loadModalData]);

  const handleTypeChange = async (event: ChangeEvent<HTMLSelectElement>) => {
    const nextTypeId = Number(event.target.value);
    const typeOption = transactionTypes.find((type) => type.id === nextTypeId);
    setFormData((prev) => ({
      ...prev,
      typeId: String(nextTypeId),
      typeValue: typeOption?.value ?? prev.typeValue,
      goalId: "",
      debtId: "",
    }));

    const nextCategories = await fetchCategoriesByType(nextTypeId);
    setCategories(nextCategories);
    setCatalogNotice(null);

    if (nextCategories.length === 0) {
      setCatalogNotice(
        "No encontramos categorías para este tipo. Revisa la sección de Configuración."
      );
    }

    if (typeOption) {
      const normalized = normalizeTypeLabel(typeOption.value);
      if (normalized.includes("ahorro") && goals.length === 0) {
        setCatalogNotice(
          "Para planear un ahorro necesitas crear una meta desde la sección Metas y deudas."
        );
      }
      if (normalized.includes("deuda") && debts.length === 0) {
        setCatalogNotice(
          "Para planear un pago de deuda necesitas registrar una deuda en Metas y deudas."
        );
      }
    }

    setFormData((prev) => ({
      ...prev,
      categoryValue: nextCategories[0]?.value ?? "",
    }));
  };

  const LIMITED_NUMERIC_FIELDS = new Set(["amount"]);

  const handleInputChange = (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;

    if (name === "description" && value.length > 100) {
      event.preventDefault();
      setFormData((prev) => ({ ...prev, description: value.slice(0, 100) }));
      return;
    }

    if (LIMITED_NUMERIC_FIELDS.has(name)) {
      const digitsOnly = value.replace(/[^0-9]/g, "");
      if (digitsOnly.length > 10) {
        return;
      }
    }

    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleCategoryChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, categoryValue: event.target.value }));
  };

  const handleGoalChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, goalId: event.target.value }));
  };

  const handleDebtChange = (event: ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, debtId: event.target.value }));
  };

  const handleReferenceMonthChange = (
    event: ChangeEvent<HTMLSelectElement>
  ) => {
    const nextMonth = event.target.value;
    setFormData((prev) => {
      const nextState = { ...prev, referenceMonth: nextMonth };
      const autoPeriod = computeAutoPeriod(
        prev.frequency,
        nextMonth,
        prev.referenceYear
      );
      if (autoPeriod) {
        nextState.start_date = normalizeDateInputValue(autoPeriod.start);
        nextState.due_date = normalizeDateInputValue(autoPeriod.end);
      }
      return nextState;
    });
  };

  const handleReferenceYearChange = (
    event: ChangeEvent<HTMLSelectElement>
  ) => {
    const nextYear = event.target.value;
    setFormData((prev) => {
      const nextState = { ...prev, referenceYear: nextYear };
      const autoPeriod = computeAutoPeriod(
        prev.frequency,
        prev.referenceMonth,
        nextYear
      );
      if (autoPeriod) {
        nextState.start_date = normalizeDateInputValue(autoPeriod.start);
        nextState.due_date = normalizeDateInputValue(autoPeriod.end);
      }
      return nextState;
    });
  };

  const handleCustomScheduleToggle = (
    event: ChangeEvent<HTMLInputElement>
  ) => {
    const { checked } = event.target;
    setFormData((prev) => {
      const nextState = { ...prev, use_custom_schedule: checked };
      if (checked) {
        const autoPeriod = computeAutoPeriod(
          prev.frequency,
          prev.referenceMonth,
          prev.referenceYear
        );
        if (autoPeriod) {
          nextState.start_date = normalizeDateInputValue(autoPeriod.start);
          nextState.due_date = normalizeDateInputValue(autoPeriod.end);
        }
      }
      return nextState;
    });
  };

  const handleFrequencyChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextFrequency = event.target.value;
    setFormData((prev) => {
      const shouldForceRecurring = prev.frequency === "Única vez";
      const nextIsRecurring =
        nextFrequency === "Única vez"
          ? false
          : shouldForceRecurring
          ? true
          : prev.is_recurring;

      const updated: BudgetFormState = {
        ...prev,
        frequency: nextFrequency,
        due_date:
          nextFrequency === "Única vez" && prev.start_date
            ? prev.start_date
            : prev.due_date,
        is_recurring: nextIsRecurring,
      };

      if (!prev.use_custom_schedule) {
        const autoPeriod = computeAutoPeriod(
          nextFrequency,
          prev.referenceMonth,
          prev.referenceYear
        );
        if (autoPeriod) {
          updated.start_date = normalizeDateInputValue(autoPeriod.start);
          updated.due_date = normalizeDateInputValue(autoPeriod.end);
        }
      }

      return updated;
    });
  };

  const handleCheckboxChange = (event: ChangeEvent<HTMLInputElement>) => {
    const { checked } = event.target;
    setFormData((prev) => ({
      ...prev,
      is_recurring: prev.frequency === "Única vez" ? false : checked,
    }));
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);

    const trimmedDescription = formData.description.trim();
    const parsedAmount = parseFloat(formData.amount);

    if (!Number.isFinite(parsedAmount) || parsedAmount <= 0) {
      setError("Ingresa un monto válido mayor que cero.");
      return;
    }

    if (!formData.typeValue) {
      setError("Selecciona un tipo de transacción para tu presupuesto.");
      return;
    }

    if (!formData.categoryValue) {
      setError("Selecciona una categoría para clasificar el presupuesto.");
      return;
    }

    if (requiresGoal && !formData.goalId) {
      setError("Selecciona la meta que deseas fondear con este presupuesto.");
      return;
    }

    if (requiresDebt && !formData.debtId) {
      setError("Selecciona la deuda a la que aplicarás este presupuesto.");
      return;
    }

    if (formData.use_custom_schedule) {
      if (!formData.start_date) {
        setError("Selecciona la fecha de inicio del presupuesto.");
        return;
      }

      if (!formData.due_date) {
        setError("Selecciona la fecha de vencimiento del presupuesto.");
        return;
      }

      const parsedStart = new Date(formData.start_date);
      const parsedDue = new Date(formData.due_date);

      if (Number.isNaN(parsedStart.getTime()) || Number.isNaN(parsedDue.getTime())) {
        setError("Las fechas proporcionadas no son válidas.");
        return;
      }

      if (parsedDue < parsedStart) {
        setError(
          "La fecha de vencimiento debe ser posterior o igual a la fecha de inicio."
        );
        return;
      }
    }

    if (entry?.id && initialSnapshot) {
      const initialDescription = initialSnapshot.description.trim();
      const initialAmount = parseFloat(initialSnapshot.amount || "0");
      const initialGoal = initialSnapshot.goalId || "";
      const initialDebt = initialSnapshot.debtId || "";
      const currentGoal = formData.goalId || "";
      const currentDebt = formData.debtId || "";

      const unchanged =
        initialDescription === trimmedDescription &&
        Number.isFinite(initialAmount) &&
        initialAmount === parsedAmount &&
        initialSnapshot.referenceMonth === formData.referenceMonth &&
        initialSnapshot.referenceYear === formData.referenceYear &&
        initialSnapshot.start_date === formData.start_date &&
        initialSnapshot.due_date === formData.due_date &&
        initialSnapshot.typeId === formData.typeId &&
        initialSnapshot.categoryValue === formData.categoryValue &&
        initialGoal === currentGoal &&
        initialDebt === currentDebt &&
        initialSnapshot.frequency === formData.frequency &&
        initialSnapshot.is_recurring === formData.is_recurring &&
        initialSnapshot.use_custom_schedule === formData.use_custom_schedule;

      if (unchanged) {
        setError("No has realizado cambios en este presupuesto.");
        return;
      }
    }

    const payload: Record<string, unknown> = {
      description: trimmedDescription || formData.categoryValue,
      type: formData.typeValue,
      category: formData.categoryValue,
      budgeted_amount: parsedAmount,
      frequency: formData.frequency,
      is_recurring:
        formData.frequency === "Única vez" ? false : formData.is_recurring,
      goal_id: formData.goalId ? Number(formData.goalId) : null,
      debt_id: formData.debtId ? Number(formData.debtId) : null,
      use_custom_schedule: formData.use_custom_schedule,
    };

    if (formData.use_custom_schedule) {
      payload.start_date = formData.start_date;
      payload.due_date = formData.due_date;
    } else {
      payload.month = Number(formData.referenceMonth);
      payload.year = Number(formData.referenceYear);
    }

    setIsSubmitting(true);

    try {
      if (entry?.id) {
        await axios.put(apiPath(`/budget/${entry.id}`), payload);
      } else {
        await axios.post(apiPath("/budget"), payload);
      }
      onSave();
      onClose();
    } catch (submitError) {
      console.error("Error al guardar la entrada del presupuesto:", submitError);
      const message =
        axios.isAxiosError(submitError) && submitError.response?.data?.detail
          ? String(submitError.response.data.detail)
          : "No pudimos guardar el presupuesto. Inténtalo de nuevo.";
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      className="nebula-modal__content"
      overlayClassName="nebula-modal__overlay"
      closeTimeoutMS={320}
    >
      <div
        className="nebula-modal__panel app-card w-full p-6 shadow-2xl backdrop-blur"
        style={{ "--modal-max-width": "min(95vw, 720px)" } as CSSProperties}
      >
        <div className="mb-5 flex items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold text-slate-900 dark:text-slate-100">
              {entry ? "Editar" : "Añadir"} entrada de presupuesto
            </h2>
            <p className="mt-1 text-sm text-muted">
              Define el compromiso, clasifícalo y fija cuándo debería ejecutarse.
            </p>
          </div>
          <CalendarDays className="h-6 w-6 text-sky-500" />
        </div>

        {error && (
          <div className="mb-4 flex items-start gap-2 rounded-xl border border-rose-500/40 bg-rose-500/10 px-4 py-3 text-sm text-rose-600 dark:text-rose-100">
            <AlertCircle className="mt-0.5 h-4 w-4" />
            <p>{error}</p>
          </div>
        )}

        {catalogNotice && !error && (
          <div className="mb-4 rounded-xl border border-amber-400/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-100">
            {catalogNotice}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                <TypeIcon className="h-3.5 w-3.5" /> Tipo
              </span>
              <select
                name="typeId"
                value={formData.typeId}
                onChange={handleTypeChange}
                disabled={isLoading || transactionTypes.length === 0}
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed dark:text-slate-100"
              >
                {transactionTypes.map((type) => (
                  <option key={type.id} value={String(type.id)}>
                    {type.value}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                <Tag className="h-3.5 w-3.5" /> Categoría
              </span>
              <select
                name="category"
                value={formData.categoryValue}
                onChange={handleCategoryChange}
                disabled={isLoading || sortedCategories.length === 0}
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 disabled:cursor-not-allowed dark:text-slate-100"
              >
                {sortedCategories.map((category) => (
                  <option key={`${category.id}-${category.value}`} value={category.value}>
                    {category.value}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {(shouldShowGoalSelect || shouldShowDebtSelect) && (
            <div className="grid gap-4 sm:grid-cols-2">
              {shouldShowGoalSelect && (
                goals.length > 0 ? (
                  <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
                    <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                      Meta
                    </span>
                    <select
                      name="goalId"
                      value={formData.goalId}
                      onChange={handleGoalChange}
                      required={requiresGoal}
                      className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    >
                      <option value="">
                        {requiresGoal
                          ? "Selecciona una meta"
                          : "Asociar meta (opcional)"}
                      </option>
                      {goals.map((goal) => (
                        <option key={goal.id} value={goal.id}>
                          {goal.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <div className="rounded-lg border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)]/80 px-3 py-2 text-sm text-muted">
                    Crea una meta para vincular este presupuesto de ahorro.
                  </div>
                )
              )}

              {shouldShowDebtSelect && (
                debts.length > 0 ? (
                  <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
                    <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                      Deuda
                    </span>
                    <select
                      name="debtId"
                      value={formData.debtId}
                      onChange={handleDebtChange}
                      required={requiresDebt}
                      className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                    >
                      <option value="">
                        {requiresDebt
                          ? "Selecciona una deuda"
                          : "Asociar deuda (opcional)"}
                      </option>
                      {debts.map((debt) => (
                        <option key={debt.id} value={debt.id}>
                          {debt.name}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : (
                  <div className="rounded-lg border border-dashed border-[var(--app-border)] bg-[var(--app-surface-muted)]/80 px-3 py-2 text-sm text-muted">
                    Registra una deuda para asignar este presupuesto de pago.
                  </div>
                )
              )}
            </div>
          )}

          <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
            <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
              <FileText className="h-3.5 w-3.5" /> Descripción
            </span>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={2}
              maxLength={100}
              placeholder="Ej. Pago de renta, seguro del auto, colegiatura..."
              className="min-h-[70px] w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
            />
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                <CalendarDays className="h-3.5 w-3.5" /> Mes de aplicación
              </span>
              <select
                name="referenceMonth"
                value={formData.referenceMonth}
                onChange={handleReferenceMonthChange}
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              >
                {MONTH_OPTIONS.map((month) => (
                  <option key={month.value} value={month.value}>
                    {month.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                <CalendarDays className="h-3.5 w-3.5" /> Año
              </span>
              <select
                name="referenceYear"
                value={formData.referenceYear}
                onChange={handleReferenceYearChange}
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              >
                {yearOptions.map((year) => (
                  <option key={year.value} value={year.value}>
                    {year.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface-muted)]/60 px-4 py-4">
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                name="use_custom_schedule"
                checked={formData.use_custom_schedule}
                onChange={handleCustomScheduleToggle}
                className="h-5 w-5 rounded border-slate-400 text-sky-500 focus:ring-sky-400"
              />
              <span className="text-sm font-medium text-[var(--app-text)]">
                Definir fechas manualmente
              </span>
            </label>
            {formData.use_custom_schedule ? (
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
                  <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                    <CalendarDays className="h-3.5 w-3.5" /> Fecha de inicio
                  </span>
                  <input
                    type="date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleInputChange}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </label>

                <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
                  <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                    <CalendarDays className="h-3.5 w-3.5" /> Fecha comprometida
                  </span>
                  <input
                    type="date"
                    name="due_date"
                    value={formData.due_date}
                    onChange={handleInputChange}
                    className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
                  />
                </label>
              </div>
            ) : automaticPeriodPreview ? (
              <div className="mt-4 rounded-xl border border-dashed border-[var(--app-border)] bg-[var(--app-surface)]/80 px-4 py-3 text-xs text-muted">
                <p>
                  El sistema aplicará automáticamente este presupuesto del
                  <span className="font-semibold text-[var(--app-text)]"> {automaticPeriodPreview.startLabel}</span>
                  al
                  <span className="font-semibold text-[var(--app-text)]"> {automaticPeriodPreview.endLabel}</span>.
                </p>
                <p className="mt-1">Al finalizar el período se marcará como vencido.</p>
              </div>
            ) : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                <Clock className="h-3.5 w-3.5" /> Frecuencia
              </span>
              <select
                name="frequency"
                value={formData.frequency}
                onChange={handleFrequencyChange}
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              >
                <option value="Única vez">Única vez</option>
                <option value="Semanal">Semanal</option>
                <option value="Quincenal">Quincenal</option>
                <option value="Mensual">Mensual</option>
                <option value="Anual">Anual</option>
              </select>
            </label>

            <label className="flex flex-col gap-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-300">
                $ Monto estimado
              </span>
              <input
                type="number"
                name="amount"
                min="0"
                step="0.01"
                value={formData.amount}
                onChange={handleInputChange}
                required
                inputMode="decimal"
                className="w-full rounded-lg border border-[var(--app-border)] bg-[var(--app-surface)] px-3 py-2 text-sm text-slate-900 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200 dark:text-slate-100"
              />
            </label>
          </div>

          <label className="flex items-center gap-3 rounded-lg border border-[var(--app-border)] bg-[var(--app-surface-muted)] px-3 py-3 text-sm text-slate-700 dark:text-slate-200">
            <input
              type="checkbox"
              name="is_recurring"
              checked={formData.is_recurring && formData.frequency !== "Única vez"}
              onChange={handleCheckboxChange}
              disabled={formData.frequency === "Única vez"}
              className="h-5 w-5 rounded border-slate-400 text-sky-500 focus:ring-sky-400"
            />
            <span className="flex-1">
              Repetir automáticamente este presupuesto para el siguiente periodo
              <span className="mt-1 block text-xs text-muted">
                {formData.frequency === "Única vez"
                  ? "Los presupuestos de una sola vez no se repiten."
                  : "Duplicaremos la entrada al cerrar el periodo para que no tengas que recrearla."}
              </span>
            </span>
          </label>

          <div className="flex flex-col-reverse gap-3 pt-4 sm:flex-row sm:items-center sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center justify-center rounded-lg border border-[var(--app-border)] px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-sky-400 hover:text-slate-900 dark:text-slate-200 dark:hover:text-slate-50"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={isSubmitting || isLoading}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-sky-600/25 transition hover:bg-sky-500 disabled:cursor-not-allowed disabled:bg-sky-700/50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Guardando
                </>
              ) : (
                "Guardar entrada"
              )}
            </button>
          </div>
        </form>
      </div>
    </Modal>
  );
}
