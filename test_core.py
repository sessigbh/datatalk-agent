import sys
sys.path.append(".")

from backend.app.agent.core import analyze

results = analyze(
    question="Quel est le total des ventes par produit ?",
    file_path="data_samples/ventes.csv"
)

print("=== RÉSULTAT TEXTE ===")
print(results["text"])

print("\n=== TABLEAU ===")
if results["dataframe"] is not None:
    print(results["dataframe"])
else:
    print("Pas de tableau")

print("\n=== GRAPHIQUE ===")
if results["figure"] is not None:
    print("Graphique généré ✅")
else:
    print("Pas de graphique")