"""Blueprint de tableaux de bord et indicateurs agrégés (RF-23 à RF-25).

En V1, ce blueprint expose un résumé synthétique pour le tableau de bord
React (cf. wireframes 30-WIREFRAMES-UI.md). Les analyses avancées (ML,
anomalies, prévisions) sont prévues dans une itération ultérieure
(cf. 20-MACHINE-LEARNING.md).
"""
from flask import Blueprint

reports_bp = Blueprint("reports", __name__)

from app.blueprints.reports import routes  # noqa: E402,F401
