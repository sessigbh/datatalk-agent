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
    elif file_path.endswith(".xlsx"):
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
1. Importer tous les modules nécessaires en début de code (ex: import re, import json...)
2. Calculer la réponse à la question
3. Stocker le résultat textuel dans une variable `result_text` (string, sans backslash dans les f-strings)
4. Si pertinent, créer un graphique plotly et le stocker dans `result_fig` (sinon `result_fig = None`)
5. Si pertinent, stocker un tableau résultat dans `result_df` (DataFrame pandas, sinon `result_df = None`)
6. Ne jamais utiliser de caractères spéciaux (accents, €, ', ") dans les noms de colonnes créées ou les clés de dictionnaire. Utiliser des noms simples comme 'chiffre_affaires', 'total', 'moyenne'.
7. Toujours convertir result_text en string avec str() avant de l'assigner.
8. Pour les graphiques, créer UN SEUL graphique simple (pas de subplots multiples). Préférer plotly.express à plotly.graph_objects.

Retourne UNIQUEMENT le code Python, sans explication, sans balises markdown.
"""
    return prompt


def call_claude(prompt: str) -> str:
    """Envoie le prompt à Claude et retourne le code Python généré."""
    
    message = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    code = message.content[0].text.strip() 
    # .content contains the request's answer,
    # [0] to select the first element, and we know we only expect one,
    # .text to select the answer, knowing we only expect a text

    return code
    

def call_claude_with_retry(prompt: str, df: pd.DataFrame, max_retries: int = 3) -> dict:
    """Appelle Claude, exécute le code, et réessaie si erreur — jusqu'à max_retries fois."""
    
    code = call_claude(prompt)
    last_error = None
    
    for attempt in range(max_retries):
        try:
            # Valider la syntaxe d'abord
            import ast
            ast.parse(code)
            
            # Exécuter le code
            result = execute_code(code, df)
            return result
            
        except Exception as e:
            last_error = str(e)
            print(f"=== TENTATIVE {attempt + 1} ÉCHOUÉE ===")
            print(f"Erreur : {last_error}")
            print(f"Code fautif :\n{code}")
            
            if attempt < max_retries - 1:
                # Demander à Claude de corriger
                correction_prompt = f"""Le code Python suivant a produit une erreur.

Code :
{code}

Erreur : {last_error}

Corrige ce code. Respecte les mêmes règles :
- Utilise le DataFrame pandas appelé `df`
- Stocke le résultat dans result_text (str), result_fig, result_df
- N'utilise pas de caractères spéciaux dans les noms de colonnes
- Importe tous les modules nécessaires
- Retourne UNIQUEMENT le code Python corrigé, sans markdown.
"""
                code = call_claude(correction_prompt)
    
    # Toutes les tentatives ont échoué
    raise ValueError(f"Impossible de générer un code valide après {max_retries} tentatives. Dernière erreur : {last_error}")


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
    
    results = call_claude_with_retry(prompt, df)
    
    return results