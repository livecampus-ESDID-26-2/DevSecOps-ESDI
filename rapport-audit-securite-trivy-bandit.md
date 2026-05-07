# Rapport d’analyse de sécurité – Audit des conteneurs et du code source

## Contexte

Dans le cadre de l’audit de sécurité de l’infrastructure et des applications, plusieurs analyses automatisées ont été réalisées à l’aide des outils Bandit et Trivy.

L’objectif de ces analyses est d’identifier :

- les vulnérabilités connues présentes dans les images Docker utilisées,
- les failles potentielles dans le code source Python,
- ainsi que les composants nécessitant une mise à jour ou une correction de sécurité.

---

# 1. Analyse statique du code source – Bandit

## Résultat global

L’analyse du code source Python a été effectuée avec l’outil Bandit.

### Résumé des résultats

- Nombre total de lignes analysées : **245**
- Vulnérabilités détectées : **0**
- Problèmes de sécurité critiques : **0**
- Problèmes de sécurité élevés : **0**
- Problèmes de sécurité moyens : **0**
- Problèmes de sécurité faibles : **0**

### Conclusion

Aucune vulnérabilité n’a été identifiée dans le code source analysé.

Le code respecte les bonnes pratiques de sécurité attendues pour :

- la gestion des entrées,
- l’exécution de commandes,
- l’utilisation des bibliothèques Python,
- ainsi que la manipulation des données sensibles.

Cette analyse indique un niveau de sécurité satisfaisant sur la partie applicative actuellement auditée.

---

# 2. Analyse des images Docker – Trivy

## Résumé global des vulnérabilités

L’analyse des images conteneurisées a été réalisée avec Trivy.

### Nombre total de vulnérabilités détectées

| Sévérité | Nombre |
| -------- | -----: |
| Critique |     96 |
| Élevée   |   1387 |
| Moyenne  |   3539 |
| Faible   |      0 |

Le volume important de vulnérabilités est principalement lié à certaines images applicatives contenant de nombreuses dépendances système et bibliothèques embarquées.

---

# 3. Analyse par composant

## Images les plus exposées

| Image Docker                       | Critiques | Élevées | Moyennes |
| ---------------------------------- | --------: | ------: | -------: |
| `wordpress:6.5-php8.2-apache`      |        71 |    1257 |     3198 |
| `grafana/grafana:11.2.0`           |         8 |      52 |      150 |
| `prom/prometheus:v2.54.1`          |         8 |      30 |       63 |
| `gcr.io/cadvisor/cadvisor:v0.49.1` |         6 |      27 |       64 |

### Observations

#### WordPress

L’image WordPress représente la principale surface d’exposition de l’infrastructure.  
Elle concentre à elle seule la majorité des vulnérabilités détectées.

Cela s’explique notamment par :

- le nombre important de dépendances PHP et système,
- la taille de l’image,
- ainsi que l’utilisation de versions comportant des composants obsolètes.

#### Grafana

Plusieurs vulnérabilités critiques affectent Grafana, notamment :

- des risques d’injection de commande,
- des problèmes de fuite d’informations,
- des vulnérabilités liées aux bibliothèques Go embarquées.

#### Prometheus / cAdvisor / Node Exporter

Les outils de monitoring présentent également des vulnérabilités critiques liées :

- à Docker/Moby,
- aux bibliothèques cryptographiques Go,
- ainsi qu’à certaines implémentations TLS et gRPC.

---

# 4. Vulnérabilités critiques identifiées

Les principales vulnérabilités critiques détectées concernent :

| CVE              | Description                          |
| ---------------- | ------------------------------------ |
| `CVE-2024-9264`  | Injection de commande dans Grafana   |
| `CVE-2024-41110` | Bypass d’autorisation Docker / Moby  |
| `CVE-2024-45337` | Contournement d’authentification SSH |
| `CVE-2025-68121` | Validation TLS incorrecte            |
| `CVE-2026-33186` | Bypass d’autorisation gRPC           |

Ces vulnérabilités peuvent potentiellement permettre :

- une exécution de code arbitraire,
- des contournements de sécurité,
- des accès non autorisés,
- ou des interceptions de communications sécurisées.

---

# 5. Évaluation du risque

## Niveau de risque global : ÉLEVÉ

Malgré l’absence de vulnérabilités dans le code source applicatif, plusieurs images Docker utilisées en production présentent un nombre important de vulnérabilités critiques et élevées.

Les risques principaux concernent :

- l’exposition des services web,
- les composants de supervision,
- les bibliothèques réseau et cryptographiques,
- ainsi que les dépendances système obsolètes.

---

# 6. Recommandations

## Actions prioritaires

### 1. Mettre à jour les images Docker

Mettre à jour l’ensemble des images vers les versions les plus récentes disposant des correctifs de sécurité.

Priorité :

1. WordPress
2. Grafana
3. Prometheus
4. cAdvisor

---

### 2. Réduire la surface d’attaque

- Utiliser des images minimalistes (Alpine, Distroless)
- Supprimer les dépendances inutiles
- Désactiver les plugins et modules non utilisés

---

### 3. Mettre en place un scan automatique CI/CD

Intégrer :

- Trivy,
- Bandit,
- et éventuellement Grype ou Snyk

dans la pipeline CI/CD afin de détecter automatiquement les nouvelles vulnérabilités avant déploiement.

---

### 4. Renforcer le monitoring sécurité

Mettre en place :

- des alertes CVE,
- une surveillance des versions déployées,
- ainsi qu’une politique régulière de patch management.

---

# Conclusion

L’analyse du code source ne révèle aucune faille de sécurité directe, ce qui indique un bon niveau de qualité sur la partie développement.

En revanche, l’analyse des conteneurs met en évidence un nombre important de vulnérabilités au sein des dépendances et images Docker utilisées, principalement sur WordPress et certains outils de monitoring.

Une campagne de mise à jour et de durcissement des images est fortement recommandée afin de réduire la surface d’exposition et limiter les risques de compromission de l’infrastructure.
