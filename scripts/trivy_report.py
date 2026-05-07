#!/usr/bin/env python3
"""Génère un rapport lisible (Markdown + HTML) à partir des sorties JSON Trivy.

Usage:
    python trivy_report.py --input reports/ --out-md report.md --out-html report.html \
        [--fail-on CRITICAL]

Le script :
  * fusionne plusieurs rapports JSON Trivy (un par image scannée),
  * compte les vulnérabilités par sévérité,
  * liste le top N des CVE les plus critiques,
  * écrit un Markdown (utilisable dans GITHUB_STEP_SUMMARY),
  * écrit une page HTML autoporteuse (artefact CI),
  * sort en code != 0 si le seuil `--fail-on` est atteint (CI bloquante).
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
SEVERITY_RANK = {sev: i for i, sev in enumerate(SEVERITIES)}


@dataclass
class Vulnerability:
    image: str
    target: str
    pkg: str
    installed_version: str
    fixed_version: str
    vuln_id: str
    severity: str
    title: str

    @property
    def rank(self) -> int:
        return SEVERITY_RANK.get(self.severity, len(SEVERITIES))


@dataclass
class ImageReport:
    image: str
    vulnerabilities: list[Vulnerability] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        c = {sev: 0 for sev in SEVERITIES}
        for v in self.vulnerabilities:
            c[v.severity] = c.get(v.severity, 0) + 1
        return c


def load_trivy_json(path: Path) -> ImageReport:
    """Charge un fichier JSON Trivy et renvoie un ImageReport.

    Trivy peut être appelé avec différentes versions du schéma ; on supporte
    les deux plus courants (clé racine `Results` avec `ArtifactName`).
    """
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    image = data.get("ArtifactName") or path.stem
    report = ImageReport(image=image)

    for result in data.get("Results", []) or []:
        target = result.get("Target", "")
        for vuln in result.get("Vulnerabilities", []) or []:
            severity = (vuln.get("Severity") or "UNKNOWN").upper()
            report.vulnerabilities.append(
                Vulnerability(
                    image=image,
                    target=target,
                    pkg=vuln.get("PkgName", "?"),
                    installed_version=vuln.get("InstalledVersion", "?"),
                    fixed_version=vuln.get("FixedVersion", "") or "—",
                    vuln_id=vuln.get("VulnerabilityID", "?"),
                    severity=severity,
                    title=(vuln.get("Title") or vuln.get("Description") or "")[:140],
                )
            )
    return report


def aggregate_counts(reports: Iterable[ImageReport]) -> dict[str, int]:
    total = {sev: 0 for sev in SEVERITIES}
    for r in reports:
        for sev, n in r.counts().items():
            total[sev] = total.get(sev, 0) + n
    return total


def render_markdown(reports: list[ImageReport], top_n: int = 15) -> str:
    totals = aggregate_counts(reports)
    lines: list[str] = []
    lines.append("# Rapport de vulnérabilités Trivy\n")
    lines.append("## Résumé global\n")
    lines.append("| Sévérité | Nombre |")
    lines.append("|----------|-------:|")
    for sev in SEVERITIES:
        lines.append(f"| **{sev}** | {totals.get(sev, 0)} |")
    lines.append("")

    lines.append("## Détail par image\n")
    lines.append("| Image | CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN |")
    lines.append("|-------|---------:|-----:|-------:|----:|--------:|")
    for r in reports:
        c = r.counts()
        lines.append(
            f"| `{r.image}` | {c['CRITICAL']} | {c['HIGH']} | {c['MEDIUM']} | "
            f"{c['LOW']} | {c['UNKNOWN']} |"
        )
    lines.append("")

    all_vulns = sorted(
        (v for r in reports for v in r.vulnerabilities),
        key=lambda v: (v.rank, v.image, v.pkg),
    )
    if all_vulns:
        lines.append(f"## Top {top_n} des vulnérabilités les plus critiques\n")
        lines.append("| Sévérité | Image | Paquet | Version | Fix | CVE | Titre |")
        lines.append("|----------|-------|--------|---------|-----|-----|-------|")
        for v in all_vulns[:top_n]:
            lines.append(
                f"| {v.severity} | `{v.image}` | {v.pkg} | {v.installed_version} | "
                f"{v.fixed_version} | {v.vuln_id} | {v.title.replace('|', '/')} |"
            )
    else:
        lines.append("Aucune vulnérabilité détectée.")

    return "\n".join(lines) + "\n"


def render_html(reports: list[ImageReport]) -> str:
    totals = aggregate_counts(reports)
    color = {
        "CRITICAL": "#b91c1c",
        "HIGH": "#ea580c",
        "MEDIUM": "#ca8a04",
        "LOW": "#0284c7",
        "UNKNOWN": "#6b7280",
    }

    summary_cards = "".join(
        f'<div class="card" style="border-left:6px solid {color[s]}">'
        f'<div class="num">{totals[s]}</div><div class="lbl">{s}</div></div>'
        for s in SEVERITIES
    )

    rows_per_image = "".join(
        "<tr>"
        f"<td><code>{html.escape(r.image)}</code></td>"
        + "".join(f"<td>{r.counts()[s]}</td>" for s in SEVERITIES)
        + "</tr>"
        for r in reports
    )

    all_vulns = sorted(
        (v for r in reports for v in r.vulnerabilities),
        key=lambda v: (v.rank, v.image, v.pkg),
    )
    rows_vulns = "".join(
        "<tr>"
        f"<td style='color:{color.get(v.severity, '#000')};font-weight:600'>{v.severity}</td>"
        f"<td><code>{html.escape(v.image)}</code></td>"
        f"<td>{html.escape(v.pkg)}</td>"
        f"<td>{html.escape(v.installed_version)}</td>"
        f"<td>{html.escape(v.fixed_version)}</td>"
        f"<td><a href='https://nvd.nist.gov/vuln/detail/{html.escape(v.vuln_id)}'>"
        f"{html.escape(v.vuln_id)}</a></td>"
        f"<td>{html.escape(v.title)}</td>"
        "</tr>"
        for v in all_vulns
    )

    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<title>Rapport Trivy</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 24px; color: #111; }}
  h1 {{ margin-bottom: 4px; }}
  .summary {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }}
  .card {{ background: #f9fafb; border-radius: 8px; padding: 12px 18px; min-width: 110px; }}
  .num {{ font-size: 28px; font-weight: 700; }}
  .lbl {{ font-size: 12px; color: #555; letter-spacing: .04em; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 14px; }}
  th, td {{ border: 1px solid #e5e7eb; padding: 6px 10px; text-align: left; }}
  th {{ background: #f3f4f6; }}
  code {{ background: #f3f4f6; padding: 1px 4px; border-radius: 3px; }}
</style></head>
<body>
  <h1>Rapport de vulnérabilités Trivy</h1>
  <p>Généré automatiquement par la pipeline DevSecOps.</p>
  <div class="summary">{summary_cards}</div>

  <h2>Détail par image</h2>
  <table>
    <thead><tr><th>Image</th>{''.join(f'<th>{s}</th>' for s in SEVERITIES)}</tr></thead>
    <tbody>{rows_per_image}</tbody>
  </table>

  <h2>Toutes les vulnérabilités ({len(all_vulns)})</h2>
  <table>
    <thead><tr>
      <th>Sévérité</th><th>Image</th><th>Paquet</th><th>Version</th>
      <th>Fix</th><th>CVE</th><th>Titre</th>
    </tr></thead>
    <tbody>{rows_vulns or '<tr><td colspan=7>Aucune vulnérabilité.</td></tr>'}</tbody>
  </table>
</body></html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Dossier contenant les fichiers JSON Trivy.",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=Path("trivy-report.md"),
        help="Chemin du rapport Markdown.",
    )
    parser.add_argument(
        "--out-html",
        type=Path,
        default=Path("trivy-report.html"),
        help="Chemin du rapport HTML.",
    )
    parser.add_argument(
        "--fail-on",
        choices=SEVERITIES + ["NONE"],
        default="NONE",
        help="Sévérité minimale qui fait échouer le job (NONE = jamais).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=15,
        help="Nombre de CVE listées dans le top du Markdown.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.input.is_dir():
        print(f"[ERREUR] dossier introuvable : {args.input}", file=sys.stderr)
        return 2

    json_files = sorted(args.input.glob("*.json"))
    if not json_files:
        print(f"[INFO] aucun JSON Trivy trouvé dans {args.input}")
        return 0

    reports = [load_trivy_json(p) for p in json_files]
    args.out_md.write_text(render_markdown(reports, top_n=args.top), encoding="utf-8")
    args.out_html.write_text(render_html(reports), encoding="utf-8")

    totals = aggregate_counts(reports)
    print("Résumé :", ", ".join(f"{s}={totals[s]}" for s in SEVERITIES))
    print(f"Markdown -> {args.out_md}")
    print(f"HTML     -> {args.out_html}")

    if args.fail_on != "NONE":
        threshold = SEVERITY_RANK[args.fail_on]
        blocking = sum(n for s, n in totals.items() if SEVERITY_RANK[s] <= threshold)
        if blocking > 0:
            print(
                f"[FAIL] {blocking} vulnérabilité(s) >= {args.fail_on} détectée(s).",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
