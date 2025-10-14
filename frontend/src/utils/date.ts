const pad = (value: number): string => value.toString().padStart(2, "0");

const formatFromDate = (input: Date): string => {
  return `${input.getFullYear()}-${pad(input.getMonth() + 1)}-${pad(input.getDate())}`;
};

export const getTodayDateInputValue = (): string => formatFromDate(new Date());

export const normalizeDateInputValue = (
  value: string | Date | null | undefined,
  fallback: string = getTodayDateInputValue()
): string => {
  if (value instanceof Date) {
    return formatFromDate(value);
  }

  if (typeof value === "string") {
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return value;
    }
    const parsed = new Date(value);
    if (!Number.isNaN(parsed.getTime())) {
      return formatFromDate(parsed);
    }
  }

  return fallback;
};
