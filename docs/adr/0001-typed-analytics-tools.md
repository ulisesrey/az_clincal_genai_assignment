# Typed analytics tools instead of text-to-SQL or CSV-in-context

The LLM answers data questions only by calling a small set of typed, deterministic analytics tools. Python does all the arithmetic, and the LLM only picks the tools, their arguments and how to word the answer. Policy §8.2 requires traceable lineage from source to report. Fixed tools make every figure reproducible and tied to its Source Rows, and the hallucination surface stays narrow enough to check each citation.

## Considered Options

- **CSV in the prompt**: rejected. LLM arithmetic over 140 rows across three currencies is unreliable, and nothing can be traced.
- **Text-to-SQL**: rejected for now. It is more flexible, but generated queries are hard to verify, and it is harder to tie them to Source Rows for Evidence.
- **Code interpreter (sandboxed Python over the data)**: deferred. It is the natural next step for open-ended questions the typed tools can't express, but it needs sandboxing and a way to capture lineage from code it generates.

## Consequences

Questions outside what the tools cover get declined rather than approximated. Coverage grows by adding tools, and each new tool is a code change with tests.
