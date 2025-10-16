const pad = (value: number): string => value.toString().padStart(2, "0");

const formatFromDate = (input: Date): string => {
  return `${input.getFullYear()}-${pad(input.getMonth() + 1)}-${pad(input.getDate())}`;
};

export const getTodayDateInputValue = (): string => formatFromDate(new Date());

export const parseDateOnly = (
  value: string | Date | null | undefined
): Date | null => {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  if (value instanceof Date) {
    return new Date(value.getFullYear(), value.getMonth(), value.getDate());
  }

  const trimmed = String(value).trim();
  const isoMatch = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (isoMatch) {
    const [, year, month, day] = isoMatch;
    return new Date(
      Number.parseInt(year, 10),
      Number.parseInt(month, 10) - 1,
      Number.parseInt(day, 10)
    );
  }

  const parsed = new Date(trimmed);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return new Date(
    parsed.getFullYear(),
    parsed.getMonth(),
    parsed.getDate()
  );
};

export const normalizeDateInputValue = (
  value: string | Date | null | undefined,
  fallback: string = getTodayDateInputValue()
): string => {
  if (value instanceof Date) {
    return formatFromDate(value);
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      return trimmed;
    }
    const isoMatch = trimmed.match(/^(\d{4}-\d{2}-\d{2})[T ]/);
    if (isoMatch) {
      return isoMatch[1];
    }
    const parsed = parseDateOnly(trimmed);
    if (parsed) {
      return formatFromDate(parsed);
    }
  }

  return fallback;
};

export const formatDateForDisplay = (
  value: string | Date | null | undefined,
  locale = "es-MX"
): string => {
  const parsed = parseDateOnly(value);
  if (!parsed) {
    return "";
  }
  return parsed.toLocaleDateString(locale);
};
