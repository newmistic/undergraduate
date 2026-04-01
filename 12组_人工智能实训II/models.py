from layers import *
from torch.autograd import Variable
import numpy
from collections import Counter


class Model(nn.Module):
    def __init__(self, t_dim, l_dim, u_dim, embed_dim, ex, dropout=0.1):
        super(Model, self).__init__()
        emb_t = nn.Embedding(t_dim, embed_dim, padding_idx=0)
        emb_l = nn.Embedding(l_dim, embed_dim, padding_idx=0)
        emb_u = nn.Embedding(u_dim, embed_dim, padding_idx=0)
        emb_su = nn.Embedding(2, embed_dim, padding_idx=0)
        emb_sl = nn.Embedding(2, embed_dim, padding_idx=0)
        emb_tu = nn.Embedding(2, embed_dim, padding_idx=0)
        emb_tl = nn.Embedding(2, embed_dim, padding_idx=0)
        embed_layers = emb_t, emb_l, emb_u, emb_su, emb_sl, emb_tu, emb_tl

        self.MultiEmbed = MultiEmbed(ex, embed_dim, embed_layers)
        self.SelfAttn = SelfAttn(embed_dim, embed_dim)
        self.Embed = Embed(ex, embed_dim, l_dim-1, embed_layers)
        self.Attn = Attn(emb_l, l_dim-1)

    def forward(self, traj, mat1, mat2, vec, traj_len):
        # long(N, M, [u, l, t]), float(N, M, M, 2), float(L, L), float(N, M), long(N)
        joint, delta = self.MultiEmbed(traj, mat1, traj_len)  # (N, M, emb), (N, M, M, emb)
        self_attn = self.SelfAttn(joint, delta, traj_len)  # (N, M, emb)
        self_delta = self.Embed(traj[:, :, 1], mat2, vec, traj_len)  # (N, M, L, emb)
        output = self.Attn(self_attn, self_delta, traj_len)  # (N, L)
        return output


class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(MLP, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(max_len * 3, hidden_dim),  # 输入维度修正为轨迹总特征数
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
    
    def forward(self, x, *args):
        batch_size = x.shape[0]
        x = x.view(batch_size, -1).float()  # 展平为 (N, M*3) 并转 Float
        return self.fc(x)

class LSTM_Model(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(LSTM_Model, self).__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, *args):
        x = x.float()  # 强制转换为 Float 类型
        out, _ = self.lstm(x)  # out: (N, M, hidden_dim)
        traj_len = args[-1] if args else x.size(1)
        out = out[range(len(x)), traj_len-1, :]
        return self.fc(out)

class CNN_Model(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(CNN_Model, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(input_dim, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveMaxPool1d(1))
        self.fc = nn.Linear(64, output_dim)
    def forward(self, x, *args):
        x = x.permute(0, 2, 1).float() 
        features = self.conv(x).squeeze(-1)
        return self.fc(features)

class SimpleAttn(nn.Module):
    def __init__(self, l_dim, embed_dim):
        super(SimpleAttn, self).__init__()
        self.emb_loc = nn.Embedding(l_dim, embed_dim)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads=1)
        self.fc = nn.Linear(embed_dim, l_dim)
    def forward(self, traj, *args):
        traj_loc = traj[:, :, 1]  # 取位置信息
        emb = self.emb_loc(traj_loc).float()
        emb = emb.permute(1, 0, 2)
        attn_out, _ = self.attn(emb, emb, emb)
        attn_out = attn_out.mean(dim=0)
        return self.fc(attn_out)

class RNN_Model(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(RNN_Model, self).__init__()
        self.rnn = nn.RNN(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x, *args):
        x = x.float()  # 确保输入类型为Float
        out, _ = self.rnn(x)  # out: (N, M, hidden_dim)
        traj_len = args[-1] if args else x.size(1)
        last_out = out[range(len(x)), traj_len-1, :]  # 取最后一个有效时间步
        return self.fc(last_out)

class MarkovChain(nn.Module):
    def __init__(self, l_dim):
        super(MarkovChain, self).__init__()
        # 转移矩阵参数化：从位置i到j的概率
        self.trans_matrix = nn.Parameter(torch.randn(l_dim, l_dim))
    
    def forward(self, traj, *args):
        # 输入traj: (N, M, 3)，取最后一个有效位置
        traj_len = args[-1] if args else traj.size(1)
        last_loc = traj[range(len(traj)), traj_len-1, 1].long()  # (N)
        # 获取转移概率 (N, l_dim)
        logits = self.trans_matrix[last_loc]
        return logits