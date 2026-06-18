"""Services métier (logique transactionnelle partagée entre blueprints).

Cf. 09-BACKEND-FLASK.md : la couche `services` encapsule les règles de
gestion (RG-XX) et orchestre les écritures sur plusieurs modèles dans une
même transaction, en s'appuyant sur les couches `routes` (HTTP) et
`models` (persistance) sans logique métier.
"""
