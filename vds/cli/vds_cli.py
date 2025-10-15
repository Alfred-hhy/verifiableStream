from __future__ import annotations

import json
import os
import sys
from typing import Optional

import click


@click.group()
def cli() -> None:
    """vds-cli: demo commands for VDS schemes (scaffold)."""


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--curve", type=str, default="MNT224")
@click.option("--q", "q_branch", type=int, default=64)
@click.option("--store", type=click.Path(), required=False)
def init(scheme: str, curve: str, q_branch: int, store: Optional[str]) -> None:
    """Initialize scheme state (skeleton)."""
    click.echo(
        json.dumps(
            {
                "ok": True,
                "note": "Scaffold only. Crypto not implemented.",
                "scheme": scheme,
                "curve": curve,
                "q": q_branch,
                "store": store or "(memory)",
            }
        )
    )


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--data", type=str, required=True, help="hex data or file path")
def append(scheme: str, data: str) -> None:
    click.echo(json.dumps({"ok": False, "error": "Not implemented in scaffold", "scheme": scheme}))


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--index", type=int, required=True)
@click.option("--out", type=str, required=False)
def query(scheme: str, index: int, out: Optional[str]) -> None:
    click.echo(json.dumps({"ok": False, "error": "Not implemented in scaffold", "scheme": scheme, "index": index}))


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--index", type=int, required=True)
@click.option("--data", type=str, required=True)
@click.option("--proof", type=str, required=True)
def verify(scheme: str, index: int, data: str, proof: str) -> None:
    click.echo(json.dumps({"ok": False, "error": "Not implemented in scaffold"}))


@cli.command()
@click.option("--scheme", type=click.Choice(["cvc", "acc"]), required=True)
@click.option("--index", type=int, required=True)
@click.option("--data", type=str, required=True)
def update(scheme: str, index: int, data: str) -> None:
    click.echo(json.dumps({"ok": False, "error": "Not implemented in scaffold"}))


if __name__ == "__main__":
    cli()

