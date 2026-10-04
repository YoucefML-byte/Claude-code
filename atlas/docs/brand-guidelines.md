# Atlas Torréfacteurs — Charte de marque v1.0

Atlas est une torréfaction de café de spécialité (marque fictive de démonstration).
Petits lots de 12 kg, torréfiés le mardi, expédiés le mercredi.

## Quick Reference

| Élément | Valeur |
|---------|--------|
| Primary Color | #2340A8 |
| Secondary Color | #6E7A3C |
| Accent Color | #C8861A |
| Police titre | Big Shoulders Stencil |
| Police texte | Instrument Sans |
| Police données | IBM Plex Mono |
| Voix | Précise, chaleureuse, sans jargon inutile |

Le monde visuel vient de l'atelier : les sacs de jute marqués au pochoir,
le café vert avant torréfaction, les fiches de suivi du torréfacteur
(courbe de température, temps de développement, couleur Agtron).

## 1. Couleurs

### Primary Colors
| Nom | Hex | RGB | Usage |
|-----|-----|-----|-------|
| Bleu pochoir | #2340A8 | rgb(35,64,168) | Marque, boutons, liens, marquages |
| Bleu pochoir dark | #182E7E | rgb(24,46,126) | Survol et état actif |
| Bleu pochoir light | #DCE2F6 | rgb(220,226,246) | Fonds de sélection |

### Secondary Colors
| Nom | Hex | RGB | Usage |
|-----|-----|-----|-------|
| Grain vert | #6E7A3C | rgb(110,122,60) | Café vert, début de courbe, états « frais » |
| Grain vert light | #DDE2C4 | rgb(221,226,196) | Étiquettes discrètes |

### Accent Colors
| Nom | Hex | RGB | Usage |
|-----|-----|-----|-------|
| Premier crack | #C8861A | rgb(200,134,26) | Repère du premier crack, rares points d'attention |

### Neutral Palette
| Nom | Hex | RGB | Usage |
|-----|-----|-----|-------|
| Fond café vert | #ECEEE2 | rgb(236,238,226) | Fond de page |
| Surface | #F8F9F2 | rgb(248,249,242) | Cartes, tiroirs |
| Torréfié (texte) | #1F1A14 | rgb(31,26,20) | Texte principal |
| Texte secondaire | #5A5348 | rgb(90,83,72) | Légendes |
| Filet | #C9CCB8 | rgb(201,204,184) | Séparateurs |

Thème sombre : fond #14110D, surface #1E1A15, texte #ECEADF, bleu pochoir éclairci #8FA3F5.

### Accessibilité
- Texte #1F1A14 sur fond #ECEEE2 : 15,1:1 (AAA)
- Bleu pochoir #2340A8 sur fond #ECEEE2 : 7,3:1 (AAA)
- Texte blanc sur bouton #2340A8 : 8,6:1 (AAA)
- Le premier crack #C8861A sert uniquement aux repères graphiques, jamais au texte courant.

## 2. Typographie

```css
--font-display: 'Big Shoulders Stencil', 'Arial Narrow', sans-serif;
--font-body: 'Instrument Sans', 'Helvetica Neue', Arial, sans-serif;
--font-mono: 'IBM Plex Mono', ui-monospace, Menlo, monospace;
```

| Élément | Police | Graisse | Taille (desktop / mobile) | Interligne |
|---------|--------|---------|---------------------------|-----------|
| H1 | Big Shoulders Stencil | 800 | 104px / 56px | 0.92 |
| H2 | Big Shoulders Stencil | 800 | 56px / 38px | 1.0 |
| H3 | Instrument Sans | 600 | 22px / 20px | 1.3 |
| Texte | Instrument Sans | 400 | 17px / 16px | 1.6 |
| Donnée | IBM Plex Mono | 500 | 13px / 13px | 1.4 |
| Étiquette | IBM Plex Mono | 500, majuscules, +0.08em | 12px | 1.4 |

Le pochoir sert aux titres et aux noms d'origine, comme sur un sac. Jamais en texte courant.

## 3. Logo

- **Symbole** : un grain de café dont la fente centrale dessine la ligne de crête de l'Atlas.
- **Principal** : symbole + mot « ATLAS » au pochoir + « TORRÉFACTEURS » en mono.
- **Variantes** : horizontal, symbole seul (favicon), monochrome blanc sur bleu pochoir.
- **Zone de protection** : la hauteur du symbole sur chaque côté.
- **Taille minimale** : 96px de large (horizontal), 24px (symbole seul).
- **À éviter** : déformer, ajouter une ombre, poser sur une photo chargée, changer de couleur hors palette.

Fichiers : `assets/logo/atlas-logo.svg`, `assets/logo/atlas-mark.svg`, `assets/logo/atlas-logo-reverse.svg`.

## 4. Voix

| Trait | Ce que ça veut dire | À faire | À éviter |
|-------|---------------------|---------|----------|
| Précise | On donne les vrais chiffres de l'atelier | « Torréfié mardi, 9 min 40, sortie à 206 °C » | « Une torréfaction parfaite » |
| Chaleureuse | On parle comme au comptoir | « Essayez-le en filtre d'abord » | « Découvrez une expérience unique » |
| Sans jargon inutile | Un terme technique est toujours expliqué | « Lavé : la pulpe est retirée avant séchage » | Empiler les termes sans définition |

### Adaptation du ton
| Contexte | Ton | Exemple |
|----------|-----|---------|
| Site, fiches café | Précis et concret | « Notes : pêche blanche, jasmin, miel. » |
| Réseaux sociaux | Plus direct | « Nouveau lot ce mardi. 140 sachets. » |
| Service client | Calme et utile | « Votre colis part demain matin, voici le suivi. » |

## 5. Messages clés

1. **Fraîcheur** : torréfié le mardi, chez vous en 48 h.
2. **Traçabilité** : chaque sachet porte la ferme, l'altitude, le procédé et la date.
3. **Accompagnement** : chaque café est livré avec sa recette (ratio, mouture, temps).

## 6. Éléments graphiques

- **Courbe de torréfaction** : température du grain dans le temps, avec les repères
  charge, point bas, jaunissement, premier crack et sortie. Elle remplace la photo d'ambiance.
- **Échelle Agtron** : barre de couleur de torréfaction (95 = très clair, 45 = foncé).
- **Tampon** : marquage rectangulaire au pochoir, légèrement incliné, pour les dates de lot.
