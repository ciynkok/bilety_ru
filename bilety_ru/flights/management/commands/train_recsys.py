from django.core.management.base import BaseCommand
from django.conf import settings
import os
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
import numpy as np
from tqdm import tqdm

# Импорт модели из проекта
from flights.recsys.model_stub import RecModelForInference


class Command(BaseCommand):
    help = "Обучает рекомендательную модель на основе экспортированных CSV-файлов (bookings.csv и items.csv)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--bookings",
            type=str,
            default=os.path.join(settings.BASE_DIR, "recsys_data", "bookings.csv"),
            help="Путь к bookings.csv",
        )
        parser.add_argument(
            "--items",
            type=str,
            default=os.path.join(settings.BASE_DIR, "recsys_data", "offers.csv"),
            help="Путь к offers.csv",
        )
        parser.add_argument(
            "--out",
            type=str,
            default=os.path.join(settings.BASE_DIR, "recsys_model.pth"),
            help="Путь для сохранения обученной модели",
        )
        parser.add_argument("--epochs", type=int, default=3, help="Количество эпох обучения")
        parser.add_argument("--batch-size", type=int, default=256, help="Размер батча")
        parser.add_argument("--max-len", type=int, default=30, help="Максимальная длина последовательности")

    def handle(self, *args, **options):
        
        class BookingsSeqDataset(Dataset):
            def __init__(self, bookings_csv, items_csv, max_len=30):
                bk = pd.read_csv(bookings_csv)
                items = pd.read_csv(items_csv)

                self.item_ids = items['item_id'].astype(int).tolist()
                self.item2idx = {iid: i for i, iid in enumerate(self.item_ids)}
                self.num_items = len(self.item2idx)
                self.PAD_IDX = self.num_items
                self.max_len = max_len

                self.user_seqs = []
                for uid, g in bk.sort_values('created_at').groupby('user_id'):
                    seq = [self.item2idx[i] for i in g['offer_id'].astype(int).tolist() if int(i) in self.item2idx]
                    if len(seq) < 2:
                        continue
                    self.user_seqs.append(seq)

            def __len__(self):
                return len(self.user_seqs)

            def __getitem__(self, idx):
                seq = self.user_seqs[idx]
                cut = np.random.randint(1, len(seq))
                src = seq[:cut]
                tgt = seq[cut]
                if len(src) > self.max_len:
                    src = src[-self.max_len:]
                pad = [self.PAD_IDX] * (self.max_len - len(src))
                src_padded = pad + src
                return torch.LongTensor(src_padded), torch.LongTensor([tgt])
            
            
        bookings_path = options["bookings"]
        items_path = options["items"]
        out_path = options["out"]
        epochs = options["epochs"]
        batch_size = options["batch_size"]
        max_len = options["max_len"]
        #print(items_path)

        if not os.path.exists(bookings_path) or not os.path.exists(items_path):
            self.stderr.write("❌ Не найдены CSV-файлы. Сначала выполните export_booking_data.")
            return

        self.stdout.write(f"📊 Загружаем данные из:\n  {bookings_path}\n  {items_path}")

        ds = BookingsSeqDataset(bookings_path, items_path, max_len=max_len)
        loader = DataLoader(ds, batch_size=batch_size, shuffle=True)

        model = RecModelForInference(num_items=ds.num_items, max_len=max_len)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)

        opt = torch.optim.Adam(model.parameters(), lr=1e-3)
        crit = nn.CrossEntropyLoss()

        for epoch in range(1, epochs + 1):
            model.train()
            pbar = tqdm(loader, desc=f"Эпоха {epoch}")
            total_loss = 0.0
            for src, tgt in pbar:
                src = src.to(device)
                tgt = tgt.squeeze(1).to(device)
                logits = model(src)
                loss = crit(logits, tgt)
                opt.zero_grad()
                loss.backward()
                opt.step()
                total_loss += loss.item()
                pbar.set_postfix(loss=total_loss / len(loader))

            self.stdout.write(f"Эпоха {epoch} завершена, средний loss = {total_loss/len(loader):.4f}")

        torch.save(model.state_dict(), out_path)
        self.stdout.write(self.style.SUCCESS(f"💾 Модель сохранена в {out_path}"))