"""View HTML forense self-contained derivada do report canônico (WIRS-095)."""

# O template inline mantém CSS self-contained; suas linhas não são código Python.
# ruff: noqa: E501

from __future__ import annotations

from html import escape
from typing import Any

from wirs.domain import Severity
from wirs.reporting.canonical import CanonicalReport

_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; "
    "font-src 'none'; script-src 'none'; object-src 'none'; base-uri 'none'; "
    "form-action 'none'; frame-ancestors 'none'"
)


def _text(value: Any) -> str:
    """Escapa texto já redigido pelo modelo canônico."""
    return escape(str(value), quote=True)


def _cell(value: Any) -> str:
    return f"<td>{_text(value)}</td>"


def render_forensic_html(report: CanonicalReport) -> str:
    """Renderiza somente dados do CanonicalReport, sem consultar o Target."""
    data = report.to_dict()
    findings = data["findings"]
    coverage = data["coverage"]
    diagnoses = data["diagnoses"]
    artifacts = data["artifacts"]
    evidence = data["evidence"]
    provider_runs = data["provider_runs"]
    counts = {severity.value: 0 for severity in Severity}
    for finding in findings:
        counts[finding["severity"]] = counts.get(finding["severity"], 0) + 1

    finding_rows = []
    for finding in findings:
        attributes = finding.get("attributes", {})
        path = attributes.get("path", finding["artifact_ref"])
        finding_rows.append(
            "<article class='finding'>"
            f"<h3><span class='severity severity-{_text(finding['severity'])}'>"
            f"{_text(finding['severity'])}</span> {_text(finding['rule_id'])}</h3>"
            f"<p class='title'>{_text(finding['title'])}</p>"
            "<dl>"
            f"<dt>Arquivo/Artifact</dt>{_cell(path)}"
            f"<dt>Categoria</dt>{_cell(finding['category'])}"
            f"<dt>Confiança</dt>{_cell(finding['confidence']['class'])}"
            f"<dt>Evidence</dt>{_cell(', '.join(finding['evidence_refs']))}"
            "</dl></article>"
        )
    findings_html = "".join(finding_rows) or "<p class='empty'>Nenhum Finding.</p>"

    coverage_rows = "".join(
        "<tr>"
        + _cell(entry["capability"])
        + _cell(entry["state"])
        + _cell(entry["verified"])
        + _cell(entry["failed"])
        + _cell(entry["unavailable"])
        + "</tr>"
        for entry in coverage
    )
    diagnosis_html = (
        "".join(
            "<article class='diagnosis'>"
            f"<h3>{_text(item['rule_id'])}: {_text(item['title'])}</h3>"
            f"<p>{_text(item['summary'])}</p>"
            f"<p><strong>Confiança:</strong> {_text(item['confidence'])}</p>"
            f"<p><strong>Próximos checks:</strong> {_text(', '.join(item['recommended_next_checks']))}</p>"
            "</article>"
            for item in diagnoses
        )
        or "<p class='empty'>Nenhuma Diagnosis foi produzida nesta execução.</p>"
    )
    provider_rows = (
        "".join(
            "<tr>"
            + _cell(run["provider_id"])
            + _cell(run["status"])
            + _cell(run.get("reason", ""))
            + "</tr>"
            for run in provider_runs
        )
        or "<tr><td colspan='3'>Nenhuma execução de provider registrada.</td></tr>"
    )

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="{escape(_CSP, quote=True)}">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WIRS - relatório forense</title>
<style>
:root {{ color-scheme: light dark; --bg:#10151b; --panel:#18212b; --ink:#edf2f7; --muted:#a9b6c3; --line:#344453; --accent:#68d391; --danger:#fc8181; --warn:#f6ad55; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--bg); color:var(--ink); font:15px/1.5 system-ui,sans-serif; }}
main {{ max-width:1100px; margin:auto; padding:2rem 1rem 4rem; }} header {{ border-bottom:1px solid var(--line); margin-bottom:2rem; }}
h1,h2,h3 {{ line-height:1.2; }} h1 {{ font-size:clamp(1.8rem,4vw,3rem); }} h2 {{ margin-top:2.5rem; }}
.meta,.muted,.empty {{ color:var(--muted); }} .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:.75rem; }}
.metric,.finding,.diagnosis,.notice {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:1rem; }}
.metric strong {{ display:block; font-size:1.8rem; }} .severity {{ border-radius:999px; padding:.2rem .5rem; font-size:.75rem; font-weight:700; }}
.severity-critical,.severity-high {{ background:var(--danger); color:#241015; }} .severity-medium {{ background:var(--warn); color:#251a0c; }} .severity-low {{ background:#90cdf4; color:#10202b; }} .severity-info {{ background:#cbd5e0; color:#1a202c; }}
.finding,.diagnosis {{ margin:.75rem 0; }} .title {{ font-size:1.05rem; }} dl {{ display:grid; grid-template-columns:minmax(9rem, auto) 1fr; gap:.35rem .75rem; }} dt {{ color:var(--muted); font-weight:600; }} dd {{ margin:0; overflow-wrap:anywhere; }}
table {{ width:100%; border-collapse:collapse; margin:1rem 0; }} th,td {{ border-bottom:1px solid var(--line); padding:.6rem; text-align:left; overflow-wrap:anywhere; }} th {{ color:var(--muted); }}
.notice {{ border-left:4px solid var(--accent); }} @media print {{ :root {{ color-scheme:light; --bg:#fff; --panel:#fff; --ink:#111; --muted:#444; --line:#bbb; }} body {{ font-size:10pt; }} main {{ max-width:none; padding:.5cm; }} .finding,.diagnosis,.metric,.notice {{ break-inside:avoid; }} }}
</style></head><body><main>
<header><p class="meta">WIRS · relatório forense filesystem-only · schema {_text(data["schema_version"])}</p>
<h1>Resumo da investigação</h1><p>Target: <strong>{_text(data["manifest"]["target"]["root"])}</strong></p>
<p class="meta">Scan {_text(data["manifest"]["scan_id"])} · perfil {_text(data["manifest"]["profile"])} · gerado em {_text(data["manifest"]["generated_at"])}</p></header>
<section aria-labelledby="summary"><h2 id="summary">Summary</h2><div class="grid">{"".join(f'<div class="metric"><span>{_text(severity.name)}</span><strong>{counts.get(severity.value, 0)}</strong></div>' for severity in Severity)}</div></section>
<section aria-labelledby="findings"><h2 id="findings">Findings ({len(findings)})</h2>{findings_html}</section>
<section aria-labelledby="diagnoses"><h2 id="diagnoses">Diagnoses</h2>{diagnosis_html}</section>
<section aria-labelledby="coverage"><h2 id="coverage">Coverage</h2><table><thead><tr><th>Capability</th><th>State</th><th>Verified</th><th>Failed</th><th>Unavailable</th></tr></thead><tbody>{coverage_rows}</tbody></table></section>
<section aria-labelledby="timeline"><h2 id="timeline">Timeline</h2><p class="notice">Timeline não disponível: esta view cobre o fluxo filesystem-only. Logs temporais ainda não fazem parte deste report.</p></section>
<section aria-labelledby="appendices"><h2 id="appendices">Apêndices</h2><p class="muted">Metadados preservados do report canônico; conteúdo bruto do Target não é incluído.</p>
<h3>Artifacts ({len(artifacts)})</h3><p>{len(artifacts)} Artifact(s) referenciável(is) no modelo.</p>
<h3>Evidence ({len(evidence)})</h3><p>{len(evidence)} Evidence registrada(s), com provenance e redaction aplicadas.</p>
<h3>Provider runs</h3><table><thead><tr><th>Provider</th><th>Status</th><th>Motivo</th></tr></thead><tbody>{provider_rows}</tbody></table></section>
</main></body></html>
"""
