"""Génère examples/ventes.csv : un jeu de ventes fictif pour tester l'agent."""

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 3000

regions = ["Île-de-France", "Auvergne-Rhône-Alpes", "Occitanie", "Nouvelle-Aquitaine", "Hauts-de-France", "Grand Est", "Bretagne"]
canaux = ["Web", "Magasin", "Marketplace"]
catalogue = {
    "Informatique": [("Ordinateur portable", 899), ("Écran 27\"", 279), ("Clavier", 59)],
    "Téléphonie": [("Smartphone", 649), ("Écouteurs", 129), ("Coque", 19)],
    "Maison": [("Aspirateur", 249), ("Cafetière", 89), ("Lampe", 39)],
    "Loisirs": [("Console", 449), ("Jeu vidéo", 59), ("Drone", 329)],
}

dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 626, n), unit="D")
# Saisonnalité : plus de commandes en fin d'année
boost = np.where(dates.month.isin([11, 12]), 1.6, 1.0)
keep = rng.random(n) < boost / 1.6
dates = dates[keep]
m = len(dates)

cats = rng.choice(list(catalogue), m, p=[0.35, 0.3, 0.2, 0.15])
rows = []
for i in range(m):
    produit, prix = catalogue[cats[i]][rng.integers(0, 3)]
    qte = int(rng.choice([1, 1, 1, 2, 2, 3]))
    remise = float(rng.choice([0, 0, 0.05, 0.1, 0.2]))
    ca = round(prix * qte * (1 - remise), 2)
    taux_marge = {"Informatique": 0.18, "Téléphonie": 0.22, "Maison": 0.35, "Loisirs": 0.28}[cats[i]]
    rows.append(
        {
            "date_commande": dates[i].strftime("%d/%m/%Y"),
            "commande_id": f"CMD-{100000 + i}",
            "client_id": f"CLI-{rng.integers(1, 900):04d}",
            "region": rng.choice(regions, p=[0.3, 0.17, 0.12, 0.12, 0.11, 0.1, 0.08]),
            "canal": rng.choice(canaux, p=[0.5, 0.35, 0.15]),
            "categorie": cats[i],
            "produit": produit,
            "quantite": qte,
            "remise_pct": int(remise * 100),
            "chiffre_affaires": f"{ca:.2f}".replace(".", ","),
            "marge": f"{ca * (taux_marge - remise / 2) + rng.normal(0, 5):.2f}".replace(".", ","),
            "note_satisfaction": int(np.clip(round(rng.normal(4.1 - remise * 2, 0.8)), 1, 5)),
        }
    )

df = pd.DataFrame(rows).sort_values("commande_id")
out = Path(__file__).with_name("ventes.csv")
df.to_csv(out, sep=";", index=False)
print(f"{len(df)} lignes -> {out}")
