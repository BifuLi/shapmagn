import os, sys
sys.path.insert(0, os.path.abspath('../..'))
import copy
import numpy as np
import open3d as o3
from probreg import cpd, filterreg
import transformations as trans
from probreg import features
import torch

# load source and target point cloud
def estimate_normals(pcd, params):
    pcd.estimate_normals(search_param=params)
    pcd.orient_normals_to_align_with_direction()

source = o3.io.read_point_cloud('./data/toy_demo_data/bunny.pcd')
source.transform(np.array([[np.cos(0), -np.sin(0), 0.0, 0.0],
                           [np.sin(0), np.cos(0), 0.0, 0.0],
                           [0.0, 0.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0, 0.1]]))
target = copy.deepcopy(source)
# transform target point cloud
th = np.deg2rad(120.0)
target.transform(np.array([[np.cos(th), -np.sin(th), 0.0, 1.2],
                           [np.sin(th), np.cos(th), 0.0, 0.3],
                           [0.0, 0.0, 1.0, 1.6],
                           [0.0, 0.0, 0.0, 1.0]]))
source = source.voxel_down_sample(voxel_size=0.05)
target = target.voxel_down_sample(voxel_size=0.05)
cv = lambda x: np.asarray(x.points if isinstance(x, o3.geometry.PointCloud) else x)
# source_fea = features.FPFH()(cv(source)).astype(np.float32)[None]
# target_fea = features.FPFH()(cv(source)).astype(np.float32)[None]
source_fea = None
target_fea = None



# # Experiment 1  run cpd registration from probreg package
# tf_param, _, _ = cpd.registration_cpd(source, target,tf_type_name='rigid')
# result = copy.deepcopy(source)
# result.points = tf_param.transform(result.points)
#
# # draw result
# source.paint_uniform_color([1, 0, 0])
# target.paint_uniform_color([0, 1, 0])
# result.paint_uniform_color([0, 0, 1])
# o3.visualization.draw_geometries([source, target, result])


# cbs = []#[callbacks.Open3dVisualizerCallback(source, target)]
# objective_type = 'pt2pt'
# tf_param, _, _ = filterreg.registration_filterreg(source, target,
#                                                   objective_type=objective_type,
#                                                   sigma2=1, feature_fn=features.FPFH(),
#                                                   callbacks=cbs)
# result = copy.deepcopy(source)
# result.points = tf_param.transform(result.points)
#
# # draw result
# source.paint_uniform_color([1, 0, 0])
# target.paint_uniform_color([0, 1, 0])
# result.paint_uniform_color([0, 0, 1])
# o3.visualization.draw_geometries([source, target, result])






# Experiment 2 run prealign registration
from shapmagn.global_variable import *
from shapmagn.models.multiscale_optimization import *
from shapmagn.utils.module_parameters import ParameterDict
from shapmagn.datasets.data_utils import compute_interval
from shapmagn.demos.demo_utils import get_omt_mapping
from shapmagn.utils.visualizer import *
totensor = lambda x: torch.tensor(np.asarray(x.points).astype(np.float32))
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu") #"cuda:0" if torch.cuda.is_available() else "cpu"

source_points = totensor(source)[None].to(device)
target_points = totensor(target)[None].to(device)
source = Shape().set_data(points=source_points,pointfea=source_fea)
target = Shape().set_data(points=target_points,pointfea=target_fea)
compute_interval(source.points[0].cpu().numpy())
shape_pair = create_shape_pair(source, target)


task_name = "prealign_opt"
solver_opt = ParameterDict()
record_path = "./output/prealign_demo/{}".format(task_name)
os.makedirs(record_path,exist_ok=True)
solver_opt = ParameterDict()
record_path = "./output/prealign_demo/{}".format(task_name)
os.makedirs(record_path,exist_ok=True)
solver_opt["record_path"] = record_path
solver_opt["save_2d_capture_every_n_iter"] = 1
solver_opt["capture_plot_obj"] = "visualizer.capture_plotter()"
model_name = "prealign_opt"
model_opt =ParameterDict()
model_opt[("sim_loss", {}, "settings for sim_loss_opt")]
model_opt["module_type"] = "gradflow_prealign"
model_opt[("gradflow_prealign", {}, "settings for gradflow_prealign")]
blur = 0.01#0.05
model_opt["gradflow_prealign"]["method_name"]="rigid"  # affine
model_opt["gradflow_prealign"]["gradflow_mode"]="ot_mapping"
model_opt["gradflow_prealign"]["niter"] = 10
model_opt["gradflow_prealign"] ['plot'] = True
model_opt["gradflow_prealign"]["search_init_transform"]=False
model_opt["gradflow_prealign"][("geomloss", {}, "settings for geomloss")]
model_opt["gradflow_prealign"]['geomloss']["mode"] = "soft"
model_opt["gradflow_prealign"]['geomloss']["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur={}, scaling=0.8,debias=False)".format(blur)
model_opt["gradflow_prealign"]["pair_feature_extractor_obj"] ="local_feature_extractor.pair_feature_FPFH_extractor(radius_normal=0.1, radius_feature=0.5)" # it only works for the same scale

model_opt['sim_loss']['loss_list'] =  ["geomloss"]
model_opt['sim_loss'][("geomloss", {}, "settings for geomloss")]
model_opt['sim_loss']['geomloss']["attr"] = "pointfea"
# model_opt['sim_loss']['geomloss']["mode"] = "pointfea"
model_opt['sim_loss']['geomloss']["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur={}, scaling=0.8,debias=False)".format(blur)
model = MODEL_POOL[model_name](model_opt)
solver = build_single_scale_model_embedded_solver(solver_opt,model)
model.init_reg_param(shape_pair)
shape_pair = solver(shape_pair)
print("the registration complete")
gif_folder = os.path.join(record_path,"gif")
os.makedirs(gif_folder,exist_ok=True)
saving_gif_path = os.path.join(gif_folder,task_name+".gif")
fea_to_map =  shape_pair.source.points[0]
mapped_fea = get_omt_mapping(model_opt["gradflow_prealign"]['geomloss'], source, target,fea_to_map ,p=2,mode="hard",confid=0.1)
# visualize_multi_point([shape_pair.source.points[0],shape_pair.flowed.points[0],shape_pair.target.points[0]],
#                      [fea_to_map,fea_to_map, mapped_fea],
#                      ["source", "gradient_flow","target"],
#                         [True, True, True])
visualize_point_overlap(shape_pair.source.points, shape_pair.target.points, shape_pair.source.weights, shape_pair.target.weights, title="source and target points", point_size=(10, 10),
                        rgb_on=False, opacity=(1.0, 1.0))
visualize_point_overlap(shape_pair.flowed.points, shape_pair.target.points, shape_pair.flowed.weights, shape_pair.target.weights, title="prealigned and target points", point_size=(10, 10),
                        rgb_on=False, opacity=(1.0, 1.0))



