import os
import pandas as pd
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")


def load_dataframe(file_path: str) -> pd.DataFrame:
    """Charge un fichier CSV ou Excel en DataFrame pandas."""
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Format non supporté : {file_path}")
    

def build_prompt(question: str, df: pd.DataFrame) -> str:
    """Construit le prompt envoyé à Claude avec la question et un aperçu des données."""
    
    apercu = df.head(5).to_string()
    colonnes = df.dtypes.to_string()
    nb_lignes = len(df)

    prompt = f"""Tu es un assistant data analyst. Tu aides des utilisateurs non-techniques à analyser leurs données.

L'utilisateur a chargé un fichier avec {nb_lignes} lignes.

Voici les colonnes et leurs types :
{colonnes}

Voici un aperçu des 5 premières lignes :
{apercu}

Question de l'utilisateur : {question}

Génère du code Python qui répond à cette question en utilisant un DataFrame pandas appelé `df`.
Le code doit :
1. Calculer la réponse à la question
2. Stocker le résultat textuel dans une variable `result_text` (string)
3. Si pertinent, créer un graphique plotly et le stocker dans `result_fig` (sinon `result_fig = None`)
4. Si pertinent, stocker un tableau résultat dans `result_df` (DataFrame pandas, sinon `result_df = None`)

Retourne UNIQUEMENT le code Python, sans explication, sans balises markdown.
"""
    return prompt


def call_claude(prompt: str) -> str:
    """Envoie le prompt à Claude et retourne le code Python généré."""
    
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    code = message.content[0].text.strip() 
    # .content contien les retours de notre requête,
    # [0] pour le premier élément, sachant qu'on attend une réponse unique,
    # .text pour récupérer notre réponse dont on sait que c'est du texte
    return code


def execute_code(code: str, df: pd.DataFrame) -> dict:
    """Exécute le code généré par Claude et retourne les résultats."""
    
    # Nettoyage des balises markdown si Claude en a ajouté
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()
    
    # Environnement d'exécution : on donne accès à df et aux librairies
    local_vars = {
        "df": df,
        "pd": pd,
    }
    
    # Exécution du code
    exec(code, {}, local_vars) # source, global variables, local variables. Ici aucune var globale utilisée afin de ne pas faire de modif irréversible. On les passe plutôt en var locale
    
    
    # Récupération des résultats
    return {
        "text": local_vars.get("result_text", "Analyse terminée."),
        "figure": local_vars.get("result_fig", None),
        "dataframe": local_vars.get("result_df", None),
    }



def analyze(question: str, file_path: str) -> dict:
    """Fonction principale : reçoit une question et un fichier, retourne une analyse complète."""
    
    # Étape 1 : charger les données
    df = load_dataframe(file_path)
    
    # Étape 2 : construire le prompt
    prompt = build_prompt(question, df)
    
    # Étape 3 : appeler Claude
    code = call_claude(prompt)
    
    # Étape 4 : exécuter le code et retourner les résultats
    results = execute_code(code, df)
    
    return results