"""Terminal output via Rich. Uses i18n for prefixes/titles when lang is given."""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .i18n import t

console = Console()


def print_analysis(markdown_text: str, title: str = "Smart Diff", lang: str = "en") -> None:
    """Print LLM response as Markdown in a panel."""
    md = Markdown(markdown_text, code_theme="monokai")
    console.print(Panel(md, title=title, border_style="blue"))


def print_error(message: str, lang: str = "en") -> None:
    """Print error line with localized prefix."""
    prefix = t("error_prefix", lang)
    console.print(f"[red]{prefix}[/red] {message}")


def print_info(message: str, lang: str = "en") -> None:
    """Print dimmed info line."""
    console.print(f"[dim]{message}[/dim]")


def print_commit_message(message: str, lang: str = "en") -> None:
    """Print suggested commit message in a panel."""
    title = t("suggested_commit", lang)
    console.print(Panel(message, title=title, border_style="green"))
