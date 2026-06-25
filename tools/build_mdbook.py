#!/usr/bin/env python3
"""Generate mdBook Markdown from the LaTeX specification sources."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOK_SRC = ROOT / "book-src"
SECTION_ORDER = [
    "introduction",
    "notation",
    "serialization",
    "ledger-model",
    "transactions",
    "script",
    "blocks",
    "pow",
    "consensus",
    "mempool",
    "p2p",
    "acknowledgements",
    "constants",
    "parameters",
    "rpc",
]

APPENDIX_TITLES = {
    "constants": "Appendix A. Constants",
    "parameters": "Appendix B. Mainnet Parameters",
    "rpc": "Appendix C. Remote Procedure Calls (RPC)",
}


def clean_book_src() -> None:
    if BOOK_SRC.exists():
        shutil.rmtree(BOOK_SRC)
    (BOOK_SRC / "chapters").mkdir(parents=True)
    (BOOK_SRC / "assets").mkdir()
    (BOOK_SRC / "pdf").mkdir()
    (BOOK_SRC / "theme").mkdir()


def copy_assets() -> None:
    for name in [
        "bitcoin-core-code-cover-light.png",
        "bitcoin-core-code-cover-dark.png",
        "bitcoin-logo-reference.png",
    ]:
        src = ROOT / "assets" / name
        if src.exists():
            shutil.copy2(src, BOOK_SRC / "assets" / name)
    for name in ["protocol.pdf", "protocol-dark.pdf"]:
        src = ROOT / "out" / name
        if src.exists():
            shutil.copy2(src, BOOK_SRC / "pdf" / name)


def strip_balanced_command(text: str, command: str) -> str:
    pattern = "\\" + command + "{"
    while pattern in text:
        start = text.find(pattern)
        brace = start + len(pattern) - 1
        depth = 0
        end = brace
        for i in range(brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        inner = text[brace + 1 : end]
        text = text[:start] + inner + text[end + 1 :]
    return text


def convert_inline(text: str) -> str:
    text = text.strip()
    text = text.replace("~", " ")
    text = text.replace("\\newline", " ")
    text = text.replace("\\par", "")
    text = text.replace("\\ldots", "...")
    text = text.replace("\\cdot", "*")
    text = text.replace("\\le", "<=")
    text = text.replace("\\ge", ">=")
    text = text.replace("\\ne", "!=")
    text = text.replace("\\top", "true")
    text = text.replace("\\bot", "false")
    text = text.replace("\\&", "&")
    text = text.replace("\\_", "_")
    text = text.replace("\\%", "%")
    text = re.sub(r"\\bip\{([^}]*)\}", r"BIP \1", text)
    text = re.sub(r"\\code\{([^{}]*)\}", r"`\1`", text)
    text = re.sub(r"\\term\{([^{}]*)\}", r"*\1*", text)
    text = re.sub(r"\\textbf\{([^{}]*)\}", r"**\1**", text)
    text = re.sub(r"\\textit\{([^{}]*)\}", r"*\1*", text)
    text = re.sub(r"\\small\s*", "", text)
    text = re.sub(r"\\scriptsize\s*", "", text)
    text = re.sub(r"\\cite\{([^}]*)\}", lambda m: f"(sources: {m.group(1)})", text)
    text = re.sub(r"\\ref\{sec:([^}]*)\}", lambda m: m.group(1).replace("-", " ").title(), text)
    text = re.sub(r"\\ref\{app:([^}]*)\}", lambda m: m.group(1).replace("-", " ").title(), text)
    text = re.sub(r"\\\((.*?)\\\)", r"$\1$", text)
    text = strip_balanced_command(text, "operatorname")
    text = strip_balanced_command(text, "mathrm")
    text = strip_balanced_command(text, "text")
    text = text.replace("{", "").replace("}", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_row(row: str) -> list[str]:
    row = row.strip()
    row = re.sub(r"\\\\\s*$", "", row)
    return [convert_inline(cell) for cell in re.split(r"(?<!\\)&", row)]


def flush_paragraph(out: list[str], paragraph: list[str]) -> None:
    if paragraph:
        out.append(convert_inline(" ".join(paragraph)))
        out.append("")
        paragraph.clear()


def convert_table(lines: list[str], start: int, out: list[str]) -> int:
    rows: list[list[str]] = []
    pending = ""
    i = start + 1
    while i < len(lines):
        raw = lines[i].strip()
        if raw.startswith("\\end{longtable}"):
            break
        if not raw or raw.startswith("\\toprule") or raw.startswith("\\midrule") or raw.startswith("\\bottomrule"):
            i += 1
            continue
        if raw.startswith("\\multicolumn"):
            match = re.search(r"\\multicolumn\{[^}]+\}\{[^}]+\}\{(.+)\}\s*\\\\", raw)
            if match:
                title = convert_inline(match.group(1))
                out.append(f"**{title}**")
                out.append("")
            i += 1
            continue
        pending = f"{pending} {raw}".strip()
        if pending.endswith("\\\\"):
            cells = split_row(pending)
            if len(cells) >= 2:
                rows.append(cells)
            pending = ""
        i += 1

    if rows:
        width = max(len(row) for row in rows)
        normalized = [row + [""] * (width - len(row)) for row in rows]
        header, body = normalized[0], normalized[1:]
        out.append("| " + " | ".join(header) + " |")
        out.append("| " + " | ".join(["---"] * width) + " |")
        for row in body:
            out.append("| " + " | ".join(row) + " |")
        out.append("")
    return i


def convert_tex(path: Path, appendix_title: str | None = None) -> str:
    lines = path.read_text().splitlines()
    out: list[str] = []
    paragraph: list[str] = []
    in_math = False
    in_enumerate = False
    in_itemize = False
    item_number = 1
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            flush_paragraph(out, paragraph)
            i += 1
            continue

        if line.startswith("\\label"):
            i += 1
            continue

        section = re.match(r"\\section\{(.+)\}", line)
        appendix = re.match(r"\\appendixsection\{(.+)\}", line)
        subsection = re.match(r"\\subsection\{(.+)\}", line)
        if section or appendix:
            flush_paragraph(out, paragraph)
            title = appendix_title or convert_inline((section or appendix).group(1))
            out.append(f"# {title}")
            out.append("")
            i += 1
            continue
        if subsection:
            flush_paragraph(out, paragraph)
            out.append(f"## {convert_inline(subsection.group(1))}")
            out.append("")
            i += 1
            continue

        if line.startswith("\\begin{longtable}"):
            flush_paragraph(out, paragraph)
            i = convert_table(lines, i, out)
            i += 1
            continue

        if line.startswith("\\begin{enumerate}"):
            flush_paragraph(out, paragraph)
            in_enumerate = True
            item_number = 1
            i += 1
            continue
        if line.startswith("\\end{enumerate}"):
            flush_paragraph(out, paragraph)
            in_enumerate = False
            out.append("")
            i += 1
            continue
        if line.startswith("\\begin{itemize}"):
            flush_paragraph(out, paragraph)
            in_itemize = True
            i += 1
            continue
        if line.startswith("\\end{itemize}"):
            flush_paragraph(out, paragraph)
            in_itemize = False
            out.append("")
            i += 1
            continue
        if line.startswith("\\item"):
            flush_paragraph(out, paragraph)
            item_text = convert_inline(line.replace("\\item", "", 1))
            if in_enumerate:
                out.append(f"{item_number}. {item_text}")
                item_number += 1
            elif in_itemize:
                out.append(f"- {item_text}")
            i += 1
            continue

        if line == "\\[":
            flush_paragraph(out, paragraph)
            out.append("$$")
            in_math = True
            i += 1
            continue
        if line == "\\]":
            out.append("$$")
            out.append("")
            in_math = False
            i += 1
            continue
        if in_math:
            out.append(raw)
            i += 1
            continue

        if line.startswith("\\begin{") or line.startswith("\\end{"):
            i += 1
            continue

        paragraph.append(line)
        i += 1

    flush_paragraph(out, paragraph)
    return "\n".join(out).strip() + "\n"


def title_for_section(slug: str, markdown: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return slug.replace("-", " ").title()


def write_index() -> None:
    cover = "assets/bitcoin-core-code-cover-light.png"
    text = f"""# Bitcoin Protocol Specification

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/bitcoin-core-code-cover-dark.png">
  <img alt="Bitcoin Protocol Specification cover" src="{cover}">
