import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn

class Recommender:
    def __init__(self, model_cls, model_state_path, data_dir='recsys_data', device=None, max_len=30):
        self.data_dir = data_dir
        self.device = device or (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))
        self.max_len = max_len

        # load item mapping
        items_path = os.path.join(data_dir, 'offers.csv')
        if not os.path.exists(items_path):
            raise FileNotFoundError('items.csv not found in data_dir')
        items_df = pd.read_csv(items_path)
        self.item_ids = items_df['item_id'].astype(int).tolist()
        # mapping item_id -> index (0..N-1)
        self.item2idx = {iid: i for i, iid in enumerate(self.item_ids)}
        self.idx2item = {i: iid for iid, i in self.item2idx.items()}
        self.num_items = len(self.item2idx)

        # instantiate model and load weights
        self.model = model_cls(num_items=self.num_items, max_len=self.max_len)
        self.model.load_state_dict(torch.load(model_state_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

        # pre-load bookings to build user sequences quickly
        bookings_path = os.path.join(data_dir, 'bookings.csv')
        if os.path.exists(bookings_path):
            self.bookings = pd.read_csv(bookings_path)
        else:
            self.bookings = pd.DataFrame(columns=['user_id','offer_id','created_at'])

    def _build_user_seq(self, user_id):
        # returns list of item indices sorted by time
        df = self.bookings[self.bookings['user_id'] == int(user_id)].sort_values('created_at')
        seq = [self.item2idx[i] for i in df['offer_id'].astype(int).tolist() if int(i) in self.item2idx]
        return seq

    def recommend_for_user(self, user_id, top_k=10):
        seq = self._build_user_seq(user_id)
        # prepare input (pad left with PAD index = num_items)
        PAD_IDX = self.num_items
        if len(seq) > self.max_len:
            seq = seq[-self.max_len:]
        pad = [PAD_IDX] * (self.max_len - len(seq))
        src = torch.LongTensor([pad + seq]).to(self.device)
        with torch.no_grad():
            logits = self.model(src)  # shape [1, num_items]
            scores = logits.squeeze(0).cpu().numpy()
            top_idx = np.argsort(-scores)[:top_k]
            top_item_ids = [self.idx2item[i] for i in top_idx]
        return top_item_ids