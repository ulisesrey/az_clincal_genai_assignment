import { useEffect, useRef, useState, type ComponentProps, type FormEvent, type ReactNode } from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertTriangle, Ban, CheckCircle2, ChevronRight, Loader2, RefreshCw, SendHorizontal } from "lucide-react";
import {
  askQuestion,
  formatMoney,
  type AskResponse,
  type Computation,
  type InvoiceSourceRow,
  type PolicyReference,
  type SourceRow,
  type VendorSourceRow,
} from "./api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface Question {
  id: number;
  text: string;
}

export function ChatPanel() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [draft, setDraft] = useState("");
  const nextId = useRef(1);

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setQuestions((previous) => [...previous, { id: nextId.current++, text }]);
    setDraft("");
  }

  return (
    <section aria-labelledby="chat-heading">
      <Card>
        <CardHeader>
          <CardTitle id="chat-heading">Ask a question</CardTitle>
          <p className="text-sm text-muted-foreground">
            Answers are computed from the invoice data and cited against the procurement policy.
          </p>
        </CardHeader>
        <CardContent>
          {questions.length === 0 && (
            <p className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
              No questions yet. Try “What was our total spend with our top vendor?”
            </p>
          )}
          {questions.map((question) => (
            <ChatMessage key={question.id} question={question.text} />
          ))}
          <form onSubmit={submit} className="space-y-1.5">
            <label htmlFor="question-input" className="block text-sm font-medium">
              Question
            </label>
            <div className="flex items-center gap-2">
              <Input id="question-input" value={draft} onChange={(event) => setDraft(event.target.value)} />
              <Button type="submit" disabled={!draft.trim()}>
                Ask
                <SendHorizontal aria-hidden />
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}

function ChatMessage({ question }: { question: string }) {
  const ask = useMutation({ mutationFn: askQuestion });
  const sent = useRef(false);

  useEffect(() => {
    if (sent.current) return;
    sent.current = true;
    ask.mutate(question);
  }, [ask, question]);

  return (
    <article aria-label={question} className="space-y-3">
      <p className="rounded-lg bg-muted px-4 py-2.5 text-sm">
        <strong className="font-semibold">Q:</strong> {question}
      </p>
      {ask.isPending && (
        <p role="status" className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Answering…
        </p>
      )}
      {ask.isError && (
        <div role="alert" data-look="error" className={LOOKS.error}>
          <p className="flex items-start gap-2 text-sm">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" aria-hidden />
            <span>
              <strong>Error</strong>: could not answer. {ask.error.message}
            </span>
          </p>
          <Button type="button" variant="outline" size="sm" className="self-start" onClick={() => ask.mutate(question)}>
            <RefreshCw aria-hidden />
            Retry
          </Button>
        </div>
      )}
      {ask.isSuccess && <Answer response={ask.data} />}
    </article>
  );
}

type Look = "answered" | "warned" | "declined" | "error";

// Each outcome looks different, so a Declined Answer is never mistaken for an answer or for an error.
const LOOKS: Record<Look, string> = {
  answered: "space-y-3 rounded-lg border bg-card p-4",
  warned: "space-y-3 rounded-lg border-2 border-solid border-amber-600 bg-amber-50 p-4",
  declined: "space-y-3 rounded-lg border-2 border-dashed border-slate-500 bg-slate-100 p-4",
  error: "flex flex-col gap-3 rounded-lg border-2 border-solid border-red-700 bg-red-50 p-4 text-red-900",
};

function Evidence({ title, children }: { title: string; children: ReactNode }) {
  return (
    <details className="group rounded-md border bg-card">
      <summary className="flex cursor-pointer list-none items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring [&::-webkit-details-marker]:hidden">
        <ChevronRight className="size-4 transition-transform group-open:rotate-90" aria-hidden />
        {title}
      </summary>
      <div className="space-y-3 border-t p-3">{children}</div>
    </details>
  );
}

