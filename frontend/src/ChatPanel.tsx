import { useEffect, useRef, useState, type FormEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { askQuestion, formatMoney, type AskResponse, type Computation, type SourceRow } from "./api";

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
        <div role="alert">
          <p>Could not answer: {ask.error.message}</p>
          <button type="button" onClick={() => ask.mutate(question)}>
            Retry
          </button>
        </div>
      )}
      {ask.isSuccess && <Answer response={ask.data} />}
    </article>
  );
}

function Answer({ response }: { response: AskResponse }) {
  const { computations, rows } = response.evidence;
  return (
    <div className={`answer answer-${response.status}`}>
      <p>
        <span data-testid="answer-status">{response.status}</span>
        {response.status === "declined" && " (Declined Answer)"}
      </p>
      <p style={{ whiteSpace: "pre-wrap" }}>{response.answer}</p>
      {response.warnings.length > 0 && (
        <ul aria-label="Warnings">
          {response.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
      )}
      <details>
        <summary>Computation</summary>
        {computations.length === 0 && <p>No Computation was run.</p>}
        {computations.map((computation, index) => (
          <ComputationView key={index} number={index + 1} computation={computation} />
        ))}
      </details>
      <details>
        <summary>Source Rows</summary>
        {rows.length === 0 ? <p>No Source Rows.</p> : <SourceRowsTable rows={rows} />}
      </details>
    </div>
  );
}

function ComputationView({ number, computation }: { number: number; computation: Computation }) {
  const { result } = computation;
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
      {result.by_currency && result.by_currency.length > 0 && (
        <table aria-label={`Computation ${number} by Original Currency`}>
          <thead>
            <tr>
              <th scope="col">Currency</th>
              <th scope="col">Net Spend (native)</th>
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
        <table aria-label={`Computation ${number} groups`}>
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

function SourceRowsTable({ rows }: { rows: SourceRow[] }) {
  const invoices = rows.filter((row) => row.invoice_number);
  const vendors = rows.filter((row) => row.vendor_id && !row.invoice_number);
  return (
    <>
      {invoices.length > 0 && (
        <table aria-label="Source Rows: invoices">
          <thead>
            <tr>
              <th scope="col">Invoice</th>
              <th scope="col">Invoice date</th>
              <th scope="col">Vendor</th>
              <th scope="col">Country</th>
              <th scope="col">Vendor Status (current)</th>
              <th scope="col">Original amount</th>
              <th scope="col">EUR-Equivalent</th>
              <th scope="col">ECB Reference Rate</th>
              <th scope="col">Rate Date</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(({ invoice_number, fields }) => (
              <tr key={invoice_number}>
                <th scope="row">{invoice_number}</th>
                <td>{fields.invoice_date}</td>
                <td>
                  {fields.vendor_id} {fields.vendor_name}
                </td>
                <td>{fields.country}</td>
                <td>{fields.vendor_status}</td>
                <td>{fields.amount && fields.currency && formatMoney(fields.amount, fields.currency)}</td>
                <td>{fields.eur_equivalent && formatMoney(fields.eur_equivalent, "EUR")}</td>
                <td>{fields.ecb_rate ?? "—"}</td>
                <td>{fields.rate_date ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {vendors.length > 0 && (
        <table aria-label="Source Rows: vendors">
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
            {vendors.map(({ vendor_id, fields }) => (
              <tr key={vendor_id}>
                <th scope="row">{vendor_id}</th>
                <td>{fields.vendor_name}</td>
                <td>{fields.country}</td>
                <td>{fields.category}</td>
                <td>{fields.vendor_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
