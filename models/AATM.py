import torch
import torch.nn as nn
from torch.nn import functional as F
from models.SRAG import SRAG
from models.TRAG import TRAG

def weights_init_kaiming(m):
    classname = m.__class__.__name__
    if classname.find('Linear') != -1:
        nn.init.kaiming_normal_(m.weight, a=0, mode='fan_out')
        nn.init.constant_(m.bias, 0.0)
    elif classname.find('Conv') != -1:
        nn.init.kaiming_normal_(m.weight, a=0, mode='fan_in')
        if m.bias is not None:
            nn.init.constant_(m.bias, 0.0)
    elif classname.find('BatchNorm') != -1:
        if m.affine:
            nn.init.constant_(m.weight, 1.0)
            nn.init.constant_(m.bias, 0.0)

class AATM(nn.Module):

    def __init__(self, inplanes, mid_planes, spatial_method,
                 is_mutual_channel_attention, is_mutual_spatial_attention,
                 is_appearance_channel_attention, is_appearance_spatial_attention,
                 fix, num, **kwargs):

        super(AATM, self).__init__()

        self.spatial_method = spatial_method
        self.sigmoid = nn.Sigmoid()
        self.avg = nn.AdaptiveAvgPool2d((1, 1))
        self.relu = nn.ReLU(inplace=True)
        self.num = num

        self.Embeding = nn.Sequential(
            nn.Conv2d(in_channels=inplanes, out_channels=mid_planes,
                      kernel_size=1, stride=1, padding=0, bias=False),
            nn.BatchNorm2d(mid_planes),
            self.relu,
            nn.Conv2d(in_channels=mid_planes, out_channels=128,
                      kernel_size=1, stride=1, padding=0, bias=False),
            nn.BatchNorm2d(128),
            self.relu
        )
        self.Embeding.apply(weights_init_kaiming)

        if self.num != '0':
            self.TRAG = TRAG(inplanes=inplanes, is_mutual_channel_attention=is_mutual_channel_attention,
                            is_mutual_spatial_attention = is_mutual_spatial_attention, num=num, fix=fix)

            self.conv_block = nn.Sequential(
                nn.Conv2d(in_channels=inplanes, out_channels=mid_planes, kernel_size=1, bias=False),
                nn.BatchNorm2d(mid_planes),
                self.relu,
                nn.Conv2d(in_channels=mid_planes, out_channels=mid_planes, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(mid_planes),
                self.relu,
                nn.Conv2d(in_channels=mid_planes, out_channels=inplanes, kernel_size=1, bias=False),
                nn.BatchNorm2d(inplanes),
                self.relu
            )
            self.conv_block.apply(weights_init_kaiming)

        self.SRAG = SRAG(inplanes=inplanes, is_appearance_spatial_attention=is_appearance_spatial_attention,
                         is_appearance_channel_attention=is_appearance_channel_attention, num=num)

    def forward(self, feat_map):

        b, t, c, h, w = feat_map.size()
        reshape_map = feat_map.view(b * t, c, h, w)
        feat_vect = self.avg(reshape_map).view(b, t, -1)
        embed_feat = self.Embeding(reshape_map).view(b, t, -1, h, w)

        if self.num != '0':
           gap_feat_map0 = self.TRAG(feat_map, reshape_map, feat_vect, embed_feat)

        if self.num == '0':
            gap_feat_map = self.SRAG(feat_map, reshape_map, embed_feat, feat_vect)
        else :
            gap_feat_map = self.SRAG(feat_map, reshape_map, embed_feat, feat_vect, gap_feat_map0)

            gap_feat_map = self.conv_block(gap_feat_map)

        if self.spatial_method == 'max':
            gap_feat_vect = F.max_pool2d(gap_feat_map, gap_feat_map.size()[2:])

        elif self.spatial_method == 'avg':
            gap_feat_vect = F.avg_pool2d(gap_feat_map, gap_feat_map.size()[2:])

        gap_fea_vect = gap_feat_vect.view(b, -1, gap_feat_map.size(1))
        feature = gap_fea_vect.mean(1)
        feature = feature.view(b, -1)
        gap_feat_map = gap_feat_map.view(b, -1, gap_feat_map.size(1), h, w)
        torch.cuda.empty_cache()

        return gap_feat_map, feature





