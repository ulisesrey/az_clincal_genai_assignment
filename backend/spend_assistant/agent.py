"""Agent loop: one stateless, single-turn question answered with typed tools over Converse."""

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from spend_assistant.evidence import Citations, Computation, Evidence, ToolCall, assemble_evidence
from spend_assistant.ledger import SpendData
from spend_assistant.llm import ChatProvider
from spend_assistant.policy import Policy
from spend_assistant.prompt import (
    DECLINE,
    SUBMIT_ANSWER,
    AnswerStatus,
    Decline,
    FinalAnswer,
    system_prompt,
    tool_specs,
)
from spend_assistant.tools import TOOLS, Tool

MAX_TOOL_ITERATIONS = 5

_FINISHERS: dict[str, type[FinalAnswer] | type[Decline]] = {SUBMIT_ANSWER: FinalAnswer, DECLINE: Decline}

_REPROMPT = (
    f"Finish by calling {SUBMIT_ANSWER} with your answer and its citations, or {DECLINE} with the reason; "
    "a plain-text reply is not accepted."
)


class AskResponse(BaseModel):
    answer: str
    status: AnswerStatus
    evidence: Evidence
    warnings: list[str] = Field(default_factory=list)


class Agent:
    def __init__(self, data: SpendData, provider: ChatProvider, policy: Policy) -> None:
        self.data = data
        self.provider = provider
        self.policy = policy
        self.system_prompt = system_prompt(policy)
        self.tool_specs = tool_specs()

    def ask(self, question: str) -> AskResponse:
        messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": question}]}]
        tool_calls: list[ToolCall] = []
        retried_invalid_arguments = False

        for _ in range(MAX_TOOL_ITERATIONS):
            message = self.provider.converse(self.system_prompt, messages, self.tool_specs)
            messages.append(message)
            content = message.get("content", [])
            tool_uses = [block["toolUse"] for block in content if "toolUse" in block]
            if not tool_uses:
                messages.append({"role": "user", "content": [{"text": _REPROMPT}]})
                continue

            results = []
            final: FinalAnswer | Decline | None = None
            invalid_arguments = False
            for tool_use in tool_uses:
                name = tool_use["name"]
                tool = TOOLS.get(name)
                schema = _FINISHERS.get(name) or (tool.args_model if tool else None)
                if schema is None:
                    results.append(_tool_result(tool_use, {"error": f"Unknown tool {name!r}."}, error=True))
                    continue
                try:
                    args = schema.model_validate(tool_use["input"])
                except ValidationError as error:
                    invalid_arguments = True
                    results.append(_tool_result(tool_use, {"error": str(error)}, error=True))
                    continue
                if isinstance(args, (FinalAnswer, Decline)):
                    final = final or args
                elif tool is not None:
                    results.append(self._run_tool(tool_use, tool, args, tool_calls))
            if final is not None:
                return self._respond(final.status, final.text, final, tool_calls)
            if invalid_arguments:
                if retried_invalid_arguments:
                    return self._decline(
                        "The question could not be turned into valid tool arguments, even after one correction.",
                        tool_calls,
                    )
                retried_invalid_arguments = True
            messages.append({"role": "user", "content": results})

        return self._decline(f"No answer was reached within {MAX_TOOL_ITERATIONS} tool-call iterations.", tool_calls)

    def _decline(self, reason: str, tool_calls: list[ToolCall]) -> AskResponse:
        return self._respond("declined", reason, Citations(), tool_calls)

    def _respond(
        self, status: AnswerStatus, answer: str, citations: Citations, tool_calls: list[ToolCall]
    ) -> AskResponse:
        evidence, warnings = assemble_evidence(self.data, self.policy, tool_calls, citations)
        return AskResponse(answer=answer, status=status, evidence=evidence, warnings=warnings)

    def _run_tool(
        self, tool_use: dict[str, Any], tool: Tool, args: BaseModel, tool_calls: list[ToolCall]
    ) -> dict[str, Any]:
        """Runs one requested tool, logging it as a Computation, and returns the toolResult for the model."""
        result = tool.run(self.data, args)
        computation = Computation(
            tool=tool.name,
            args=args.model_dump(mode="json", exclude_unset=True, exclude_none=True),
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
