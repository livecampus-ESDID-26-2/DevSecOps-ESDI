# DevSecOps-ESDI - DevSecOps - ESDI

**École :** LiveCampus - ESDID-26.2  
**Étudiant :** [Antoine MASIA](https://github.com/MasiaAntoine) - Full-Stack Developer  
**Intervenant :** [PercevalFox](https://github.com/PercevalFox) - DevSecOps Engineer

---

## 📝 [Fiche de Révision](docs/fiche-revision.md)

**Pour comprendre rapidement tous les concepts du projet :**

- 🏗️ Architecture conteneurisée multi-services (WordPress + monitoring)
- 🎨 Stack d'observabilité Prometheus + Grafana (provisioning par fichiers)
- 🔧 Pipeline CI/CD GitHub Actions multi-jobs (deploy + scan + rapport)
- 🔐 Sécurité applicative : scan d'images Trivy + analyse statique Bandit
- 🚀 Quality Gate et remontée centralisée des alertes via GitHub Security (SARIF)

👉 **[Voir la fiche de révision complète](docs/fiche-revision.md)**

---

<div align="center">

<table>
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/MasiaAntoine">
        <img src="https://avatars.githubusercontent.com/u/115811899?s=400&u=73abcb21760b5f0cdf2f1588452ba7e527305cb6&v=4" alt="Antoine MASIA" width="100">
      </a>
      <br/>
      <strong>Antoine MASIA</strong>
      <br/>
      <em>Étudiant</em>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/PercevalFox">
        <img src="https://avatars.githubusercontent.com/u/103103954?v=4" alt="PercevalFox" width="100">
      </a>
      <br/>
      <strong>PercevalFox</strong>
      <br/>
      <em>Intervenant</em>
    </td>
  </tr>
</table>

<br>

<em>Projet réalisé dans le cadre du module "DevSecOps - ESDI"</em>

</div>

---

## Description du Projet

Projet pédagogique illustrant un **pipeline DevSecOps complet** autour d'un WordPress conteneurisé : déploiement reproductible, observabilité, scan automatisé des vulnérabilités d'images Docker et analyse statique du code Python.

**Fonctionnalités principales :**

- 🐳 **Stack conteneurisée** WordPress + MariaDB démarrable en une commande
- 📊 **Observabilité** intégrée avec Prometheus, Grafana, node-exporter et cAdvisor
- 🔍 **Scan de vulnérabilités** automatisé sur 6 images Docker via Trivy
- 🐍 **Analyse statique** du code Python avec Bandit
- 🛡️ **Remontée centralisée** des alertes dans GitHub Security (SARIF)
- 📑 **Rapports HTML/Markdown** générés par un script Python custom
- 🚦 **Quality Gate** configurable (`--fail-on CRITICAL`) pour bloquer la CI
- 📄 **Rapport d'audit** type livrable client (`rapport-audit-securite-trivy-bandit.md`)

## Sommaire

- [Description du Projet](#description-du-projet)
- [Captures d'écran](#captures-décran)
- [Architecture du Projet](#architecture-du-projet)
  - [Architecture en couches DevSecOps](#architecture-en-couches-devsecops)
  - [Architecture conteneurisée (Docker Compose)](#architecture-conteneurisée-docker-compose)
  - [Flux CI/CD](#flux-cicd)
  - [Pattern Pipeline as Code](#pattern-pipeline-as-code)
  - [Pattern Quality Gate](#pattern-quality-gate)
  - [Pattern Defense in Depth](#pattern-defense-in-depth)
- [Fonctionnalités](#fonctionnalités)
  - [Stack applicative](#stack-applicative)
  - [Stack monitoring](#stack-monitoring)
  - [Pipeline CI/CD](#pipeline-cicd)
  - [Rapports de vulnérabilités](#rapports-de-vulnérabilités)
  - [Rapport d'audit (livrable client)](#rapport-daudit-livrable-client)
- [Installation et Utilisation](#installation-et-utilisation)
  - [Prérequis](#prérequis)
  - [Configuration](#configuration)
  - [Démarrage](#démarrage)
  - [Réinitialisation de la stack](#réinitialisation-de-la-stack)
  - [Régénérer les rapports en local](#régénérer-les-rapports-en-local)
- [Technologies Utilisées](#technologies-utilisées)
- [Sécurité](#sécurité)
- [Configuration](#configuration-1)
- [Projet Pédagogique](#projet-pédagogique)

## Captures d'écran

### Dashboard Grafana

![Dashboard Grafana](/docs/screenshots/grafana-overview.png)

_Dashboard "DevSecOps - Overview" provisionné automatiquement, affichant la consommation CPU/RAM hôte et par conteneur grâce à node-exporter et cAdvisor._

### Step Summary GitHub Actions

![Résumé pipeline](/docs/screenshots/github-actions-summary.png)

_Page d'un run GitHub Actions avec le tableau récapitulatif des CVE par image (Trivy) et le résumé Bandit injectés dans `$GITHUB_STEP_SUMMARY`._

### Onglet GitHub Security

![Onglet Security](/docs/screenshots/github-security-tab.png)

_Alertes consolidées dans `Security › Code scanning` : une catégorie par image (`trivy-wordpress`, `trivy-grafana`, …) plus une catégorie `bandit` pour le code Python._

### Rapport HTML Trivy

![Rapport HTML](/docs/screenshots/trivy-html-report.png)

_Rapport HTML autoporteur produit par `scripts/trivy_report.py` : cartes colorées par sévérité et tableau complet des CVE par image._

---

## Architecture du Projet

### Architecture en couches DevSecOps

Le projet est structuré en **trois couches indépendantes** qui collaborent : la stack applicative, la stack d'observabilité et le pipeline CI/CD.

**Principe clé** : _Shift Left Security_ — la sécurité est intégrée au plus tôt dans le cycle de vie (à chaque push, sur chaque image, sur chaque ligne de code).

```
┌──────────────────────── Stack applicative ────────────────────────┐
│                                                                   │
│   wordpress (Apache + PHP 8.2)  ──►  db (MariaDB 10.11)           │
│        :8080                                                      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─────────────────────── Stack monitoring ──────────────────────────┐
│                                                                   │
│   node-exporter ─┐                                                │
│   cadvisor ──────┼──►  prometheus :9090  ──►  grafana :3000       │
│                  │                                                │
└───────────────────────────────────────────────────────────────────┘

┌──────────────────────── Pipeline CI/CD ───────────────────────────┐
│                                                                   │
│   deploy-stack ──► trivy-scan (matrix images) ──► trivy-report    │
│                              │                          │         │
│                              ▼                          ▼         │
│                      GitHub Security              Artefact HTML   │
│                                                                   │
│   bandit (code Python) ──► GitHub Security + step summary         │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Architecture conteneurisée (Docker Compose)

Tous les composants tournent dans des conteneurs Docker isolés, orchestrés par Docker Compose. Le projet est versionné en mode _Infrastructure as Code_ : la stack entière se reconstruit depuis le dépôt Git.

```
.
├── .github/workflows/devsecops.yml   # Pipeline GitHub Actions
├── docker/
│   ├── docker-compose.yml            # Stack WP + monitoring
│   ├── .env.example                  # Variables d'environnement
│   ├── prometheus/prometheus.yml     # Scrape config
│   └── grafana/
│       ├── provisioning/             # Datasource + provider dashboards
│       └── dashboards/overview.json  # Dashboard CPU/RAM
├── scripts/
│   ├── trivy_report.py               # Agrégation rapports Trivy (MD + HTML)
│   └── requirements.txt              # Bandit pour la CI
├── reports/                          # Sortie des rapports (gitignoré, .gitkeep seul)
├── rapport-audit-securite-trivy-bandit.md  # Exemple de livrable client
├── .gitignore
├── .trivyignore                      # CVE volontairement ignorées
└── README.md
```

### Flux CI/CD

Le pipeline est défini dans [`.github/workflows/devsecops.yml`](.github/workflows/devsecops.yml). Il est déclenché sur `push` / `pull_request` sur `main`, manuellement (`workflow_dispatch`) et tous les lundis à 6h UTC (re-scan régulier même sans changement de code).

```
        Push / PR / cron / dispatch
                  │
                  ▼
         ┌──────────────────┐
         │   deploy-stack   │   docker compose up + smoke test
         └────────┬─────────┘
                  │
       ┌──────────┴──────────┐
       ▼                     ▼
┌──────────────┐       ┌──────────────┐
│  trivy-scan  │       │    bandit    │   matrix 6 images   |   scan code Python
│ (matrix x 6) │       │              │
└──────┬───────┘       └──────┬───────┘
       │                      │
       ▼                      ▼
┌──────────────┐        GitHub Security
│ trivy-report │       (Code scanning)
│  (MD + HTML) │
└──────┬───────┘
       │
       ▼
 Artefact HTML
 + Step Summary
```

**Caractéristiques :**

- ✅ Pipeline 100 % déclaratif (YAML versionné)
- ✅ Scan parallélisé via matrix (6 images en simultané)
- ✅ Remontée multi-format (JSON brut, SARIF GitHub, HTML autoporteur, Markdown)
- ✅ _Quality Gate_ configurable (`--fail-on CRITICAL`)

### Pattern Pipeline as Code

L'ensemble du pipeline (build, test, scan, rapport) est décrit dans un fichier YAML versionné, sans aucune configuration manuelle dans l'UI GitHub.

**Composants impliqués :**

- `.github/workflows/devsecops.yml` : définition complète des jobs et de leur orchestration
- `scripts/trivy_report.py` : logique custom de reporting (versionnée avec le code)
- `.trivyignore` : exceptions documentées et tracées en Git

**Avantages :**

- ✅ Toute modification de pipeline passe par une PR (revue de code)
- ✅ Reproductibilité totale : ré-exécution déterministe d'un run passé
- ✅ Historique Git complet de l'évolution de la sécurité

### Pattern Quality Gate

Le pipeline peut être configuré pour **échouer** automatiquement si une CVE dépasse un seuil de sévérité, transformant la pipeline en garde-fou de sécurité.

**Mécanisme :**

- `trivy_report.py --fail-on CRITICAL` → exit code 1 si CVE critique détectée
- L'échec du job bloque la merge si la branche est protégée
- Les exceptions documentées vont dans `.trivyignore` (avec commentaire justificatif)

**Avantages :**

- ✅ Aucune CVE critique ne peut être mergée sans validation explicite
- ✅ Politique de sécurité versionnée (visible dans le repo)
- ✅ Pas de drift : le seuil est appliqué à chaque commit

### Pattern Defense in Depth

La sécurité est appliquée à plusieurs niveaux indépendants : si l'un échoue, les autres restent actifs.

**Couches :**

- **Code Python** : analyse statique via Bandit (failles potentielles dans le code)
- **Images Docker** : scan Trivy (CVE des paquets système et bibliothèques)
- **Dépendances** : versions pinnées dans `docker-compose.yml`
- **Secrets** : `.env` gitignoré, exemple via `.env.example`
- **Visibilité** : remontée SARIF dans GitHub Security pour triage centralisé

**Avantages :**

- ✅ Pas de point unique de défaillance dans la chaîne sécurité
- ✅ Couverture du _code applicatif_ + _infrastructure conteneurisée_
- ✅ Triage et suivi facilités via une UI unique (GitHub Security)

---

## Fonctionnalités

### Stack applicative

- **Description** : WordPress conteneurisé, prêt à être déployé en local en une commande.
- **Détails** :
  - WordPress 6.5 (image officielle PHP 8.2 + Apache) exposé sur `:8080`
  - MariaDB 10.11 comme base de données, isolée en réseau Docker
  - Variables d'environnement via `.env` (gitignoré)
  - Volumes Docker persistants pour la BDD et les fichiers WordPress

### Stack monitoring

- **Description** : observabilité complète provisionnée automatiquement (zéro clic dans l'UI).
- **Détails** :
  - **Prometheus** scrape `node-exporter` (métriques système) et `cadvisor` (métriques par conteneur) toutes les 15 s
  - **Grafana** pré-configuré : datasource Prometheus + dashboard _DevSecOps - Overview_
  - Dashboards **provisionnés via fichiers** : tout est versionné, rien n'est cliqué dans l'UI
  - Accès Grafana sur `:3000` (`admin` / `admin`)

### Pipeline CI/CD

- **Description** : pipeline GitHub Actions multi-jobs combinant déploiement, scan d'images et analyse statique.
- **Détails** :

| Job            | Rôle                                                                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `deploy-stack` | `docker compose up`, attend WordPress/Prometheus/Grafana, puis stoppe la stack. Sert de smoke test.                                      |
| `trivy-scan`   | Matrix sur les 6 images de la stack. Génère **JSON** + **SARIF** par image.                                                              |
| `trivy-report` | Télécharge tous les JSON, lance `trivy_report.py`, publie un **résumé Markdown** dans la page du run et un **rapport HTML** en artefact. |
| `bandit`       | Analyse statique du code Python (`scripts/`). JSON + texte + SARIF.                                                                      |

### Rapports de vulnérabilités

- **Description** : production multi-format des résultats de sécurité.
- **Détails** :
  - **Onglet _Actions_** : _Step Summary_ avec tableau des CVE par image et résumé Bandit
  - **Onglet _Security › Code scanning_** : alertes consolidées par catégorie (`trivy-wordpress`, `trivy-mariadb`, …, `bandit`), avec triage et suivi dans le temps
  - **Artefacts** :
    - `trivy-json-<image>` : JSON brut Trivy de chaque image
    - `trivy-report-html` : rapport HTML autoporteur + Markdown
    - `bandit-reports` : `bandit-report.json|txt|sarif`

### Rapport d'audit (livrable client)

- **Description** : exemple de restitution synthétique destinée à un client, produite à partir des scans réels Bandit + Trivy.
- **Détails** :
  - Fichier : [`rapport-audit-securite-trivy-bandit.md`](./rapport-audit-securite-trivy-bandit.md)
  - **Contexte** de l'audit et portée des analyses
  - **Synthèse Bandit** : analyse statique du code Python
  - **Synthèse Trivy** : volume de CVE par sévérité et top des images les plus exposées (WordPress, Grafana, Prometheus, cAdvisor)
  - **CVE critiques** identifiées avec leur description (`CVE-2024-9264`, `CVE-2024-41110`, …)
  - **Évaluation du risque global** et **recommandations priorisées** (mise à jour des images, réduction de la surface d'attaque, intégration des scans en CI/CD, monitoring sécurité)
  - Format volontairement court et non technique côté lecture, présentable en revue de sécurité sans expertise DevSecOps

---

## Installation et Utilisation

### Prérequis

- **Docker Desktop** (ou Docker Engine + Compose v2)
- **Git** (pour cloner le projet)
- **Python 3.12+** (uniquement si on relance `trivy_report.py` hors Docker — optionnel)

### Configuration

1. **Cloner le projet** :

```bash
git clone https://github.com/livecampus-ESDID-26-2/DevSecOps-ESDI.git

cd DevSecOps-ESDI
```

2. **Configurer les variables d'environnement** :

```bash
cd docker
cp .env.example .env
nano .env          # adapter les mots de passe au besoin
```

```env
# docker/.env (exemple)
WORDPRESS_DB_NAME=wordpress
WORDPRESS_DB_USER=wp_user
WORDPRESS_DB_PASSWORD=change_me
MARIADB_ROOT_PASSWORD=change_me_root
MARIADB_DATABASE=wordpress
MARIADB_USER=wp_user
MARIADB_PASSWORD=change_me
```

### Démarrage

3. **Lancer la stack complète** :

```bash
docker compose up -d
```

4. **Attendre l'initialisation** :  
   Docker récupère les images, démarre MariaDB puis WordPress, puis Prometheus/Grafana avec leur provisioning. Le premier démarrage prend ~30 s.

5. **Accéder aux services** :

| Service    | URL                   | Identifiants par défaut |
| ---------- | --------------------- | ----------------------- |
| WordPress  | http://localhost:8080 | assistant d'install     |
| Prometheus | http://localhost:9090 | —                       |
| Grafana    | http://localhost:3000 | `admin` / `admin`       |

6. **Arrêter le serveur** :

```bash
docker compose down                  # arrêt simple, données conservées
```

### Réinitialisation de la stack

#### Méthode 1 : recréer les conteneurs (données conservées)

```bash
docker compose down
docker compose up -d --force-recreate
```

#### Méthode 2 : reset complet (suppression des volumes)

⚠️ **Supprime toute la base WordPress et les données Grafana**.

```bash
docker compose down -v
docker compose up -d
```

### Régénérer les rapports en local

Le dossier `reports/` est versionné (vide via `.gitkeep`) mais **son contenu ne l'est pas**. Pré-requis : Docker (pas besoin d'installer Trivy ni Bandit système).

#### Fichiers produits

| Fichier                          | Source                    | Contenu                                            |
| -------------------------------- | ------------------------- | -------------------------------------------------- |
| `reports/raw/trivy-<image>.json` | Trivy                     | JSON brut par image (entrée du script Python)      |
| `reports/trivy-report.md`        | `scripts/trivy_report.py` | Résumé Markdown des CVE par image                  |
| `reports/trivy-report.html`      | `scripts/trivy_report.py` | Page HTML autoporteuse (cartes colorées + tableau) |
| `reports/bandit-report.txt`      | Bandit                    | Analyse statique du code Python (`scripts/`)       |
| `reports/bandit-report.json`     | Bandit                    | Même rapport, version machine-readable             |
| `reports/bandit-report.sarif`    | Bandit                    | Format SARIF (uploadé vers GitHub Security en CI)  |

#### Étape 1 — Scanner les images de la stack avec Trivy

```bash
mkdir -p reports/raw
for img in \
    wordpress:6.5-php8.2-apache \
    mariadb:10.11 \
    grafana/grafana:11.2.0 \
    prom/prometheus:v2.54.1 \
    prom/node-exporter:v1.8.2 \
    gcr.io/cadvisor/cadvisor:v0.49.1
do
  slug=$(echo "$img" | tr '/:.' '___')
  docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(pwd)/reports/raw:/out" \
    -v trivy-cache:/root/.cache/ \
    aquasec/trivy:latest image \
      --severity CRITICAL,HIGH,MEDIUM --format json \
      --output "/out/trivy-${slug}.json" "$img"
done
```

#### Étape 2 — Agréger en Markdown + HTML

```bash
python3 scripts/trivy_report.py \
  --input reports/raw \
  --out-md reports/trivy-report.md \
  --out-html reports/trivy-report.html \
  --top 20
```

> Ajoute `--fail-on CRITICAL` pour que le script sorte en code 1 si une CVE critique est trouvée (utile pour faire planter la CI).

#### Étape 3 — Scan Bandit du code Python

```bash
docker run --rm -v "$(pwd):/src" -w /src python:3.12-slim sh -c '
  pip install -q bandit bandit-sarif-formatter && \
  bandit -r scripts -f txt   -o reports/bandit-report.txt && \
  bandit -r scripts -f json  -o reports/bandit-report.json && \
  bandit -r scripts -f sarif -o reports/bandit-report.sarif'
```

#### Étape 4 — Ouvrir le rapport HTML

```bash
open reports/trivy-report.html        # macOS
xdg-open reports/trivy-report.html    # Linux
```

---

## Technologies Utilisées

### Backend (stack applicative)

- **WordPress 6.5 (PHP 8.2 + Apache)** : CMS conteneurisé exposé sur `:8080`
- **MariaDB 10.11** : base de données relationnelle, isolée en réseau Docker

### Monitoring & Observabilité

- **Prometheus v2.54.1** : collecte des métriques (scrape toutes les 15 s)
- **Grafana 11.2.0** : dashboards provisionnés par fichiers (`overview.json`)
- **node-exporter v1.8.2** : exporteur des métriques système de l'hôte
- **cAdvisor v0.49.1** : exporteur des métriques par conteneur

### Sécurité (DevSecOps)

- **Trivy** : scan de vulnérabilités CVE sur les images Docker (JSON + SARIF)
- **Bandit** : analyse statique de sécurité du code Python (TXT + JSON + SARIF)
- **bandit-sarif-formatter** : converter SARIF pour l'upload GitHub
- **SARIF** : format standard de remontée des alertes vers GitHub Security

### Infrastructure

- **Docker** : conteneurisation de l'ensemble des services
- **Docker Compose v2** : orchestration locale multi-services

### CI/CD

- **GitHub Actions** : pipeline déclenchée sur `push` / `pull_request` / `cron` / `workflow_dispatch`
- **github/codeql-action/upload-sarif** : ingestion des SARIF dans GitHub Security
- **actions/upload-artifact** & **actions/download-artifact** : transfert des rapports entre jobs

### Script Python (`trivy_report.py`)

- **Python 3.12 (stdlib uniquement)** : aucune dépendance pip requise
- **JSON / HTML / Markdown** : multi-format de sortie
- **Quality Gate** : option `--fail-on CRITICAL|HIGH|MEDIUM` pour bloquer la CI

---

## Sécurité

### Sécurité des conteneurs

✅ **Scan Trivy automatisé** : 6 images scannées à chaque push/PR + tous les lundis (cron)  
✅ **Sévérités filtrées** : seuls `CRITICAL`, `HIGH` et `MEDIUM` sont remontés  
✅ **Quality Gate** : `--fail-on CRITICAL` permet de bloquer la merge sur CVE critique  
✅ **Exceptions tracées** : `.trivyignore` documente chaque CVE volontairement ignorée  
✅ **Versions pinnées** : toutes les images de `docker-compose.yml` sont fixées sur un tag précis (pas de `:latest`)  
✅ **Remontée SARIF** : alertes ingérées dans `Security › Code scanning` par catégorie (`trivy-wordpress`, …)

### Sécurité du code applicatif

✅ **Analyse statique Bandit** : exécutée sur tout le dossier `scripts/` à chaque run  
✅ **Triple format de sortie** : TXT (lisible), JSON (machine), SARIF (GitHub)  
✅ **Catégorie dédiée** : alertes Bandit isolées dans GitHub Security (catégorie `bandit`)  
✅ **Boucle fermée** : le script `trivy_report.py` est lui-même la cible du scan Bandit (_on scanne le scanneur_)

### Sécurité de la base de données

✅ **Mots de passe via `.env`** : aucun secret en dur dans le code  
✅ **`.env` gitignoré** : seul `.env.example` est versionné  
✅ **Réseau Docker isolé** : MariaDB n'est **pas** exposée en `localhost` (uniquement accessible depuis WordPress)  
✅ **Volume persistant chiffrable** : la BDD vit sur un volume Docker nommé (montable sur disque chiffré)

### Sécurité de la pipeline CI/CD

✅ **Permissions GitHub Actions explicites** : `permissions: security-events: write` (principe du moindre privilège)  
✅ **Secrets non loggés** : aucun mot de passe injecté en clair dans les logs  
✅ **Pipeline as Code** : toute modification du workflow passe par une PR (revue de code obligatoire si la branche est protégée)  
✅ **Re-scan régulier** : cron hebdomadaire pour détecter les CVE publiées **après** le merge

---

## Configuration

### Activer la remontée GitHub Security

1. _Settings › Code security and analysis_ du dépôt
2. Activer **Code scanning** (le workflow inclut déjà `permissions: security-events: write` et appelle `github/codeql-action/upload-sarif`)
3. Après le premier run, les alertes apparaissent dans _Security › Code scanning_. Chaque catégorie (`trivy-wordpress`, `bandit`, …) garde sa propre liste, ce qui évite de mélanger les sources.

> **Note** : sur un repo _privé_ sans plan GitHub Advanced Security, l'upload SARIF échoue silencieusement. Les rapports JSON / HTML restent disponibles en artefacts.

### Ignorer une CVE (`.trivyignore`)

Pour exclure volontairement une vulnérabilité (faux positif, non-exploitable dans le contexte, etc.), ajouter son identifiant dans `.trivyignore` avec un commentaire justifiant la décision.

```text
# Exemple — .trivyignore
# Faux positif : la fonctionnalité n'est pas exposée publiquement
CVE-2024-XXXXX
```

Et passer l'option `trivyignores: .trivyignore` à l'action Trivy dans le workflow.

### Bloquer la CI sur une sévérité

Pour transformer la pipeline en _Quality Gate_ strict, ajouter `--fail-on HIGH` (ou `CRITICAL`) à `trivy_report.py` dans le job `trivy-report` :

```bash
python scripts/trivy_report.py \
    --input ./trivy-raw \
    --out-md trivy-report.md \
    --out-html trivy-report.html \
    --fail-on CRITICAL
```

### Ajouter une image au scan

Compléter la matrice `trivy-scan` dans `.github/workflows/devsecops.yml` :

```yaml
strategy:
  matrix:
    image:
      - wordpress:6.5-php8.2-apache
      - mariadb:10.11
      - grafana/grafana:11.2.0
      - prom/prometheus:v2.54.1
      - prom/node-exporter:v1.8.2
      - gcr.io/cadvisor/cadvisor:v0.49.1
      - mon-image:tag # ← nouvelle image
```

### Ajouter un dashboard Grafana

Déposer un nouveau JSON dans `docker/grafana/dashboards/`, il sera détecté automatiquement par le provisioner au prochain `docker compose up`.

### Script `trivy_report.py`

Petit utilitaire (stdlib uniquement) qui :

1. Charge tous les JSON Trivy d'un dossier
2. Compte les vulnérabilités par sévérité (global et par image)
3. Produit :
   - un **Markdown** prêt à coller dans `$GITHUB_STEP_SUMMARY`
   - un **HTML** standalone (cartes colorées + tableau visuel)
4. Sort en code `1` si une CVE dépasse le seuil `--fail-on`

| Option       | Rôle                                                       |
| ------------ | ---------------------------------------------------------- |
| `--input`    | Dossier contenant les JSON Trivy                           |
| `--out-md`   | Chemin du rapport Markdown généré                          |
| `--out-html` | Chemin du rapport HTML autoporteur                         |
| `--top`      | Nombre max de CVE listées dans le tableau (défaut : 20)    |
| `--fail-on`  | Seuil de sévérité bloquante (`CRITICAL`, `HIGH`, `MEDIUM`) |

---

## Projet Pédagogique

Ce projet fait partie du module "**DevSecOps - ESDI**" à **LiveCampus - ESDID-26.2** et démontre :

### Compétences techniques

#### Conteneurisation & Infrastructure as Code

- ✅ **Docker Compose multi-services** : orchestration d'une stack complète (app + monitoring) en un seul fichier déclaratif
- ✅ **Versions pinnées** : reproductibilité des environnements (pas de `:latest`)
- ✅ **Provisioning par fichiers** : datasource et dashboards Grafana 100 % versionnés (zéro clic UI)
- ✅ **Gestion des secrets** : `.env` gitignoré + `.env.example` documenté

#### Observabilité & Monitoring

- ✅ **Prometheus + exporters** : collecte de métriques système (node-exporter) et conteneurs (cAdvisor)
- ✅ **Grafana provisionné** : dashboard _DevSecOps - Overview_ prêt à l'emploi
- ✅ **Scrape config déclarative** : intervalle 15 s, cibles définies dans `prometheus.yml`

#### Sécurité (DevSecOps)

- ✅ **Scan d'images Trivy** : détection des CVE sur 6 images en parallèle (matrix)
- ✅ **Analyse statique Bandit** : recherche de patterns à risque dans le code Python
- ✅ **Format SARIF** : standardisation des alertes pour ingestion centralisée
- ✅ **Quality Gate** : option `--fail-on` pour bloquer la CI en cas de CVE critique
- ✅ **Defense in Depth** : code + images + secrets + visibilité = couches indépendantes

#### CI/CD avec GitHub Actions

- ✅ **Pipeline multi-jobs** : `deploy-stack` → `trivy-scan` (matrix) → `trivy-report` + `bandit`
- ✅ **Triggers multiples** : `push`, `pull_request`, `cron` hebdomadaire, `workflow_dispatch`
- ✅ **Artefacts inter-jobs** : `actions/upload-artifact` + `actions/download-artifact`
- ✅ **Step Summary** : injection de Markdown dans `$GITHUB_STEP_SUMMARY` pour visualisation directe
- ✅ **Permissions explicites** : principe du moindre privilège (`security-events: write`)

### Fonctionnalités avancées

- 🔐 Quality Gate configurable bloquant la CI sur seuil de CVE
- 🐳 Stack 100 % conteneurisée démarrable en une commande
- 📊 Dashboards Grafana provisionnés automatiquement (aucun clic UI requis)
- 🔍 Scan de 6 images Docker en parallèle via une matrix GitHub Actions
- 📑 Script Python custom de reporting (Markdown + HTML autoporteur, stdlib only)
- 📄 Rapport d'audit type livrable client à partir de scans réels
- 🛡️ Remontée SARIF centralisée dans GitHub Security (multi-catégories)

### Bonnes pratiques

- **Pipeline as Code** : tout est versionné en YAML, rien n'est cliqué dans l'UI
- **Shift Left Security** : sécurité intégrée à chaque commit, pas en fin de cycle
- **Documentation as Code** : README, fiche de révision et rapport d'audit dans le repo
- **Reproductibilité** : versions pinnées partout (images Docker, actions GitHub)
- **Exceptions tracées** : `.trivyignore` avec commentaires justifiant chaque exclusion
- **Re-scan régulier** : cron hebdomadaire pour détecter les CVE publiées après le merge
- **Boucle fermée** : le script `trivy_report.py` est lui-même la cible du scan Bandit
