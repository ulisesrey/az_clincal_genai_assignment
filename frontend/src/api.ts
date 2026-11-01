const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Money = string;

export interface Summary {
  invoice_count: number;
  total_spend_eur: Money;
  by_currency: { currency: string; native_total: Money; spend_eur: Money; invoice_count: number }[];
  by_vendor_status: { vendor_status: string; spend_eur: Money; invoice_count: number }[];
  control_exceptions: { maverick_spend: number; missing_approval: number; non_active_vendor: number };
  credit_note_count: number;
}

export async function fetchSummary(): Promise<Summary> {
  const response = await fetch(`${API_URL}/summary`);
  if (!response.ok) {
    throw new Error(`Summary request failed (HTTP ${response.status})`);
  }
  return response.json();
}

const moneyFormat = new Intl.NumberFormat("en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function formatMoney(amount: Money, currency: string): string {
  return `${currency} ${moneyFormat.format(Number(amount))}`;
}

export interface CurrencySubtotal {
  currency: string;
  native_total: Money;
  spend_eur: Money;
  invoice_count: number;
}

export interface SpendGroup {
  key: string;
  name: string | null;
  spend_eur: Money;
  invoice_count: number;
  by_currency: CurrencySubtotal[];
  invoice_numbers: string[];
}

export interface Computation {
  tool: string;
  args: Record<string, unknown>;
  result: {
    spend_eur?: Money;
    invoice_count?: number;
    by_currency?: CurrencySubtotal[];
    groups?: SpendGroup[] | null;
    groups_omitted?: number;
    [field: string]: unknown;
  };
}

export interface SourceRow {
  invoice_number: string | null;
  vendor_id: string | null;
  fields: Record<string, string | null>;
}

export interface AskResponse {
  answer: string;
  status: "answered" | "declined";
  evidence: {
    policy_refs: { section: string; text: string }[];
    rows: SourceRow[];
    computations: Computation[];
  };
  warnings: string[];
}

export async function askQuestion(question: string): Promise<AskResponse> {
  const response = await fetch(`${API_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.error ? `: ${body.error}` : "";
    throw new Error(`Question failed (HTTP ${response.status})${detail}`);
  }
  return response.json();
}
