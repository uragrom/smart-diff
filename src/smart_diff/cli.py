"""CLI: smart-diff and git-dd. Config group for default model and language."""

import sys
from pathlib import Path

import click

from .config import DEFAULT_MODEL, DEEP_MODEL, VALID_LANGS
from .git_utils import GitError, get_diff_for_llm
from .html_report import build_report_data, write_report
from .i18n import t
from .ollama_client import analyze_diff, generate_commit_message
from .output import (
    print_analysis,
    print_commit_message,
    print_error,
    print_html_report_written,
    print_info,
)
from .user_config import get_config_path, load_config, save_config


def _print_ollama_error(exc: Exception, model: str, lang: str) -> None:
    """Show a clear Ollama error with hints."""
    msg = str(exc).strip()
    if "connect" in msg.lower() or "connection" in msg.lower():
        print_error(t("ollama_connect", lang), lang)
    elif "404" in msg or "not found" in msg.lower():
        print_error(t("ollama_model_not_found", lang, model=model), lang)
    else:
        print_error(f"{msg}\n{t('ollama_hint', lang, model=model)}", lang)


def _get_diff(
    staged: bool,
    ref: str | None,
    cwd: Path | None,
    auto_last_commit: bool = True,
) -> str:
    diff = get_diff_for_llm(staged=staged, ref=ref, cwd=cwd)
    if not diff.strip() and auto_last_commit and ref is None and not staged:
        try:
            diff = get_diff_for_llm(staged=False, ref="HEAD", cwd=cwd)
            if diff.strip():
                return diff, True  # True = we're analyzing last commit
        except GitError:
            pass
    return diff, False


@click.group()
@click.version_option(prog_name="smart-diff")
def cli() -> None:
    """Smart Diff — analyze changes via local LLM (Ollama)."""


@click.group("config", help="Set or show default model and language.")
def config_group() -> None:
    pass


@config_group.command("set")
@click.argument("key", type=click.Choice(["model", "lang", "report_theme", "report_auto_open"]))
@click.argument("value", required=True)
def config_set(key: str, value: str) -> None:
    """Set default model, language, or report options. E.g. config set report_theme light."""
    if key == "lang" and value not in VALID_LANGS:
        raise click.BadParameter(f"lang must be one of: {', '.join(VALID_LANGS)}")
    if key == "report_theme" and value not in ("dark", "light"):
        raise click.BadParameter("report_theme must be: dark, light")
    if key == "report_auto_open":
        value = value.lower() in ("1", "true", "yes")
    save_config({key: value})
    if key == "model":
        click.echo(t("config_model_set", "en", model=value))
    elif key == "lang":
        click.echo(t("config_lang_set", "en", lang=value))
    elif key == "report_theme":
        click.echo(f"Report theme set to: {value}")
    else:
        click.echo(f"Report auto-open set to: {value}")


@config_group.command("show")
def config_show() -> None:
    """Show current config (model, language, report options)."""
    cfg = load_config()
    model = cfg.get("model") or DEFAULT_MODEL
    lang = cfg.get("lang") or "auto"
    theme = cfg.get("report_theme") or "dark"
    auto_open = cfg.get("report_auto_open", True)
    click.echo(t("config_show", "en", model=model, lang=lang))
    click.echo(f"report_theme = {theme}")
    click.echo(f"report_auto_open = {str(auto_open).lower()}")
    click.echo(t("config_path", "en", path=str(get_config_path())))


cli.add_command(config_group)


