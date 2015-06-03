"""
simple devices
"""
from .ai import ai
from .ao import ao
from .bi import bi
from .bo import bo

from .scaler import Scaler
from .struck import Struck
from .srs570 import SRS570
from .mca import DXP, MCA, MultiXMAP, ROI
from .scan import Scan
from .transform import Transform

from .ad_base import AD_Camera
from .ad_fileplugin import AD_FilePlugin
from .ad_image import AD_ImagePlugin
from .ad_overlay import AD_OverlayPlugin
from .ad_perkinelmer import AD_PerkinElmer

Mca = MCA

