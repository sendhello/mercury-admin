#!/usr/bin/python
import subprocess

import typer

app = typer.Typer()


@app.command()
def makemigrations(text: str):
    """Create migration with text."""
    result = subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", f'"{text}"'],
        capture_output=True,
        text=True,
        check=False,
    )
    print("Log:", result.stdout)
    print("Errors:", result.stderr)


@app.command()
def migrate():
    """Upgrade migration."""
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True, check=False)
    print("Log:", result.stdout)
    print("Errors:", result.stderr)


@app.command()
def rollback(migrate_hash: str):
    """Downgrade migration."""
    result = subprocess.run(["alembic", "downgrade", migrate_hash], capture_output=True, text=True, check=False)
    print("Log:", result.stdout)
    print("Errors:", result.stderr)


if __name__ == "__main__":
    app()
