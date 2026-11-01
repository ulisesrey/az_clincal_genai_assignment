import { useQuery } from "@tanstack/react-query";
import { fetchSummary, formatMoney } from "./api";

export function SummaryPanel() {
  const summary = useQuery({ queryKey: ["summary"], queryFn: fetchSummary });

  return (
    <section aria-labelledby="summary-heading">
      <h2 id="summary-heading">Summary</h2>
      {summary.isPending && <p role="status">Loading summary…</p>}
      {summary.isError && (
        <div role="alert">
          <p>Could not load the summary: {summary.error.message}</p>
          <button type="button" onClick={() => summary.refetch()} disabled={summary.isFetching}>
            Retry
          </button>
        </div>
      )}
      {summary.isSuccess && (
        <>
          <dl>
            <dt>Invoices</dt>
            <dd data-testid="invoice-count">{summary.data.invoice_count}</dd>
            <dt>Credit Notes</dt>
            <dd data-testid="credit-note-count">{summary.data.credit_note_count}</dd>
            <dt>Net Spend (EUR-Equivalent)</dt>
            <dd data-testid="total-spend">{formatMoney(summary.data.total_spend_eur, "EUR")}</dd>
          </dl>

          <table aria-label="Spend by Original Currency">
            <thead>
              <tr>
                <th scope="col">Currency</th>
                <th scope="col">Net Spend (native)</th>
                <th scope="col">Net Spend (EUR-Equivalent)</th>
                <th scope="col">Invoices</th>
              </tr>
            </thead>
            <tbody>
              {summary.data.by_currency.map((row) => (
                <tr key={row.currency}>
                  <th scope="row">{row.currency}</th>
                  <td>{formatMoney(row.native_total, row.currency)}</td>
                  <td>{formatMoney(row.spend_eur, "EUR")}</td>
                  <td>{row.invoice_count}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <table aria-label="Spend by Vendor Status">
            <thead>
              <tr>
                <th scope="col">Vendor Status (current)</th>
                <th scope="col">Net Spend (EUR-Equivalent)</th>
                <th scope="col">Invoices</th>
              </tr>
            </thead>
            <tbody>
              {summary.data.by_vendor_status.map((row) => (
                <tr key={row.vendor_status}>
                  <th scope="row">{row.vendor_status}</th>
                  <td>{formatMoney(row.spend_eur, "EUR")}</td>
                  <td>{row.invoice_count}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3>Control Exceptions</h3>
          <dl>
            <dt>Maverick Spend (potential)</dt>
            <dd data-testid="maverick-spend-count">{summary.data.control_exceptions.maverick_spend}</dd>
            <dt>Missing Approval</dt>
            <dd data-testid="missing-approval-count">{summary.data.control_exceptions.missing_approval}</dd>
            <dt>Non-Active Vendor</dt>
            <dd data-testid="non-active-vendor-count">{summary.data.control_exceptions.non_active_vendor}</dd>
          </dl>
        </>
      )}
    </section>
  );
}
