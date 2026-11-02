import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
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
      <h2 id="chat-heading">Ask a question</h2>
      {questions.map((question) => (
        <ChatMessage key={question.id} question={question.text} />
      ))}
      <form onSubmit={submit}>
        <label htmlFor="question-input">Question</label>
        <input id="question-input" value={draft} onChange={(event) => setDraft(event.target.value)} />
        <button type="submit" disabled={!draft.trim()}>
          Ask
        </button>
      </form>
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
    <article aria-label={question}>
      <p>
        <strong>Q:</strong> {question}
      </p>
      {ask.isPending && <p role="status">Answering…</p>}
      {ask.isError && (
        <div role="alert" data-look="error" style={LOOKS.error}>
          <p>
            <strong>Error</strong>: could not answer. {ask.error.message}
          </p>
          <button type="button" onClick={() => ask.mutate(question)}>
            Retry
          </button>
        </div>
      )}
      {ask.isSuccess && <Answer response={ask.data} />}
    </article>
  );
}

type Look = "answered" | "warned" | "declined" | "error";

// Each outcome looks different, so a Declined Answer is never mistaken for an answer or for an error.
const LOOKS: Record<Look, CSSProperties> = {
  answered: { padding: "0.5rem" },
  warned: { border: "2px solid #b45309", background: "#fffbeb", padding: "0.5rem" },
  declined: { border: "2px dashed #475569", background: "#f1f5f9", padding: "0.5rem" },
  error: { border: "2px solid #b91c1c", background: "#fef2f2", color: "#7f1d1d", padding: "0.5rem" },
};

