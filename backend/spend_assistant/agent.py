"""Agent loop: one stateless, single-turn question answered with typed tools over Converse."""

import json
from typing import Any, Literal

import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from spend_assistant.evidence import Citations, Computation, Evidence, ToolCall, assemble_evidence
from spend_assistant.fx import EcbRates
from spend_assistant.llm import ChatProvider
from spend_assistant.policy import Policy
from spend_assistant.prompt import SUBMIT_ANSWER, FinalAnswer, system_prompt, tool_specs
from spend_assistant.tools import TOOLS, ToolContext

MAX_TOOL_ITERATIONS = 5

_REPROMPT = f"Finish by calling {SUBMIT_ANSWER} with your answer and its citations; a plain-text reply is not accepted."

AnswerStatus = Literal["answered", "declined"]


class AskResponse(BaseModel):
    answer: str
    status: AnswerStatus
    evidence: Evidence
    warnings: list[str] = Field(default_factory=list)


class AnswerNotReached(Exception):
    """The model kept calling tools without answering within MAX_TOOL_ITERATIONS turns."""


class Agent:
    def __init__(
        self, ledger: pd.DataFrame, vendors: pd.DataFrame, provider: ChatProvider, policy: Policy, rates: EcbRates
    ) -> None:
        self.ledger = ledger
        self.provider = provider
        self.policy = policy
        self.context = ToolContext(ledger, vendors, rates)
        self.system_prompt = system_prompt(policy)
        self.tool_specs = tool_specs()

    def ask(self, question: str) -> AskResponse:
        messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": question}]}]
        tool_calls: list[ToolCall] = []

        for _ in range(MAX_TOOL_ITERATIONS):
            message = self.provider.converse(self.system_prompt, messages, self.tool_specs)
            messages.append(message)
            content = message.get("content", [])
            tool_uses = [block["toolUse"] for block in content if "toolUse" in block]
            if not tool_uses:
                messages.append({"role": "user", "content": [{"text": _REPROMPT}]})
                continue

            results = []
            final: FinalAnswer | None = None
            for tool_use in tool_uses:
                if tool_use["name"] != SUBMIT_ANSWER:
                    results.append(self._run_tool(tool_use, tool_calls))
                    continue
                try:
                    submitted = FinalAnswer.model_validate(tool_use["input"])
                except ValidationError as error:
                    results.append(_tool_result(tool_use, {"error": str(error)}, error=True))
                    continue
                final = final or submitted
            if final is not None:
                return self._respond(final.answer, final, tool_calls)
            messages.append({"role": "user", "content": results})

        raise AnswerNotReached(f"No answer within {MAX_TOOL_ITERATIONS} model turns.")

    def _respond(self, answer: str, citations: Citations, tool_calls: list[ToolCall]) -> AskResponse:
        evidence, warnings = assemble_evidence(self.ledger, self.policy, tool_calls, citations)
        return AskResponse(answer=answer, status="answered", evidence=evidence, warnings=warnings)

    def _run_tool(self, tool_use: dict[str, Any], tool_calls: list[ToolCall]) -> dict[str, Any]:
        """Runs one requested tool, logging it as a Computation, and returns the toolResult for the model."""
        tool = TOOLS.get(tool_use["name"])
        if tool is None:
            return _tool_result(tool_use, {"error": f"Unknown tool {tool_use['name']!r}."}, error=True)
        try:
            args = tool.args_model.model_validate(tool_use["input"])
        except ValidationError as error:
            return _tool_result(tool_use, {"error": str(error)}, error=True)

        result = tool.run(self.context, args)
        computation = Computation(
            tool=tool.name,
            args=args.model_dump(mode="json", exclude_none=True),
            result=result.model_dump(mode="json"),
        )
        tool_calls.append(
            ToolCall(
                computation=computation,
                invoice_numbers=result.invoice_numbers,
                policy_sections=result.policy_sections,
                vendor_ids=result.vendor_ids,
            )
        )
        return _tool_result(tool_use, computation.result)


def _tool_result(tool_use: dict[str, Any], content: dict[str, Any], error: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"toolUseId": tool_use["toolUseId"], "content": [{"json": json.loads(json.dumps(content))}]}
    if error:
        result["status"] = "error"
    return {"toolResult": result}
