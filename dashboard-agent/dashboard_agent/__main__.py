"""CLI : python -m dashboard_agent donnees.csv -o dashboard.html"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .engine import SpecError, compute_dashboard
from .loader import load_table, profile_dataframe
from .render import write_html
from .spec import Dashboard


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="dashboard_agent",
        description="Agent IA : choisit les KPI et les visuels d'un dashboard à partir d'un fichier de données.",
    )
    p.add_argument("data", help="Fichier de données (csv, tsv, xlsx, json, parquet)")
    p.add_argument("-o", "--output", help="Fichier HTML de sortie (défaut : <data>.dashboard.html)")
    p.add_argument("--objectif", help="Question métier ou public visé, ex. « suivi mensuel pour la direction commerciale »")
    p.add_argument("--sheet", help="Feuille Excel à lire (nom ou index)")
    p.add_argument("--spec", help="Rendre une spec JSON existante sans appeler l'IA (après retouche manuelle par ex.)")
    p.add_argument("--profile", action="store_true", help="Afficher seulement le profil des colonnes")
    p.add_argument("--model", default="claude-opus-5-5")
    p.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    args = p.parse_args(argv)

    data_path = Path(args.data)
    sheet = int(args.sheet) if args.sheet and args.sheet.isdigit() else args.sheet
    df = load_table(data_path, sheet=sheet)
    log = lambda msg: print(msg, file=sys.stderr)  # noqa: E731
    log(f"{len(df)} lignes × {df.shape[1]} colonnes chargées depuis {data_path.name}")

    if args.profile:
        print(json.dumps(profile_dataframe(df, data_path.name), ensure_ascii=False, indent=2, default=str))
        return 0

    output = Path(args.output) if args.output else data_path.with_suffix(".dashboard.html")
    spec_path = output.with_suffix(".spec.json")

    if args.spec:
        spec = Dashboard.model_validate_json(Path(args.spec).read_text(encoding="utf-8"))
    else:
        from .agent import AgentError, DashboardAgent

        log(f"L'agent ({args.model}, effort {args.effort}) analyse les données…")
        try:
            result = DashboardAgent(model=args.model, effort=args.effort, on_event=log).run(
                df, data_path.name, args.objectif
            )
        except AgentError as e:
            log(f"Échec : {e}")
            return 1
        spec = result.spec
        spec_path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
        log(f"Spec enregistrée : {spec_path} ({result.turns} tours, {result.usage})")

    try:
        data = compute_dashboard(df, spec)
    except SpecError as e:
        log(f"Spec invalide :\n{e}")
        return 1
    write_html(data, output)
    log(f"Dashboard : {output}  ({len(spec.kpis)} KPI, {len(spec.charts)} graphiques)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
