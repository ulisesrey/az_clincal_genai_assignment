import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { fetchSummary, formatMoney } from "./api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

function Stat({ label, value, testId, tone }: { label: string; value: string | number; testId: string; tone?: "warning" }) {
  return (
    <div className="rounded-md border bg-muted/40 p-4">
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd
        data-testid={testId}
        className={`mt-1 text-2xl font-semibold tabular-nums tracking-tight ${tone === "warning" ? "text-warning" : ""}`}
      >
        {value}
      </dd>
    </div>
  );
}

export function SummaryPanel() {
  const summary = useQuery({ queryKey: ["summary"], queryFn: fetchSummary });

  return (
    <section aria-labelledby="summary-heading">
      <Card>
        <CardHeader>
          <CardTitle id="summary-heading">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          {summary.isPending && (
            <div role="status" className="space-y-3">
              <p className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" aria-hidden />
                Loading summary…
              </p>
              <div className="grid gap-3 sm:grid-cols-3">
                <Skeleton className="h-20" />
                <Skeleton className="h-20" />
                <Skeleton className="h-20" />
              </div>
            </div>
          )}
          {summary.isError && (
            <div role="alert" className="flex flex-col gap-3 rounded-md border border-destructive/40 bg-destructive/5 p-4 text-destructive">
              <p className="flex items-center gap-2 text-sm">
                <AlertTriangle className="size-4 shrink-0" aria-hidden />
                Could not load the summary: {summary.error.message}
              </p>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="self-start"
                onClick={() => summary.refetch()}
                disabled={summary.isFetching}
              >
                <RefreshCw className={summary.isFetching ? "animate-spin" : ""} aria-hidden />
                Retry
              </Button>
            </div>
          )}
          {summary.isSuccess && (
            <>
              <dl className="grid gap-3 sm:grid-cols-3">
                <Stat label="Invoices" value={summary.data.invoice_count} testId="invoice-count" />
                <Stat label="Credit Notes" value={summary.data.credit_note_count} testId="credit-note-count" />
                <Stat
                  label="Net Spend (EUR-Equivalent)"
                  value={formatMoney(summary.data.total_spend_eur, "EUR")}
                  testId="total-spend"
                />
              </dl>

              <div className="grid gap-4 lg:grid-cols-2">
                <Table aria-label="Spend by Original Currency">
                  <TableHeader>
                    <TableRow>
                      <TableHead scope="col">Currency</TableHead>
                      <TableHead scope="col">Net Spend (native)</TableHead>
                      <TableHead scope="col">Net Spend (EUR-Equivalent)</TableHead>
                      <TableHead scope="col">Invoices</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.data.by_currency.map((row) => (
                      <TableRow key={row.currency}>
                        <TableHead scope="row" className="text-foreground">{row.currency}</TableHead>
                        <TableCell>{formatMoney(row.native_total, row.currency)}</TableCell>
                        <TableCell>{formatMoney(row.spend_eur, "EUR")}</TableCell>
                        <TableCell>{row.invoice_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                <Table aria-label="Spend by Vendor Status">
                  <TableHeader>
                    <TableRow>
                      <TableHead scope="col">Vendor Status (current)</TableHead>
                      <TableHead scope="col">Net Spend (EUR-Equivalent)</TableHead>
                      <TableHead scope="col">Invoices</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.data.by_vendor_status.map((row) => (
                      <TableRow key={row.vendor_status}>
                        <TableHead scope="row" className="text-foreground">{row.vendor_status}</TableHead>
                        <TableCell>{formatMoney(row.spend_eur, "EUR")}</TableCell>
                        <TableCell>{row.invoice_count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <h3 className="pt-2 text-base font-semibold tracking-tight">Control Exceptions</h3>
              <dl className="grid gap-3 sm:grid-cols-3">
                <Stat
                  label="Maverick Spend invoices (potential)"
                  value={summary.data.control_exceptions.maverick_spend}
                  testId="maverick-spend-count"
                  tone="warning"
                />
                <Stat
                  label="Invoices with Missing Approval"
                  value={summary.data.control_exceptions.missing_approval}
                  testId="missing-approval-count"
                  tone="warning"
                />
                <Stat
                  label="Invoices from a Non-Active Vendor"
                  value={summary.data.control_exceptions.non_active_vendor}
                  testId="non-active-vendor-count"
                  tone="warning"
                />
              </dl>
            </>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
