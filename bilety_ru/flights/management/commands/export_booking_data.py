# ------------------------------------------------------------------
# Django integration kit for the recommendation system
# Files included in this single code document (copy each section
# into the corresponding file in your Django `main` app):
# 1) management command: main/management/commands/export_booking_data.py
# 2) recsys helper module: main/recsys/predictor.py
# 3) Django view: main/views_recs.py
# 4) URL snippet: main/urls_recs.py (include in your main/urls.py)
# 5) small training launcher: scripts/train_recsys.py (standalone)
# 6) README section at the end with instructions
# ------------------------------------------------------------------

# -----------------------------
# File: main/management/commands/export_booking_data.py
# -----------------------------
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import csv
from django.utils import timezone
from flights.models import Booking, FlightOffer
from user_management.models import CustomUser as User


class Command(BaseCommand):
    help = 'Export users, items and bookings to CSV for training the recommender'

    def add_arguments(self, parser):
        parser.add_argument('--outdir', type=str, default='recsys_data', help='Output directory')
        parser.add_argument('--limit-users', type=int, default=None, help='Limit number of users to export')

    def handle(self, *args, **options):
        outdir = options['outdir']
        limit_users = options['limit_users']
        os.makedirs(outdir, exist_ok=True)

        self.stdout.write(f'Exporting to {outdir}...')

        # Export users
        users_qs = User.objects.all().order_by('id')
        if limit_users:
            users_qs = users_qs[:limit_users]
        users_file = os.path.join(outdir, 'users.csv')
        with open(users_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # header (extend if you have extra fields)
            writer.writerow(['user_id', 'is_staff', 'date_joined'])
            for u in users_qs:
                writer.writerow([u.id, getattr(u, 'is_staff', False), getattr(u, 'date_joined', '')])
        self.stdout.write(f'Users exported: {users_file}')

        # Export items (flights/offers)
        items_qs = FlightOffer.objects.select_related('flightRequest').all().order_by('id')
        items_file = os.path.join(outdir, 'offers.csv')
        with open(items_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['item_id', 'origin', 'destination', 'departure_date', 'duration', 'currencyCode', 'totalPrice'])
            for it in items_qs:
                writer.writerow([
                    it.id,
                    it.flightRequest.originLocationCode,
                    it.flightRequest.destinationLocationCode,
                    it.dep_duration.date(),  # дата вылета
                    it.duration,
                    it.currencyCode,
                    it.totalPrice
                ])
        self.stdout.write(f'Items exported: {items_file}')

        # Export bookings / interactions
        # Expected Booking fields: id, user (FK), item (FK), event_time (datetime), price_at_event, event_type, purchased
        bookings_qs = Booking.objects.select_related('user', 'offer').order_by('user_id', 'created_at')
        if limit_users:
            bookings_qs = bookings_qs.filter(user__in=users_qs)
        bookings_file = os.path.join(outdir, 'bookings.csv')
        with open(bookings_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow(['event_id', 'user_id', 'offer_id', 'created_at', 'total_price', 'currency_code', 'status'])
            for b in bookings_qs:
                writer.writerow([
                    b.id,
                    b.user.id if b.user else '',
                    b.offer.id,
                    b.created_at,
                    b.total_price,
                    b.currency_code,
                    b.status
                ])

        self.stdout.write(f'Bookings exported: {bookings_file}')
        self.stdout.write(self.style.SUCCESS('Export finished.'))





# -----------------------------
# README / INSTRUCTIONS
# -----------------------------
# 1) Place each "File:" section into the corresponding file path within your Django project.
#    - management command -> main/management/commands/export_booking_data.py
#    - predictor & model_stub -> main/recsys/
#    - views_recs.py and urls_recs.py -> main/
#    - scripts/train_recsys.py -> scripts/ (project root)
#
# 2) Adjust model field names if your models use different attributes. I left comments where
#    you should change attribute names (Item.origin, Booking.event_time, etc.).
#
# 3) Run the export command to produce CSVs:
#       python manage.py export_booking_data --outdir=recsys_data
#
# 4) Train a model locally using the training script:
#       python scripts/train_recsys.py --bookings=recsys_data/bookings.csv --items=recsys_data/items.csv --out=recsys_model.pth
#
# 5) Configure settings.py with absolute paths (optional):
#    RECSYS_MODEL_PATH = BASE_DIR / 'recsys_model.pth'
#    RECSYS_DATA_DIR = BASE_DIR / 'recsys_data'
#
# 6) Wire the URLs: include main/urls_recs.py in your project's url config or main/urls.py.
#
# 7) Test the endpoint (JSON):
#    GET /main/recommendations/123/  -> returns {"user_id":123, "recommendations": [item_ids...]}
#
# 8) For production inference, consider:
#    - exporting the model to TorchScript or ONNX
#    - running inference in a separate FastAPI service
#    - caching top-K per user and refreshing periodically
#
# Dependencies (pip):
#   pandas, numpy, torch, tqdm
#
# That's it — adapt the model architecture, negative sampling and metrics later when you
# have real logs. Good luck!