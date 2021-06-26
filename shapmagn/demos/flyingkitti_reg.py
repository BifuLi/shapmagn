import os, sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))
from shapmagn.utils.module_parameters import ParameterDict
from shapmagn.datasets.data_utils import get_file_name, generate_pair_name, compute_interval, read_json_into_list, \
    get_obj, get_pair_obj
from shapmagn.shape.shape_pair_utils import create_shape_pair
from shapmagn.models_reg.multiscale_optimization import build_single_scale_model_embedded_solver, build_multi_scale_solver
from shapmagn.global_variable import MODEL_POOL,Shape, shape_type
from shapmagn.utils.visualizer import visualize_point_fea, visualize_point_pair, visualize_source_flowed_target_overlap
from shapmagn.demos.demo_utils import *
from shapmagn.experiments.datasets.toy.toy_utils import *
from shapmagn.utils.utils import memory_sort, add_zero_last_dim, sigmoid_decay, to_tensor

# import pykeops
# pykeops.clean_pykeops()

assert shape_type == "pointcloud", "set shape_type = 'pointcloud'  in global_variable.py"
device = torch.device("cpu") # cuda:0  cpu
reader_obj = "flyingkitti_nonocc_utils.flyingkitti_nonocc_reader()"
normalizer_obj = "flyingkitti_nonocc_utils.flyingkitti_nonocc_normalizer()"
sampler_obj = "flyingkitti_nonocc_utils.flyingkitti_nonocc_sampler(num_sample=8192)"
pair_postprocess_obj = "flyingkitti_nonocc_utils.flyingkitti_nonocc_pair_postprocess()"
pair_postprocess = obj_factory(pair_postprocess_obj)

assert shape_type == "pointcloud", "set shape_type = 'pointcloud'  in global_variable.py"
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
server_path = "./" # "/playpen-raid1/"#"/home/zyshen/remote/llr11_mount/"
source_path =  server_path+"data/flying3d_data/0000000/pc1.npy"
target_path = server_path+"data/flying3d_data/0000000/pc2.npy"
get_obj_func = get_pair_obj(reader_obj, normalizer_obj, sampler_obj, pair_postprocess_obj,device,expand_bch_dim=True)
source_obj,target_obj, source_interval,target_interval = get_obj_func(source_path, target_path)
min_interval = min(source_interval, target_interval)
print("the source and the target min interval is {},{}".format(source_interval,target_interval))
input_data = {"source":source_obj,"target":target_obj}
create_shape_pair_from_data_dict = obj_factory("shape_pair_utils.create_source_and_target_shape()")
source, target = create_shape_pair_from_data_dict(input_data)
shape_pair = create_shape_pair(source, target)

###############  do registration ###########################s############
#
# """ Experiment 1:  gradient flow """
# task_name = "gradient_flow"
# solver_opt = ParameterDict()
# record_path = server_path+"output/toy_demo/{}".format(task_name)
# os.makedirs(record_path,exist_ok=True)
# solver_opt["record_path"] = record_path
# model_name = "gradient_flow_opt"
# model_opt =ParameterDict()
# model_opt["interpolator_obj"] ="point_interpolator.nadwat_kernel_interpolator(scale=0.1, exp_order=2)"
# model_opt[("sim_loss", {}, "settings for sim_loss_opt")]
# model_opt['sim_loss']['loss_list'] =  ["geomloss"]
# model_opt['sim_loss'][("geomloss", {}, "settings for geomloss")]
# model_opt['sim_loss']['geomloss']["attr"] = "points"
# blur = 0.1
# model_opt['sim_loss']['geomloss']["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur={}, scaling=0.8,debias=False)".format(blur)
# model = MODEL_POOL[model_name](model_opt)
# solver = build_single_scale_model_embedded_solver(solver_opt,model)
# model.init_reg_param(shape_pair)
# shape_pair = solver(shape_pair)
# print("the registration complete")
# gif_folder = os.path.join(record_path,"gif")
# os.makedirs(gif_folder,exist_ok=True)
# saving_gif_path = os.path.join(gif_folder,task_name+".gif")
# fea_to_map =  shape_pair.source.points
# mapped_fea = get_omt_mapping(model_opt['sim_loss']['geomloss'], source, target,fea_to_map ,p=2,mode="hard",confid=0.1)
# flow_points = shape_pair.flowed.points-shape_pair.source.points
# visualize_source_flowed_target_overlap(
#     shape_pair.source.points,shape_pair.flowed.points,shape_pair.target.points,
#     fea_to_map,fea_to_map, mapped_fea,
#     "source", "gradient_flow","target",
#     flow_points,
#     rgb_on=  [True, True, True],
#     saving_gif_path=None)





