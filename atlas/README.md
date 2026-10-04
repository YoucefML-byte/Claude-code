# Atlas Torréfacteurs

Site vitrine et boutique d'une torréfaction de café de spécialité (marque fictive de démonstration).
HTML, CSS et JavaScript sans étape de build : ouvrez `index.html` dans un navigateur.

## Contenu

| Fichier | Rôle | Skill utilisée |
|---------|------|----------------|
| `index.html` | Site : fiche de torréfaction interactive, boutique et panier, recettes avec minuteur, abonnement, atelier, lettre d'information | ui-ux-pro-max, ui-styling, dataviz |
| `docs/brand-guidelines.md` | Charte : couleurs, typographie, logo, voix, messages | brand |
| `assets/design-tokens.json` / `.css` | Tokens en trois couches (primitive, sémantique, composant) | design-system |
| `assets/logo/*.svg` | Logo horizontal, version inversée, symbole seul | design (logo) |
| `assets/banners/lancement/` | Bannières Instagram 1080×1080 (×2) et en-tête X 1500×500, source HTML et PNG | banner-design |
| `presentation/index.html` | Présentation de marque en 6 diapositives avec graphique Chart.js | slides |

## Régénérer

```bash
# Tokens CSS depuis le JSON
node ../.claude/skills/design-system/scripts/generate-tokens.cjs --config assets/design-tokens.json -o assets/design-tokens.css
```

Les bannières PNG sont des captures des éléments de `assets/banners/lancement/banners.html` à leur taille exacte.

## Notes

- Thèmes clair et sombre, bouton de bascule dans l'en-tête.
- Le panier, le thème et la méthode de recette sont gardés dans le `localStorage` du navigateur.
- Aucune commande, réservation ni inscription n'est transmise : le site l'indique à chaque action.