@cli.command()
@click.option("--staged", "-s", is_flag=True, help="Analyze only staged changes.")
@click.option("--ref", "-r", default=None, help="Analyze this commit (e.g. HEAD, HEAD~1).")
@click.option(
    "--model",
    "-m",
    default=None,
    help=f"Ollama model (overrides config). Default in config or {DEFAULT_MODEL}.",
)
@click.option(
    "--lang",
    "-l",
    type=click.Choice(["en", "ru", "auto"]),
    default=None,
    help="Output and LLM response language. Overrides config.",
)
@click.option("--commit-msg", is_flag=True, help="Generate only a commit message (one line).")
@click.option(
    "--cwd",
    type=click.Path(path_type=Path, exists=True, file_okay=False),
    default=None,
    help="Repo directory (default: current).",
)
@click.option(
    "--output-file",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Write commit message to file (for prepare-commit-msg hook).",
)
@click.option(
    "--html",
    "html_output",
    type=click.Path(path_type=Path),
    default=None,
    help="Write HTML report to this file (e.g. report.html). Click the path in the console to open in browser.",
)
def run(
    staged: bool,
    ref: str | None,
    model: str | None,
    lang: str | None,
    commit_msg: bool,
    cwd: Path | None,
    output_file: Path | None,
    html_output: Path | None,
) -> None:
    """
    Analyze diff or generate commit message.

    Examples:

      smart-diff run              analyze current changes (or last commit if clean)

      smart-diff run --staged      only staged

      smart-diff run --ref HEAD   last commit

      smart-diff run --commit-msg  generate commit message

      smart-diff config set model deepseek-r1   set default model

      smart-diff config set lang ru             set default language
    """
    cwd = cwd or Path.cwd()
    cfg = load_config()
    model = model or cfg.get("model") or DEFAULT_MODEL
    lang = lang or cfg.get("lang") or "auto"
    # For LLM we pass "en" or "ru"; "auto" stays as "auto"
    llm_lang = lang

    try:
        diff, analyzing_last = _get_diff(staged=staged, ref=ref, cwd=cwd)
    except GitError as e:
        print_error(str(e), lang if lang != "auto" else "en")
        sys.exit(1)

    if not diff.strip():
        print_error(
            t("no_changes", lang if lang != "auto" else "en"), lang if lang != "auto" else "en"
        )
        sys.exit(1)

    if analyzing_last:
        print_info(
            t("analyzing_last", lang if lang != "auto" else "en"), lang if lang != "auto" else "en"
        )

    if commit_msg:
        print_info(
            t("commit_msg_generating", lang if lang != "auto" else "en", model=model),
            lang if lang != "auto" else "en",
        )
        try:
            msg = generate_commit_message(diff, model, llm_lang)
            if output_file:
                output_file.write_text(msg, encoding="utf-8")
                print_info(
                    t("commit_written", lang if lang != "auto" else "en", path=str(output_file)),
                    lang if lang != "auto" else "en",
                )
            else:
                print_commit_message(msg, lang if lang != "auto" else "en")
        except Exception as e:
            _print_ollama_error(e, model, lang if lang != "auto" else "en")
            sys.exit(1)
        return

    print_info(
        t("model_label", lang if lang != "auto" else "en", model=model),
        lang if lang != "auto" else "en",
    )
    try:
        analysis = analyze_diff(diff, model, llm_lang)
        title = t("analysis_title", lang if lang != "auto" else "en")
        print_analysis(analysis, title=title, lang=lang if lang != "auto" else "en")

        if html_output:
            report_path = html_output.resolve()
            report_ref = ref if ref else ("HEAD" if analyzing_last else None)
            report_theme = cfg.get("report_theme") or "dark"
            report_auto_open = cfg.get("report_auto_open", True)
            data = build_report_data(
                diff=diff,
                analysis_md=analysis,
                staged=staged,
                ref=report_ref,
                model=model,
                lang=lang,
                theme=report_theme,
                cwd=cwd,
            )
            write_report(report_path, data, auto_open=report_auto_open)
            _locale = "en" if lang == "auto" else lang
            print_html_report_written(report_path, _locale)
    except Exception as e:
        _print_ollama_error(e, model, lang if lang != "auto" else "en")
        sys.exit(1)


def main() -> None:
    """Entry point: run as smart-diff or git-dd. No subcommand defaults to run (analyze)."""
    import sys as _sys

    args = _sys.argv[1:]
    first_arg = next((a for a in args if not a.startswith("-") and "=" not in a), None)
    if first_arg == "config":
        cli()
    elif first_arg == "run":
        cli()
    else:
        # No subcommand: default to "run" so "smart-diff" and "smart-diff -m x" run analysis
        if args and args[0] in ("--help", "-h", "--version", "-V"):
            cli()
        else:
            _sys.argv = [_sys.argv[0], "run"] + args
            cli()


if __name__ == "__main__":
    main()
