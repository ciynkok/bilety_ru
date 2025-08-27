from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .models import FlightRequest
import datetime
from .scheduler_jobs import delete_req


# def start_scheduler():
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(), "default")
#
#     scheduler.add_job(
#         delete_req,  # Указываем глобальную функцию
#         'interval',
#         minutes=5,
#         id="delete_req",
#     )
#     scheduler.start()


class DeleteReq:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_jobstore(DjangoJobStore(), "default")

    def start_scheduler(self):
        self.scheduler.add_job(
            delete_req,
            'interval',
            minutes=2,
            id="my_job",
            replace_existing=True,
        )
        self.scheduler.start()
