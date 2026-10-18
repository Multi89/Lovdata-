from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Sett offentlig serveradresse i GPT Action-skjemaet.")
    parser.add_argument("server_url", help="For eksempel https://norsk-lovhjelp.example")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("gpt/openapi-actions-ready.yaml"),
    )
    args = parser.parse_args()

    server_url = args.server_url.rstrip("/")
    if not server_url.startswith("https://"):
        parser.error("Serveradressen må starte med https://")

    source = Path("gpt/openapi-actions.yaml").read_text(encoding="utf-8")
    rendered = source.replace("https://REPLACE-WITH-YOUR-DOMAIN.example", server_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