</picture>

Bitcoin is the peer-to-peer electronic cash protocol and payment network
introduced by Satoshi Nakamoto. This book is generated from the LaTeX
specification in this repository.

## Read

- [PDF](pdf/protocol.pdf)
- [Dark PDF](pdf/protocol-dark.pdf)
- [GitHub repository](https://github.com/Chainscore/bitcoin-spec)

## Scope

This specification covers consensus rules, primitive data structures,
serialization, transactions, Script execution, blocks, proof of work, mempool
behavior, peer networking, constants, and network parameters.
"""
    (BOOK_SRC / "index.md").write_text(text)


def write_summary(chapters: list[tuple[str, str]]) -> None:
    lines = ["# Summary", "", "- [Overview](index.md)"]
    for slug, title in chapters:
        lines.append(f"- [{title}](chapters/{slug}.md)")
    (BOOK_SRC / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    clean_book_src()
    copy_assets()
    (BOOK_SRC / "theme" / "custom.css").write_text(
        "img { max-width: 100%; }\n"
        ".content main { line-height: 1.55; }\n"
        "table { font-size: 0.92em; }\n"
    )
    write_index()

    chapters: list[tuple[str, str]] = []
    for slug in SECTION_ORDER:
        path = ROOT / "sections" / f"{slug}.tex"
        markdown = convert_tex(path, APPENDIX_TITLES.get(slug))
        title = title_for_section(slug, markdown)
        (BOOK_SRC / "chapters" / f"{slug}.md").write_text(markdown)
        chapters.append((slug, title))
    write_summary(chapters)


if __name__ == "__main__":
    main()
