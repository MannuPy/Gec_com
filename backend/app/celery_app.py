"""
Integration Celery (cf. 21-PIPELINE-ETL.md, 20-MACHINE-LEARNING.md section 20.7).

Sur PythonAnywhere (sans worker Celery/Redis), toutes les taches sont executees
de maniere synchrone via `.run()`. Le stub ci-dessous garantit que l'import de
ce module ne fait jamais planter l'application si celery n'est pas installe.
"""
from __future__ import annotations

try:
    from celery import Celery
    from celery.schedules import crontab
    HAS_CELERY = True
except ImportError:
    HAS_CELERY = False

    class _FakeTask:
        """Stub d'une tache Celery pour execution synchrone sans broker."""
        def __init__(self, fn):
            self._fn = fn
            self.__name__ = getattr(fn, "__name__", "task")
            self.__module__ = getattr(fn, "__module__", "")

        def run(self, *args, **kwargs):
            return self._fn(*args, **kwargs)

        def delay(self, *args, **kwargs):
            raise RuntimeError(
                "Celery non disponible (PythonAnywhere). "
                "Utilisez ?async=false ou flask ml-train-all."
            )

        def __call__(self, *args, **kwargs):
            return self._fn(*args, **kwargs)

    class Celery:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            self.conf = self
        def task(self, *args, name=None, **kwargs):
            def decorator(fn):
                return _FakeTask(fn)
            if args and callable(args[0]):
                return _FakeTask(args[0])
            return decorator
        def update(self, **kwargs): pass

    def crontab(*args, **kwargs): pass  # type: ignore[misc]


celery_app = Celery("gescom_bf")


def init_celery(app) -> object:
    """Configure Celery si disponible, no-op sinon (PythonAnywhere)."""
    if not HAS_CELERY:
        app.logger.warning(
            "Celery non installe — taches ML executees de maniere synchrone."
        )
        return celery_app

    from celery.schedules import crontab as _crontab  # type: ignore[import]

    celery_app.conf.update(
        broker_connection_retry_on_startup=True,
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        timezone="UTC",
        enable_utc=True,
        task_default_queue="ml",
        beat_schedule={
            "etl-extract-and-clean-daily": {
                "task": "app.tasks.etl_tasks.etl_extract_and_clean",
                "schedule": _crontab(hour=2, minute=0),
            },
            "etl-validate-daily": {
                "task": "app.tasks.etl_tasks.etl_validate",
                "schedule": _crontab(hour=2, minute=10),
            },
            "etl-build-features-daily": {
                "task": "app.tasks.etl_tasks.etl_build_features",
                "schedule": _crontab(hour=2, minute=20),
            },
            "train-demand-forecast-weekly": {
                "task": "app.tasks.ml_tasks.train_demand_forecast_task",
                "schedule": _crontab(day_of_week="monday", hour=2, minute=0),
            },
            "train-credit-scoring-nightly": {
                "task": "app.tasks.ml_tasks.train_credit_scoring_task",
                "schedule": _crontab(hour=2, minute=30),
            },
            "detect-anomalies-hourly": {
                "task": "app.tasks.ml_tasks.detect_anomalies_task",
                "schedule": _crontab(minute=0),
            },
            "compute-abc-xyz-weekly": {
                "task": "app.tasks.ml_tasks.compute_abc_xyz_task",
                "schedule": _crontab(day_of_week="monday", hour=3, minute=0),
            },
            "compute-rfm-segments-monthly": {
                "task": "app.tasks.ml_tasks.compute_rfm_segments_task",
                "schedule": _crontab(day_of_month=1, hour=4, minute=0),
            },
        },
    )

    class ContextTask(celery_app.Task):
        """Execute chaque tache dans le contexte applicatif Flask."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app