function Answer({ response }: { response: AskResponse }) {
  const { computations, rows: sourceRows, policy_refs: policyRefs } = response.evidence;
  const warned = response.warnings.length > 0;
  const declined = response.status === "declined";
  const look: Look = declined ? "declined" : warned ? "warned" : "answered";
  return (
    <div data-look={look} style={LOOKS[look]}>
      <p>
        <span data-testid="answer-status">{response.status}</span>
      </p>
      {declined && (
        <p>
          <strong>Declined Answer</strong>: this can't be answered from the data and policy. Reason:
        </p>
      )}
      <p data-testid="answer-text" style={{ whiteSpace: "pre-wrap" }}>{response.answer}</p>
      {warned && (
        <ul aria-label="Warnings" data-testid="answer-warnings" style={{ color: "#92400e", fontWeight: "bold" }}>
          {response.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
      <details>
        <summary>Policy References</summary>
        {policyRefs.length === 0 ? <p>No Policy References.</p> : <PolicyReferences references={policyRefs} />}
      </details>
      <details>
        <summary>Computation</summary>
        {computations.length === 0 && <p>No Computation was run.</p>}
        {computations.map((computation, index) => (
          <ComputationView key={index} number={index + 1} computation={computation} />
        ))}
      </details>
      <details>
        <summary>Source Rows</summary>
        {sourceRows.length === 0 ? <p>No Source Rows.</p> : <SourceRows sourceRows={sourceRows} />}
      </details>
    </div>
  );
}

function PolicyReferences({ references }: { references: PolicyReference[] }) {
  return (
    <>
      {references.map(({ section, text }) => (
        <blockquote key={section} data-testid="policy-ref">
          <strong data-testid="policy-ref-section">§{section}</strong>
          <div style={{ whiteSpace: "pre-wrap" }}>{text}</div>
        </blockquote>
      ))}
    </>
  );
}

function ComputationView({ number, computation }: { number: number; computation: Computation }) {
  const { result } = computation;
  const groupBy = typeof computation.args.group_by === "string" ? computation.args.group_by : "group";
  return (
    <figure>
      <figcaption>
        Computation {number}: <code>{computation.tool}</code>
      </figcaption>
      <p>
        Inputs: <code>{JSON.stringify(computation.args)}</code>
      </p>
      {result.spend_eur !== undefined && (
        <p>
          Net Spend (EUR-Equivalent): <span data-testid="computation-spend">{formatMoney(result.spend_eur, "EUR")}</span>{" "}
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
        <table aria-label={`Computation ${number} by Original Currency`}>
          <thead>
            <tr>
              <th scope="col">Currency</th>
              <th scope="col">Net Spend (Original Currency)</th>
              <th scope="col">Net Spend (EUR-Equivalent)</th>
              <th scope="col">Invoices</th>
            </tr>
          </thead>
          <tbody>
            {result.by_currency.map((row) => (
              <tr key={row.currency}>
                <th scope="row">{row.currency}</th>
                <td>{formatMoney(row.native_total, row.currency)}</td>
                <td>{formatMoney(row.spend_eur, "EUR")}</td>
                <td>{row.invoice_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {result.groups && (
        <table aria-label={`Computation ${number} grouped by ${groupBy}`}>
          <thead>
            <tr>
              <th scope="col">Group</th>
              <th scope="col">Name</th>
              <th scope="col">Net Spend (EUR-Equivalent)</th>
              <th scope="col">Invoices</th>
            </tr>
          </thead>
          <tbody>
            {result.groups.map((group) => (
              <tr key={group.key}>
                <th scope="row">{group.key}</th>
                <td>{group.name ?? ""}</td>
                <td data-testid="group-spend">{formatMoney(group.spend_eur, "EUR")}</td>
                <td>{group.invoice_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!!result.groups_omitted && <p>{result.groups_omitted} lower-ranked groups not shown.</p>}
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
    <table aria-label="Invoice Source Rows">
      <thead>
        <tr>
          <th scope="col">Invoice</th>
          <th scope="col">Invoice date</th>
          <th scope="col">Vendor</th>
          <th scope="col">Country</th>
          <th scope="col">Vendor Status (current)</th>
          <th scope="col">Original Currency amount</th>
          <th scope="col">EUR-Equivalent</th>
          <th scope="col">ECB Reference Rate</th>
          <th scope="col">Rate Date</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(({ invoice_number, fields }) => (
          <tr key={invoice_number} data-testid="source-row" data-invoice-number={invoice_number}>
            <th scope="row" data-testid="source-row-invoice">
              {invoice_number}
            </th>
            <td>{fields.invoice_date}</td>
            <td data-testid="source-row-vendor" data-vendor-id={fields.vendor_id}>
              {fields.vendor_id} {fields.vendor_name}
            </td>
            <td data-testid="source-row-country">{fields.country}</td>
            <td data-testid="source-row-vendor-status">{fields.vendor_status}</td>
            <td data-testid="source-row-amount" data-amount={fields.amount} data-currency={fields.currency}>
              {formatMoney(fields.amount, fields.currency)}
            </td>
            <td data-testid="source-row-eur" data-amount={fields.eur_equivalent}>
              {formatMoney(fields.eur_equivalent, "EUR")}
            </td>
            <td data-testid="source-row-rate">{fields.ecb_rate ?? "—"}</td>
            <td data-testid="source-row-rate-date">{fields.rate_date ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function VendorSourceRowsTable({ rows }: { rows: VendorSourceRow[] }) {
  return (
    <table aria-label="Vendor Source Rows">
      <thead>
        <tr>
          <th scope="col">Vendor</th>
          <th scope="col">Name</th>
          <th scope="col">Country</th>
          <th scope="col">Category</th>
          <th scope="col">Vendor Status (current)</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(({ vendor_id, fields }) => (
          <tr key={vendor_id} data-testid="vendor-source-row" data-vendor-id={vendor_id}>
            <th scope="row">{vendor_id}</th>
            <td>{fields.vendor_name}</td>
            <td>{fields.country}</td>
            <td>{fields.category}</td>
            <td data-testid="vendor-source-row-status">{fields.vendor_status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
