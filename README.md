# DataTalk

**Interrogez vos données en langage naturel — sans écrire une seule ligne de code.**

DataTalk est un agent IA qui permet à n'importe quel utilisateur, qu'il soit analyste, manager ou chargé de mission, de poser des questions sur ses données CSV ou SQL en français ou en anglais et d'obtenir des réponses claires : texte explicatif, tableaux récapitulatifs et graphiques interactifs.

---

## Fonctionnalités

- **Langage naturel** — posez vos questions comme vous le feriez à un collègue : *"Quel est le chiffre d'affaires moyen par région ?"*
- **Sources de données flexibles** — importez un fichier CSV ou connectez-vous à une base SQL (SQLite, PostgreSQL, MySQL)
- **Réponses multi-formats** — texte structuré, tableaux filtrables et graphiques générés automatiquement (barres, courbes, camemberts)
- **Agent conversationnel** — posez des questions de suivi, affinez votre analyse, l'agent conserve le contexte de la session
- **Aucune compétence technique requise** — interface Streamlit simple et intuitive
- **Déploiement conteneurisé** — stack Docker prête à l'emploi pour une mise en production rapide

---

## Stack technique

| Couche | Technologie |
|---|---|
| Interface utilisateur | [Streamlit](https://streamlit.io) |
| API backend | [FastAPI](https://fastapi.tiangolo.com) |
| Agent IA | [Claude API](https://www.anthropic.com) (Anthropic) |
| Traitement des données | pandas, SQLAlchemy |
| Visualisation | Plotly |
| Conteneurisation | Docker, Docker Compose |
| Langage | Python 3.11+ |

---

## Architecture

```
datatalk-agent/
├── backend/
│   ├── main.py               # Point d'entrée FastAPI
│   └── app/
│       ├── api/routes.py     # Endpoints REST
│       └── agent/core.py     # Logique de l'agent (Claude)
├── frontend/
│   └── app.py                # Interface Streamlit
├── tests/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Installation

### Prérequis

- Python 3.11+
- Docker & Docker Compose (optionnel, recommandé)
- Une clé API Anthropic — obtenez-en une sur [console.anthropic.com](https://console.anthropic.com)

### 1. Cloner le dépôt

```bash
git clone https://github.com/sessigbh/datatalk-agent.git
cd datatalk-agent
```

### 2. Configurer les variables d'environnement

```bash
cp .env.example .env
```

Editez `.env` et renseignez votre clé API :

```env
ANTHROPIC_API_KEY=sk-ant-...
```

### 3a. Lancement avec Docker (recommandé)

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Interface Streamlit | http://localhost:8501 |
| API FastAPI | http://localhost:8000 |
| Documentation API | http://localhost:8000/docs |

### 3b. Lancement sans Docker

```bash
# Installer les dépendances
pip install -r requirements.txt

# Démarrer le backend
uvicorn backend.main:app --reload --port 8000

# Dans un autre terminal, démarrer le frontend
streamlit run frontend/app.py
```

---

## Exemple d'utilisation

**1. Importez votre fichier CSV** via le panneau latéral de l'interface.

**2. Posez une question en langage naturel :**

> *"Montre-moi les 5 produits qui ont généré le plus de revenus le mois dernier."*

**3. DataTalk vous répond :**

- Un résumé textuel de l'analyse
- Un tableau avec les 5 produits et leurs revenus respectifs
- Un graphique en barres interactif

**4. Continuez la conversation :**

> *"Et si on exclut la catégorie 'Promotions' ?"*

L'agent affine l'analyse sans que vous n'ayez à tout re-saisir.

---

## Variables d'environnement

| Variable | Description | Obligatoire |
|---|---|---|
| `ANTHROPIC_API_KEY` | Clé API Anthropic pour accéder à Claude | Oui |
| `CLAUDE_MODEL` | Modèle Claude à utiliser (défaut : `claude-sonnet-4-20250514`) | Non |
| `DATABASE_URL` | URL de connexion SQL (ex: `postgresql://user:pass@host/db`) | Non |
| `MAX_ROWS_PREVIEW` | Nombre maximum de lignes envoyées à l'agent (défaut : `500`) | Non |

---

## Contribuer

Les contributions sont les bienvenues. Merci d'ouvrir une issue avant de soumettre une pull request.

---

## Licence

Distribué sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.