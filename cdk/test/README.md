# AdoptAI API Tests

Suite de tests complète pour valider l'API AdoptAI déployée et son handler Lambda.

## Structure

```
test/
├── python/                      # Tests unitaires Python
│   ├── conftest.py             # Fixtures pytest (mocks S3)
│   ├── test_endpoints.py       # Tests des endpoints
│   ├── test_filters.py         # Tests des filtres
│   ├── test_helpers.py         # Tests des fonctions utilitaires
│   └── test_error_handling.py  # Tests de gestion d'erreurs
├── api.integration.test.ts     # Tests en production (API déployée)
└── README.md                    # Cette documentation
```

## Prérequis

### TypeScript (Vitest)
```bash
cd cdk
yarn install
```

### Python (pytest avec uv)
```bash
cd cdk

# Créer l'environnement virtuel
uv venv

# Installer les dépendances
uv pip install -r requirements-dev.txt
```

## Exécution des tests

### Tests unitaires

```bash
cd cdk
yarn test
```

**Ce qui est testé** :
- ✅ Tests Lambda Python (pytest) - 70 tests
  - Endpoints et structure des réponses
  - Logique de filtrage (date, stage, time, search, now)
  - Fonctions utilitaires (parse_time, datetime)
  - Gestion d'erreurs et caching

**Total** : 70 tests unitaires

### Tests en production

```bash
cd cdk
yarn test:prod
```

**Ce qui est testé** :
- ✅ Appels HTTP réels à https://adoptai.codecrafter.fr/
- ✅ Tous les endpoints (/, /llms.txt, /robots.txt, /health, /sessions, /speakers, 404)
- ✅ Paramètres de filtrage (date, stage, time, search, now)
- ✅ Validation structure des réponses
- ✅ Headers CORS et Content-Type UTF-8
- ✅ Encodage des caractères spéciaux (•)

**Total** : 20 tests d'intégration

### Rapport de couverture HTML (optionnel)

```bash
cd cdk
yarn test:html
```

Génère un rapport HTML de couverture pour le code Python.
**Ouvrir** : `cdk/lib/lambda/htmlcov/index.html`

## Description des tests

### Tests unitaires Python (70 tests)

#### test_endpoints.py (~10 tests)
- GET / et /llms.txt retournent la documentation
- GET /robots.txt retourne robots.txt
- GET /health retourne status healthy
- GET /sessions retourne toutes les sessions
- GET /speakers retourne tous les speakers
- 404 pour chemins inconnus
- OPTIONS retourne headers CORS
- Les champs internes (_start_dt, _end_dt) ne sont pas exposés

#### test_filters.py (~35 tests)
- Filtrage par date (2025-11-25, 2025-11-26)
- Filtrage par stage (case-insensitive)
- Filtrage par time (morning/afternoon)
- Recherche par texte (titre, speaker, company)
- Filtres combinés
- Paramètre `now` (sessions en cours et à venir dans 30 min)
- Recherche speakers

#### test_helpers.py (~27 tests)
- parse_time: conversion heure → minutes (9:00 AM → 540)
- parse_session_datetime: parsing date + heure → datetime Paris
- get_paris_now: retourne datetime timezone Paris
- filter_sessions_by_now: détection sessions en cours/à venir
- Edge cases: midnight, noon, sessions sans end time

#### test_error_handling.py (~13 tests)
- Erreurs S3 (ClientError, JSON invalide)
- Fallback llms.txt quand fichier absent
- Caching des données (sessions, speakers, llms.txt)
- Sessions/speakers avec champs manquants
- Query strings malformées

### Tests d'intégration API (20 tests)

#### GET / et /llms.txt (~2 tests)
- Documentation retournée avec UTF-8 correct
- Caractères spéciaux (•) affichés correctement

#### GET /sessions (~13 tests)
- Toutes les sessions (243)
- Filtrage date, stage, time, search
- Paramètre now (sessions en cours/à venir)
- Filtres combinés
- Validation structure JSON
- Résultats vides

#### GET /speakers (~2 tests)
- Tous les speakers (499)
- Recherche speakers

#### Autres endpoints (~3 tests)
- /robots.txt, /health, 404
- Headers CORS (OPTIONS)

## Statistiques

- **Total tests** : 90 tests
  - 70 tests unitaires (Python Lambda)
  - 20 tests d'intégration (API production)
- **Couverture** : Tous les endpoints et cas d'usage documentés dans llms.txt

## Commandes rapides

```bash
# Tests unitaires (Python Lambda)
yarn test

# Tests API en production
yarn test:prod

# Rapport de couverture HTML
yarn test:html
```

## CI/CD

Pour intégrer dans un pipeline CI/CD :

```yaml
# .github/workflows/test.yml
- name: Install dependencies
  run: |
    cd cdk
    yarn install
    uv venv
    uv pip install -r requirements-dev.txt

- name: Run unit tests
  run: |
    cd cdk
    yarn test

- name: Run production tests
  run: |
    cd cdk
    yarn test:prod
```