function Answer({ response }: { response: AskResponse }) {
  const { computations, rows: sourceRows, policy_refs: policyRefs } = response.evidence;
  const warned = response.warnings.length > 0;
  const declined = response.status === "declined";
  const look: Look = declined ? "declined" : warned ? "warned" : "answered";
  const StatusIcon = declined ? Ban : warned ? AlertTriangle : CheckCircle2;
  return (
    <div data-look={look} className={LOOKS[look]}>
      <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground">
        <StatusIcon className="size-4" aria-hidden />
        <span data-testid="answer-status">{response.status}</span>
      </p>
      {declined && (
        <p className="text-sm">
          <strong>Declined Answer</strong>: this can't be answered from the data and policy. Reason:
        </p>
      )}
      <p data-testid="answer-text" className="whitespace-pre-wrap text-sm leading-relaxed">
        {response.answer}
      </p>
      {warned && (
        <ul aria-label="Warnings" data-testid="answer-warnings" className="list-inside list-disc text-sm font-semibold text-amber-800">
          {response.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
      <Evidence title="Policy References">
        {policyRefs.length === 0 ? <EmptyNote>No Policy References.</EmptyNote> : <PolicyReferences references={policyRefs} />}
      </Evidence>
      <Evidence title="Computation">
        {computations.length === 0 && <EmptyNote>No Computation was run.</EmptyNote>}
        {computations.map((computation, index) => (
          <ComputationView key={index} number={index + 1} computation={computation} />
        ))}
      </Evidence>
      <Evidence title="Source Rows">
        {sourceRows.length === 0 ? <EmptyNote>No Source Rows.</EmptyNote> : <SourceRows sourceRows={sourceRows} />}
      </Evidence>
    </div>
  );
}

function EmptyNote({ children }: { children: ReactNode }) {
  return <p className="text-sm text-muted-foreground">{children}</p>;
}

function PolicyReferences({ references }: { references: PolicyReference[] }) {
  return (
    <>
      {references.map(({ section, text }) => (
        <blockquote key={section} data-testid="policy-ref" className="space-y-1 border-l-4 border-primary/40 pl-3 text-sm">
          <strong data-testid="policy-ref-section" className="text-primary">
            §{section}
          </strong>
          <div className="whitespace-pre-wrap text-muted-foreground">{text}</div>
        </blockquote>
      ))}
    </>
  );
}

function RowHeader({ className, ...props }: ComponentProps<"th">) {
  return <TableHead scope="row" className={cn("font-medium text-foreground", className)} {...props} />;
}

function ComputationView({ number, computation }: { number: number; computation: Computation }) {
  const { result } = computation;
  const groupBy = typeof computation.args.group_by === "string" ? computation.args.group_by : "group";
  return (
    <figure className="space-y-2 text-sm">
      <figcaption className="font-medium">
        Computation {number}: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{computation.tool}</code>
      </figcaption>
      <p className="text-muted-foreground">
        Inputs: <code className="break-all font-mono text-xs">{JSON.stringify(computation.args)}</code>
      </p>
      {result.spend_eur !== undefined && (
        <p>
          Net Spend (EUR-Equivalent): <span data-testid="computation-spend" className="font-semibold">{formatMoney(result.spend_eur, "EUR")}</span>{" "}
          across {result.invoice_count} invoices
        </p>
      )}
      {result.approval_tier !== undefined && result.eur_equivalent !== undefined && (
        <p>
          Approval Tier: <strong data-testid="approval-tier">{result.approval_tier}</strong> for{" "}
          {result.currency && result.amount && formatMoney(result.amount, result.currency)}, an EUR-Equivalent of{" "}
          <span data-testid="approval-eur-equivalent" data-amount={result.eur_equivalent}>
            {formatMoney(result.eur_equivalent, "EUR")}
          </span>
          {result.ecb_rate && (
            <>
              {" "}
              at ECB Reference Rate <span data-testid="approval-rate">{result.ecb_rate}</span> (Rate Date{" "}
              <span data-testid="approval-rate-date">{result.rate_date}</span>)
            </>
          )}
        </p>
      )}
      {result.by_currency && result.by_currency.length > 0 && (
        <Table aria-label={`Computation ${number} by Original Currency`}>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Currency</TableHead>
              <TableHead scope="col">Net Spend (Original Currency)</TableHead>
              <TableHead scope="col">Net Spend (EUR-Equivalent)</TableHead>
              <TableHead scope="col">Invoices</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {result.by_currency.map((row) => (
              <TableRow key={row.currency}>
                <RowHeader>{row.currency}</RowHeader>
                <TableCell>{formatMoney(row.native_total, row.currency)}</TableCell>
                <TableCell>{formatMoney(row.spend_eur, "EUR")}</TableCell>
                <TableCell>{row.invoice_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {result.groups && (
        <Table aria-label={`Computation ${number} grouped by ${groupBy}`}>
          <TableHeader>
            <TableRow>
              <TableHead scope="col">Group</TableHead>
              <TableHead scope="col">Name</TableHead>
              <TableHead scope="col">Net Spend (EUR-Equivalent)</TableHead>
              <TableHead scope="col">Invoices</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {result.groups.map((group) => (
              <TableRow key={group.key}>
                <RowHeader>{group.key}</RowHeader>
                <TableCell>{group.name ?? ""}</TableCell>
                <TableCell data-testid="group-spend">{formatMoney(group.spend_eur, "EUR")}</TableCell>
                <TableCell>{group.invoice_count}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      {!!result.groups_omitted && <EmptyNote>{result.groups_omitted} lower-ranked groups not shown.</EmptyNote>}
    </figure>
  );
}

function SourceRows({ sourceRows }: { sourceRows: SourceRow[] }) {
  const invoices = sourceRows.filter((row): row is InvoiceSourceRow => row.kind === "invoice");
  const vendors = sourceRows.filter((row): row is VendorSourceRow => row.kind === "vendor");
  return (
    <>
      {invoices.length > 0 && <InvoiceSourceRowsTable rows={invoices} />}
      {vendors.length > 0 && <VendorSourceRowsTable rows={vendors} />}
    </>
  );
}

function InvoiceSourceRowsTable({ rows }: { rows: InvoiceSourceRow[] }) {
  return (
    <Table aria-label="Invoice Source Rows">
      <TableHeader>
        <TableRow>
          <TableHead scope="col">Invoice</TableHead>
          <TableHead scope="col">Invoice date</TableHead>
          <TableHead scope="col">Vendor</TableHead>
          <TableHead scope="col">Country</TableHead>
          <TableHead scope="col">Vendor Status (current)</TableHead>
          <TableHead scope="col">Original Currency amount</TableHead>
          <TableHead scope="col">EUR-Equivalent</TableHead>
          <TableHead scope="col">ECB Reference Rate</TableHead>
          <TableHead scope="col">Rate Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map(({ invoice_number, fields }) => (
          <TableRow key={invoice_number} data-testid="source-row" data-invoice-number={invoice_number}>
            <RowHeader data-testid="source-row-invoice">{invoice_number}</RowHeader>
            <TableCell>{fields.invoice_date}</TableCell>
            <TableCell data-testid="source-row-vendor" data-vendor-id={fields.vendor_id}>
              {fields.vendor_id} {fields.vendor_name}
            </TableCell>
            <TableCell data-testid="source-row-country">{fields.country}</TableCell>
            <TableCell data-testid="source-row-vendor-status">{fields.vendor_status}</TableCell>
            <TableCell data-testid="source-row-amount" data-amount={fields.amount} data-currency={fields.currency}>
              {formatMoney(fields.amount, fields.currency)}
            </TableCell>
            <TableCell data-testid="source-row-eur" data-amount={fields.eur_equivalent}>
              {formatMoney(fields.eur_equivalent, "EUR")}
            </TableCell>
            <TableCell data-testid="source-row-rate">{fields.ecb_rate ?? "—"}</TableCell>
            <TableCell data-testid="source-row-rate-date">{fields.rate_date ?? "—"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function VendorSourceRowsTable({ rows }: { rows: VendorSourceRow[] }) {
  return (
    <Table aria-label="Vendor Source Rows">
      <TableHeader>
        <TableRow>
          <TableHead scope="col">Vendor</TableHead>
          <TableHead scope="col">Name</TableHead>
          <TableHead scope="col">Country</TableHead>
          <TableHead scope="col">Category</TableHead>
          <TableHead scope="col">Vendor Status (current)</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map(({ vendor_id, fields }) => (
          <TableRow key={vendor_id} data-testid="vendor-source-row" data-vendor-id={vendor_id}>
            <RowHeader>{vendor_id}</RowHeader>
            <TableCell>{fields.vendor_name}</TableCell>
            <TableCell>{fields.country}</TableCell>
            <TableCell>{fields.category}</TableCell>
            <TableCell data-testid="vendor-source-row-status">{fields.vendor_status}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
