"""Rich logger and console formatting for Justice AI."""

import logging
import sys

try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

_CONSOLE = Console() if HAS_RICH else None

def get_console():
    return _CONSOLE

def get_logger(name: str = "justice_ai") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        if HAS_RICH:
            handler = RichHandler(
                console=_CONSOLE,
                rich_tracebacks=True,
                show_time=True,
                show_path=False
            )
        else:
            handler = logging.StreamHandler(sys.stdout)
            fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(name)s: %(message)s", "%H:%M:%S")
            handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger

def print_header(title: str, subtitle: str = ""):
    if HAS_RICH:
        content = f"[bold cyan]{title}[/bold cyan]"
        if subtitle:
            content += f"\n[dim]{subtitle}[/dim]"
        _CONSOLE.print(Panel(content, border_style="blue", expand=False))
    else:
        print(f"\n=== {title} ===")
        if subtitle:
            print(f"    {subtitle}")

def print_summary_table(rows: list, headers: list = None, title: str = "Pipeline Results"):
    if HAS_RICH:
        table = Table(title=title, show_header=True, header_style="bold magenta")
        headers = headers or ["Model / Stage", "Metric", "Value", "Paper Benchmark", "Difference"]
        for h in headers:
            table.add_column(h)
        for r in rows:
            table.add_row(*[str(x) for x in r])
        _CONSOLE.print(table)
    else:
        print(f"\n--- {title} ---")
        for r in rows:
            print(" | ".join(str(x) for x in r))
