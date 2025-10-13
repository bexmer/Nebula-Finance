const RAW_API_BASE_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000";

const NORMALIZED_BASE_URL = RAW_API_BASE_URL.replace(/\/$/, "");
const USE_PREFIXED_API = NORMALIZED_BASE_URL.endsWith("/api");

export const API_BASE_URL = USE_PREFIXED_API
  ? NORMALIZED_BASE_URL
  : `${NORMALIZED_BASE_URL}/api`;

export const apiPath = (segment: string) => {
  const normalized = segment.startsWith("/") ? segment : `/${segment}`;
  return `${API_BASE_URL}${normalized}`;
};

export const apiPathWithParams = (segment: string, params?: URLSearchParams) => {
  const base = apiPath(segment);
  if (!params || Array.from(params.keys()).length === 0) {
    return base;
  }
  return `${base}?${params.toString()}`;
};
