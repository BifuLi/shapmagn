from shapmagn.metrics.losses import *
from shapmagn.datasets.dataset import RegistrationDataset
from shapmagn.shape.point_cloud import PointCloud
from shapmagn.shape.surface_mesh import SurfaceMesh
from shapmagn.shape.poly_line import PolyLine
shape_type = "pointcloud"
SHAPE_POOL = {"pointcloud":PointCloud, "surfacemesh":SurfaceMesh, "polyline":PolyLine}
Shape = SHAPE_POOL[shape_type]

from shapmagn.utils.keops_kernels import LazyKeopsKernel
from shapmagn.utils.torch_kernels import TorchKernel
from shapmagn.models.model_opt_lddmm import LDDMMOPT
LOSS_POOL ={"current": CurrentDistance, "varifold":VarifoldDistance, "geomloss":GeomDistance, "l2":L2Distance}
DATASET_POOL = {
    "pair_dataset": RegistrationDataset
}
MODEL_POOL = {"lddmm_opt": LDDMMOPT}

from shapmagn.utils.point_sampler import grid_shape_sampler, uniform_shape_sampler
from shapmagn.utils.point_interpolator import kernel_interpolator, spline_intepolator

SHAPE_SAMPLER_POOL = {"point_grid": grid_shape_sampler, "point_uniform":uniform_shape_sampler}
# INTERPOLATOR_POOL = {"point_kernel":kernel_interpolator, "point_spline": spline_intepolator}

