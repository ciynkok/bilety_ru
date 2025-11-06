import torch
import torch.nn as nn

class RecModelForInference(nn.Module):
    def __init__(self, num_items, emb_dim=128, max_len=30, n_heads=4, n_layers=2):
        super().__init__()
        self.num_items = num_items
        self.max_len = max_len
        PAD_IDX = num_items
        self.item_emb = nn.Embedding(num_items+1, emb_dim, padding_idx=PAD_IDX)
        self.pos_emb = nn.Embedding(max_len, emb_dim)
        encoder_layer = nn.TransformerEncoderLayer(d_model=emb_dim, nhead=n_heads, dim_feedforward=emb_dim*4)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.output = nn.Linear(emb_dim, num_items)

    def forward(self, src):
        # src: [B, max_len]
        B = src.size(0)
        positions = torch.arange(0, self.max_len, device=src.device).unsqueeze(0).repeat(B,1)
        x = self.item_emb(src) + self.pos_emb(positions)
        x = x.permute(1,0,2)
        out = self.transformer(x, src_key_padding_mask=(src==self.num_items))
        out = out.permute(1,0,2)
        last_idxs = (src != self.num_items).sum(dim=1) - 1
        last_repr = out[torch.arange(B), last_idxs]
        logits = self.output(last_repr)
        return logits
    