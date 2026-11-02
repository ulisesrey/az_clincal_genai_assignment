const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Money = string;

export type OriginalCurrency = "EUR" | "GBP" | "USD";

export interface CurrencyBreakdown {
  currency: OriginalCurrency;
  native_total: Money;
  spend_eur: Money;
  invoice_count: number;
}

export interface Summary {
  invoice_count: number;
  total_spend_eur: Money;
  by_currency: CurrencyBreakdown[];
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

export interface SpendGroup {
  key: string;
  name: string | null;
  spend_eur: Money;
  invoice_count: number;
  by_currency: CurrencyBreakdown[];
  invoice_numbers: string[];
}

export interface VendorRow {
  vendor_id: string;
  vendor_name: string;
  country: string;
  category: string;
  vendor_status: string;
  spend_eur: Money;
  invoice_count: number;
  invoice_numbers: string[];
}

export interface Computation {
  tool: string;
  args: Record<string, unknown>;
  result: {
    spend_eur?: Money;
    invoice_count?: number;
    by_currency?: CurrencyBreakdown[];
    groups?: SpendGroup[] | null;
    groups_omitted?: number;
    approval_tier?: string;
    amount?: Money;
    currency?: OriginalCurrency;
    eur_equivalent?: Money;
    ecb_rate?: string | null;
    rate_date?: string | null;
    invoices?: unknown[];
    invoices_omitted?: number;
    vendors?: VendorRow[];
    [field: string]: unknown;
  };
}

export interface PolicyReference {
  section: string;
  text: string;
}

export interface SourceRow {
  invoice_number: string;
  fields: Record<string, string | null>;
}

export interface AskResponse {
  answer: string;
  status: "answered" | "declined";
  evidence: {
    policy_refs: PolicyReference[];
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
