# Fiche de révision — DevSecOps ESDI

Synthèse **technique** pour réviser le projet sans relire tout le README. Idée générale : une appli dans des conteneurs, du monitoring qui tourne à côté, et une CI qui vérifie que ça monte **et** qu’il n’y a pas trop de soucis sécu.

---

## 1. Stack conteneurisée (Docker Compose)

- **Pourquoi Docker** : même environnement partout (ta machine, la CI). Pas de « ça marchait chez moi ».
- **`docker/docker-compose.yml`** : décrit les **services** (images, ports, volumes, réseaux). C’est une forme d’**Infrastructure as Code**.
- **Applicatif** : **WordPress** (PHP / Apache, port **8080** côté hôte) + **MariaDB** pour la base. Le WordPress dépend du `db` sain (`healthcheck`).
- **Isolation** : réseaux `frontend` / `backend` pour séparer ce qui doit être exposé du reste.

À retenir en oral : *« La stack est reproductible : un `docker compose up` à partir du dépôt ».*

---

## 2. Observabilité (Prometheus + Grafana)

- **Prometheus** : collecte des **métriques** (séries temporelles) en scrapant des endpoints HTTP configurés dans `prometheus/prometheus.yml`.
- **node-exporter** : métriques de la **machine** (CPU, mémoire, etc.).
- **cAdvisor** : métriques des **conteneurs** (per container).
- **Grafana** (port **3000**) : tableaux de bord. Les datasources et le dashboard sont **provisionnés par fichiers** (`grafana/provisioning/`, `grafana/dashboards/`) → pas besoin de cliquer dans l’UI pour recréer la config : tout est **versionné**.

À retenir : *« Observabilité = métriques + dashboards ; provisioning = Git comme source de vérité ».*

---

## 3. Pipeline CI/CD (GitHub Actions)

Fichier : **`.github/workflows/devsecops.yml`**.

**Déclencheurs** : push / PR sur `main`, lancement manuel, **cron** (re-scan régulier : les vulnérabilités des images évoluent même si ton code non).

**Enchaînement logique** :

| Job | Rôle court |
|-----|----------------|
| `deploy-stack` | Monte la stack, **smoke tests** (`curl` WordPress `:8080`, readiness Prometheus / Grafana), puis teardown. |
| `trivy-scan` | **Matrice** : une exécution par **image** (6 images upstream). Produits JSON + **SARIF**, upload SARIF vers GitHub. |
| `trivy-report` | Dépend du scan : télécharge les JSON, **`scripts/trivy_report.py`** → MD + HTML, résumé dans `$GITHUB_STEP_SUMMARY`. |
| `bandit` | Analyse **statique** du dossier `scripts/` (Python), SARIF + résumé dans le run. |

**Permissions utiles à connaître** : `security-events: write` pour **Code scanning** (upload SARIF).

À retenir : *« Pipeline as Code = le YAML est dans Git, chaque changement peut être revu comme du code ».*

---

## 4. Sécurité dans la chaîne

- **Trivy** : scan des **images** (CVE OS + libs). Sévérités typiques CRITICAL → LOW selon les étapes.
- **Bandit** : **SAST** sur Python (mauvaises pratiques, risques comme des appels `eval`, etc.).
- **SARIF** : format standard pour remonter les findings dans **GitHub › Security › Code scanning** avec une **`category`** par image (`trivy-wordpress`, …) et `bandit`.
- **Quality Gate** : dans le script rapport Trivy, `--fail-on CRITICAL` (ou `NONE` en CI actuelle selon ligne de commande) permet de **faire échouer** la pipeline si seuil dépassé — utile pour bloquer une fusion sur `main`.
- **`.trivyignore`** : exceptions **explicitées et versionnées** (mieux que ignorer sans trace).

À retenir : *« Shift left : sécurité dès la CI, pas seulement en prod ».*

---

## 5. Fichiers utiles à citer

- Stack : `docker/docker-compose.yml`, `docker/.env.example`
- Monitoring : `docker/prometheus/prometheus.yml`, `docker/grafana/provisioning/`
- CI : `.github/workflows/devsecops.yml`
- Rapports : `scripts/trivy_report.py`, sorts dans `reports/` (souvent gitignoré sauf `.gitkeep`)