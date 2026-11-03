# Finance Spend Intelligence

An assistant that helps Finance analysts answer questions about 2025 vendor invoices and the Global Procurement & Spend Policy (FIN-POL-014), with every answer backed by traceable evidence.

## Invoices & spend

**Invoice**:
A single row in the 2025 invoice data, identified by its invoice number, with an amount in its original currency.
_Avoid_: Bill, transaction, record

**Credit Note**:
An invoice with a negative amount, representing money owed back by a vendor (policy §6).
_Avoid_: Refund, negative invoice

**Spend**:
The net sum of invoice amounts, so credit notes reduce it. Unless stated otherwise, spend means net spend.
_Avoid_: Cost, total (unqualified), gross spend (unless explicitly meant)

**Original Currency**:
The currency an invoice was issued in (EUR, GBP or USD).
_Avoid_: Local currency, invoice currency

**Reporting Currency**:
EUR, the Group currency that all spend is reported in (policy §5.1).
_Avoid_: Base currency, home currency

**EUR-Equivalent**:
An invoice amount converted to the reporting currency at the ECB reference rate for the invoice date.
_Avoid_: Converted amount, normalised amount

**ECB Reference Rate**:
The European Central Bank's published daily euro exchange rate, which is the authoritative conversion rate under policy §5.1.
_Avoid_: FX rate (unqualified), spot rate

**Rate Date**:
The ECB publication date of the rate used for an EUR-Equivalent. It is either the invoice date or the most recent earlier ECB business day.
_Avoid_: FX date, conversion date

## Vendors

**Vendor**:
A supplier listed in the Vendor Master, identified by vendor ID.
_Avoid_: Supplier, merchant, payee

**Vendor Master**:
The authoritative list of vendors with their country, category and status.
_Avoid_: Vendor list, supplier table

**Vendor Status**:
A vendor's current standing in the Vendor Master: ACTIVE, INACTIVE or ON_HOLD. Only ACTIVE vendors may be paid (policy §4.1). The Vendor Master holds no history, so we don't know a vendor's status at the time of an invoice.
_Avoid_: Vendor state, flag

## Policy & controls

**Approver**:
The person recorded as having approved an invoice. Only their username is known, not their role.
_Avoid_: Signer, authoriser

**Approval Tier**:
The role required to approve an invoice, based on its EUR value (policy §3), e.g. Department Head or Finance Director.
_Avoid_: Approval level, sign-off level

**Control Exception**:
An invoice that breaks a policy control that can be checked from the data: Maverick Spend, Missing Approval or Non-Active Vendor. One invoice can have several.
_Avoid_: Violation, breach, flag, issue

**Maverick Spend**:
An invoice with no PO reference and an EUR-Equivalent of EUR 1,000 or more (policy §2.2). It is only a potential exception, because an emergency exception under §9 can't be ruled out. Credit notes are never Maverick Spend.
_Avoid_: Rogue spend, off-PO spend

**Missing Approval**:
An invoice with no approver recorded. Such invoices must be held and not paid (policy §3.1).
_Avoid_: Unapproved invoice

**Non-Active Vendor**:
A vendor whose current Vendor Status is INACTIVE or ON_HOLD, which means its invoices need escalation (policy §4.1).
_Avoid_: Blocked vendor, bad vendor

**Policy Section**:
A numbered clause of FIN-POL-014 (e.g. §3.1), quoted word for word when cited.
_Avoid_: Rule, paragraph, chunk

## Answers

**Evidence**:
Everything an answer rests on: the policy references, the source rows and the computation that produced it.
_Avoid_: Sources, context, citations (unqualified)

**Policy Reference**:
A cited policy section, with its ID and verbatim text.
_Avoid_: Policy snippet, chunk

**Source Row**:
An invoice or vendor row that an answer was computed from, identified by invoice number or vendor ID.
_Avoid_: Record, hit, match

**Computation**:
The named analysis that was run to produce a figure, with its inputs and result.
_Avoid_: Query, calculation, tool output

**Declined Answer**:
An answer saying the question can't be answered from the available data and policy, with the reason why.
_Avoid_: Refusal, fallback, error
