import os
import sys

import uvicorn

from spend_assistant.app import create_app
from spend_assistant.data_pack import DataPackMissingError, load_data_pack, resolve_data_dir
from spend_assistant.fx import EcbRates
from spend_assistant.ledger import build_ledger
from spend_assistant.llm import BedrockProvider


def main() -> None:
    try:
        pack = load_data_pack(resolve_data_dir())
    except DataPackMissingError as error:
        print(f"Startup failed: {error}", file=sys.stderr)
        sys.exit(1)

    app = create_app(build_ledger(pack, EcbRates()), pack.policy_text, BedrockProvider())
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