# Experiment 4:  optimization based discrete flow
task_name = "discrete_flow"
gradient_flow_mode = True
solver_opt = ParameterDict()
record_path = server_path+"output/toy_demo/{}".format(task_name)
solver_opt["record_path"] = record_path
solver_opt["save_2d_capture_every_n_iter"] = -1
solver_opt["point_grid_scales"] =  [-1]
solver_opt["iter_per_scale"] = [50] if not gradient_flow_mode else [5]
solver_opt["rel_ftol_per_scale"] = [ 1e-9, 1e-9, 1e-9]
solver_opt["init_lr_per_scale"] = [1e-1,1e-1,1e-1]
solver_opt["save_3d_shape_every_n_iter"] = 10
solver_opt["shape_sampler_type"] = "point_grid"
solver_opt["stragtegy"] = "use_optimizer_defined_here" if not gradient_flow_mode else "use_optimizer_defined_from_model"
solver_opt[("optim", {}, "setting for the optimizer")]
solver_opt[("scheduler", {}, "setting for the scheduler")]
solver_opt["optim"]["type"] = "sgd" #lbgfs
solver_opt["scheduler"]["type"] = "step_lr"
solver_opt["scheduler"][("step_lr",{},"settings for step_lr")]
solver_opt["scheduler"]["step_lr"]["gamma"] = 0.5
solver_opt["scheduler"]["step_lr"]["step_size"] = 30
model_name = "discrete_flow_opt"
model_opt =ParameterDict()
model_opt["drift_every_n_iter"] = 10
use_aniso_kernel = True
model_opt["use_aniso_kernel"] = use_aniso_kernel
model_opt["fix_anistropic_kernel_using_initial_shape"] = True and use_aniso_kernel
model_opt["fix_feature_using_initial_shape"] =True
kernel_size = 1 # iso 0.08
#spline_param="cov_sigma_scale=0.01,aniso_kernel_scale={},principle_weight=(3.,1.,1.),eigenvalue_min=0.1,iter_twice=True".format(kernel_size)
spline_param="cov_sigma_scale=0.3,aniso_kernel_scale={},eigenvalue_min=0.2,iter_twice=True, fixed={}, leaf_decay=False, self_center=False".format(kernel_size,model_opt["fix_anistropic_kernel_using_initial_shape"] )
if not use_aniso_kernel:
    model_opt["spline_kernel_obj"] ="point_interpolator.NadWatIsoSpline(kernel_scale={}, exp_order=2)".format(kernel_size)
else:
    model_opt["spline_kernel_obj"] ="point_interpolator.NadWatAnisoSpline(exp_order=2,{})".format(spline_param)
