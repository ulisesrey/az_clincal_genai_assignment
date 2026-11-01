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
