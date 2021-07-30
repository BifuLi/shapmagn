
ID_COPD={
"12042G":"copd6",
"12105E":"copd7",
"12109M":"copd8",
"12239Z":"copd9",
"12829U":"copd10",
"13216S":"copd1",
"13528L":"copd2",
"13671Q":"copd3",
"13998W":"copd4",
"17441T":"copd5"
}
import os
from shapmagn.datasets.vtk_utils import read_vtk
from shapmagn.global_variable import Shape
from shapmagn.utils.visualizer import visualize_point_fea,visualize_point_pair
def reader(file_path):
    raw_data_dict = read_vtk(file_path)
    points = raw_data_dict["points"][:, None]
    weights = raw_data_dict["weights"][:, None]
    pointfea = raw_data_dict["pointfea"][:, None]
    shape = Shape().set_data(points=points,weights=weights, pointfea=pointfea)
    return shape
folder_path = "/home/zyshen/remote/llr11_mount/zyshen/data/lung_expri/model_eval/deep_feature_pointconv_dirlab_complex_aniso_15dim_normalized_60000/records/fea_visual"
case_name = "12829U"
source_path = os.path.join(folder_path,"{}_source.vtk".format(case_name))
target_path = os.path.join(folder_path,"{}_target.vtk".format(case_name))
flowed_path = os.path.join(folder_path,"{}_flowed.vtk".format(case_name))
source = reader(source_path)
flowed = reader(flowed_path)
target = reader(target_path)
camera_pos = [(-4.924379645467042, 2.17374925796456, 1.5003730890759344), (0.0, 0.0, 0.0),
              (0.40133888001174545, 0.31574165540339943, 0.8597873634998591)]

visualize_point_pair(source.points.squeeze(),target.points.squeeze(),
                     source.pointfea.squeeze(),target.pointfea.squeeze(),
                     "source","target",
camera_pos=camera_pos,
                     rgb_on=True,col_adaptive=False)