model_opt["interp_kernel_obj"] ="point_interpolator.nadwat_kernel_interpolator(exp_order=2)"  # only used for multi-scale registration
#model_opt["pair_feature_extractor_obj"] ="local_feature_extractor.pair_feature_extractor(fea_type_list=['eigenvalue_prod'],weight_list=[1], radius=0.2,include_pos=True)"
model_opt["gradient_flow_mode"] = gradient_flow_mode
model_opt["running_result_visualize"] = True
model_opt[("gradflow_guided", {}, "settings for gradflow guidance")]
model_opt["gradflow_guided"] ['gradflow_blur_init']= 0.1
model_opt["gradflow_guided"] ['update_gradflow_blur_by_raito']= 0.5
model_opt["gradflow_guided"] ['gradflow_blur_min']= 0.1
model_opt["gradflow_guided"] [("geomloss", {}, "settings for geomloss")]
model_opt["gradflow_guided"]["geomloss"]["attr"] = "points" #todo  the pointfea will be  more generalized choice
model_opt["gradflow_guided"]["geomloss"]["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur=blurplaceholder, reach=None,scaling=0.8,debias=False)"

model_opt[("sim_loss", {}, "settings for sim_loss_opt")]
model_opt['sim_loss']['loss_list'] = ["geomloss"]
model_opt['sim_loss'][("geomloss", {}, "settings for geomloss")]
model_opt['sim_loss']['geomloss']["attr"] = "points" #todo  the pointfea will be  more generalized choice
blur = 0.01
model_opt['sim_loss']['geomloss']["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur={}, scaling=0.8, debias=False)".format(blur)

model = MODEL_POOL[model_name](model_opt)
solver = build_multi_scale_solver(solver_opt,model)
model.init_reg_param(shape_pair)
shape_pair = solver(shape_pair)
print("the registration complete")
gif_folder = os.path.join(record_path,"gif")
os.makedirs(gif_folder,exist_ok=True)
saving_gif_path = os.path.join(gif_folder,task_name+".gif")
fea_to_map =  shape_pair.source.points[0]
blur = 0.1
model_opt['sim_loss']['geomloss']["geom_obj"] = model_opt['sim_loss']['geomloss']["geom_obj"].replace("blurplaceholder",str(blur))
shape_pair.source, shape_pair.target = model.extract_fea(shape_pair.source, shape_pair.target)
mapped_fea = get_omt_mapping(model_opt['sim_loss']['geomloss'],shape_pair.source, shape_pair.target,fea_to_map,p=2,mode="hard",confid=0.0)
flow_points = shape_pair.flowed.points-shape_pair.source.points
visualize_source_flowed_target_overlap(
    shape_pair.source.points,shape_pair.flowed.points,shape_pair.target.points,
    fea_to_map,fea_to_map, mapped_fea,
    "source", "discrete_flow","target",
    flow_points,
    rgb_on=  [True, True, True],
    saving_gif_path=None)



def update_sigma(sigma, iter):
    sigma = float(
        max(sigmoid_decay(iter, static=10, k=8) * 1.,0.01))
    return sigma






# Experiment 4:  optimization based discrete flow
task_name = "discrete_flow"
gradient_flow_mode = True
solver_opt = ParameterDict()
record_path = server_path+"output/toy_demo/{}".format(task_name)
solver_opt["record_path"] = record_path
solver_opt["save_2d_capture_every_n_iter"] = -1
solver_opt["point_grid_scales"] =  [-1]
solver_opt["iter_per_scale"] = [200] if not gradient_flow_mode else [3]
solver_opt["rel_ftol_per_scale"] = [ 1e-9, 1e-9, 1e-9]
solver_opt["init_lr_per_scale"] = [1e-1,1e-1,1e-1]
solver_opt["save_3d_shape_every_n_iter"] = 10
solver_opt["shape_sampler_type"] = "point_grid"
solver_opt["stragtegy"] = "use_optimizer_defined_here" if not gradient_flow_mode else "use_optimizer_defined_from_model"
solver_opt[("optim", {}, "setting for the optimizer")]
solver_opt[("scheduler", {}, "setting for the scheduler")]
solver_opt["optim"]["type"] = "lbgfs" #lbgfs
solver_opt["scheduler"]["type"] = "step_lr"
solver_opt["scheduler"][("step_lr",{},"settings for step_lr")]
solver_opt["scheduler"]["step_lr"]["gamma"] = 0.5
solver_opt["scheduler"]["step_lr"]["step_size"] = 30
model_name = "discrete_flow_opt"
model_opt =ParameterDict()
model_opt["drift_every_n_iter"] = 50
use_aniso_kernel = True
model_opt["use_aniso_kernel"] = use_aniso_kernel
model_opt["fix_anistropic_kernel_using_initial_shape"] = False and use_aniso_kernel
model_opt["fix_feature_using_initial_shape"] =True
kernel_size = 0.0 # iso 0.08
#spline_param="cov_sigma_scale=0.01,aniso_kernel_scale={},principle_weight=(3.,1.,1.),eigenvalue_min=0.1,iter_twice=True".format(kernel_size)
spline_param="cov_sigma_scale=0.04,aniso_kernel_scale=[0.03, 0.05,0.07],aniso_kernel_weight=[0.2,0.3,0.5],eigenvalue_min=0.1,iter_twice=True, fixed={}, leaf_decay=False, self_center=False".format(model_opt["fix_anistropic_kernel_using_initial_shape"] )
if not use_aniso_kernel:
    model_opt["spline_kernel_obj"] ="point_interpolator.NadWatIsoSpline(kernel_scale=[0.05,0.08, 0.1],kernel_weight=[0.1,0.3,0.6], exp_order=2)".format(kernel_size)
else:
    model_opt["spline_kernel_obj"] ="point_interpolator.NadWatAnisoSpline(exp_order=2,{})".format(spline_param)
model_opt["interp_kernel_obj"] ="point_interpolator.nadwat_kernel_interpolator(exp_order=2)"  # only used for multi-scale registration
#model_opt["pair_feature_extractor_obj"] ="local_feature_extractor.pair_feature_extractor(fea_type_list=['eigenvalue_prod'],weight_list=[1], std_normalize=False, radius=0.05,include_pos=True)"
model_opt["gradient_flow_mode"] = gradient_flow_mode
model_opt["running_result_visualize"] = True
model_opt[("gradflow_guided", {}, "settings for gradflow guidance")]
model_opt["gradflow_guided"] ['gradflow_blur_init']= 0.0005
model_opt["gradflow_guided"] ['update_gradflow_blur_by_raito']= 0.5
model_opt["gradflow_guided"] ['gradflow_blur_min']= 0.0005
model_opt["gradflow_guided"] [("geomloss", {}, "settings for geomloss")]
model_opt["gradflow_guided"]["geomloss"]["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur=blurplaceholder, reach=5,scaling=0.8,debias=False)"

# model_opt[("sim_loss", {}, "settings for sim_loss_opt")]
# model_opt['sim_loss']['loss_list'] = ["gmm"]
# model_opt['sim_loss'][("gmm", {}, "settings for geomloss")]
# model_opt['sim_loss']['gmm']["attr"] = "points"
# model_opt['sim_loss']['gmm']["sigma"] = 0.001
# model_opt['sim_loss']['gmm']["w_noise"] = 0.0
# model_opt['sim_loss']['gmm']["mode"] = "sym_neglog_likelihood"  # sym_neglog_likelihood   neglog_likelihood
#
# #

model_opt[("sim_loss", {}, "settings for sim_loss_opt")]
model_opt['sim_loss']['loss_list'] = ["geomloss"]
model_opt['sim_loss'][("geomloss", {}, "settings for geomloss")]
model_opt['sim_loss']['geomloss']["attr"] = "points" #todo  the pointfea will be  more generalized choice
blur = 0.005
model_opt['sim_loss']['geomloss']["geom_obj"] = "geomloss.SamplesLoss(loss='sinkhorn',blur={}, scaling=0.8,reach=1., debias=False)".format(blur)


model = MODEL_POOL[model_name](model_opt)
solver = build_multi_scale_solver(solver_opt,model)
model.init_reg_param(shape_pair)
shape_pair = solver(shape_pair)
print("the registration complete")



model_opt["running_result_visualize"] = True

use_aniso_kernel = True
model_opt["use_aniso_kernel"] = use_aniso_kernel
model_opt["fix_anistropic_kernel_using_initial_shape"] = True and use_aniso_kernel
model_opt["fix_feature_using_initial_shape"] =True
kernel_size = 0.04 # iso 0.08
spline_param="cov_sigma_scale=0.01,aniso_kernel_scale={},principle_weight=(5.,1.),eigenvalue_min=0.1,iter_twice=True,leaf_decay=False,self_center=False".format(kernel_size)
#spline_param="cov_sigma_scale=0.04,aniso_kernel_scale={},eigenvalue_min=0.1,iter_twice=True, fixed={}, leaf_decay=False, self_center=False".format(kernel_size,model_opt["fix_anistropic_kernel_using_initial_shape"] )
if not use_aniso_kernel:
    model_opt["spline_kernel_obj"] ="point_interpolator.NadWatIsoSpline(kernel_scale={}, exp_order=2)".format(kernel_size)
else:
    model_opt["spline_kernel_obj"] ="point_interpolator.NadWatAnisoSpline(exp_order=2,{})".format(spline_param)
model_opt["interp_kernel_obj"] ="point_interpolator.nadwat_kernel_interpolator(exp_order=2)"  # only used for multi-scale registration
#model_opt["pair_feature_extractor_obj"] ="local_feature_extractor.pair_feature_extractor(fea_type_list=['eigenvalue_prod'],weight_list=[1], std_normalize=False, radius=0.05,include_pos=True)"
model_opt["gradient_flow_mode"] = gradient_flow_mode



shape_pair.source = shape_pair.flowed
shape_pair.control_points = shape_pair.flowed_control_points
model = MODEL_POOL[model_name](model_opt)
solver = build_multi_scale_solver(solver_opt,model)
model.init_reg_param(shape_pair)
shape_pair = solver(shape_pair)
print("the registration complete")