from django.apps import AppConfig


class FlightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'flights'

    # def ready(self):
    #     # if not os.environ.get('RUN_MAIN'):
    #     #     return
    #     from . import tasks
    #     tasks.DeleteReq().start_scheduler()
