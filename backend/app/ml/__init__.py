"""
Modules d'entraînement et d'inférence des modèles de Machine Learning
(cf. 20-MACHINE-LEARNING.md).

Chaque sous-module expose au minimum :
- `train(...)` : entraîne le(s) modèle(s), enregistre une entrée
  `MLModel` (registre/traçabilité, RNF-17/RG-40) et produit des
  `Prediction` associées ;
- `latest_predictions(...)` : relit les dernières prédictions enregistrées
  (utilisé par le blueprint `analytics`).

Toutes les dépendances lourdes (xgboost, prophet, mlflow) sont importées de
manière défensive : si elles sont indisponibles, un algorithme de repli
(scikit-learn / règles pandas) est utilisé et consigné dans
`ml_models.algorithm` afin de rester tracable (cf. 21-PIPELINE-ETL.md).
"""
