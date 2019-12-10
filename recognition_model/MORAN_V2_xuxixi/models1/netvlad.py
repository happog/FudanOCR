import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy

class NetVLAD(nn.Module):
    """NetVLAD layer implementation"""

    def __init__(self, G,num_clusters=64, dim=128, alpha=100.0,
                 normalize_input=True):
        """
        Args:
            num_clusters : int
                The number of clusters
            dim : int
                Dimension of descriptors
            alpha : float
                Parameter of initialization. Larger value is harder assignment.
            normalize_input : bool
                If true, descriptor-wise L2 normalization is applied to input.
        """
        super(NetVLAD, self).__init__()
        self.G = G
        self.num_clusters = num_clusters
        self.dim = dim
        self.alpha = alpha
        self.normalize_input = normalize_input
        self.conv = nn.Conv2d(dim, num_clusters, kernel_size=(1, 1), bias=True)
        #self.centroids = nn.Parameter(torch.rand(num_clusters, dim))
        self.centroids = nn.Parameter(torch.rand(num_clusters, dim), requires_grad=True)
        self._init_params()
    def _init_params(self):
        self.conv.weight.data = nn.Parameter(2.0 * self.alpha * self.centroids.data).unsqueeze(-1).unsqueeze(-1).data
        #print(self.conv.weight.data.size()) #torch.Size([72, 512, 1, 1])
        #print(type(self.conv.weight.data)) #<class 'torch.Tensor'>
        
        self.conv.bias.data = nn.Parameter(
            - self.alpha * self.centroids.norm(dim=1).data
        ).data     
        #print(self.conv.bias.data.size())#torch.Size([72])
        #print(type(self.conv.bias.data)) #<class 'torch.Tensor'>

    def forward(self, x):
        #N, C = x.shape[:2]
        N, C = x.size()[:2]
        
        if self.normalize_input:
            x = F.normalize(x, p=2, dim=1)  # across descriptor dim
        # soft-assignment
        soft_assign = self.conv(x).view(N, self.num_clusters, -1)
        soft_assign = F.softmax(soft_assign, dim=1)
        soft_assign =soft_assign[:,0:(self.num_clusters-self.G),:]

        x_flatten = x.view(N, C, -1)

        centroids = self.centroids[0:(self.num_clusters-self.G),:]
        # calculate residuals to each clusters
        residual = x_flatten.expand(self.num_clusters-self.G, -1, -1, -1).permute(1, 0, 2, 3) - centroids.expand(x_flatten.size(-1), -1, -1).permute(1, 2, 0).unsqueeze(0)

        residual *= soft_assign.unsqueeze(2)
        vlad = residual.sum(dim=-1)
        #vlad = vlad.sum(dim=0)
        vlad = F.normalize(vlad, p=2, dim=1)  # intra-normalization
        vlad = vlad.view(x.size(0), -1)  # flatten
        #vlad = vlad.view(1, -1)
        vlad = F.normalize(vlad, p=2, dim=1)  # L2 normalize
        
        return vlad

class EmbedNet(nn.Module):
    def __init__(self, base_model, net_vlad):
        super(EmbedNet, self).__init__()
        self.base_model = base_model
        self.net_vlad = net_vlad

    def forward(self, input):
        x = self.base_model(input.cuda())
        embedded_x = self.net_vlad(x)
        return embedded_x

class TripletNet(nn.Module):
    def __init__(self, embed_net):
        super(TripletNet, self).__init__()
        self.embed_net = embed_net

    def forward(self, a, p, n):
        embedded_a = self.embed_net(a)
        embedded_p = self.embed_net(p)
        embedded_n = self.embed_net(n)
        return embedded_a, embedded_p, embedded_n

    def feature_extract(self, x):
        return self.embed_net(x)