from glob import glob
import os
import copy
import numpy as np
import pyvista as pv
import SimpleITK as sitk
from shapmagn.experiments.datasets.lung.img_sampler import DataProcessing
from shapmagn.datasets.vtk_utils import read_vtk
from shapmagn.shape.shape_utils import get_scale_and_center
import pykeops
"""
High resolution to low resoltuion dirlab mapping

1. flip the last dimension of the high resolution image
2. take the high resoltuion (max between the insp and exp )
3.  padding at the end

Landmark mapping
loc[z] = (high_image.shape[z] - low_index[z]*4 + 1.5)*high_spacing + high_origin ( 2 seems better in practice)

"""

COPD_ID={
    "copd6":"12042G",
    "copd7":"12105E",
    "copd8":"12109M",
    "copd9":"12239Z",
    "copd10":"12829U",
    "copd1":"13216S",
    "copd2":"13528L",
    "copd3":"13671Q",
    "copd4":"13998W",
    "copd5":"17441T"
}

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

#in sitk coord
COPD_spacing = {"copd1": [0.625, 0.625, 2.5],
                "copd2": [0.645, 0.645, 2.5],
                "copd3": [0.652, 0.652, 2.5],
                "copd4": [0.590, 0.590, 2.5],
                "copd5": [0.647, 0.647, 2.5],
                "copd6": [0.633, 0.633, 2.5],
                "copd7": [0.625, 0.625, 2.5],
                "copd8": [0.586, 0.586, 2.5],
                "copd9": [0.664, 0.664, 2.5],
                "copd10": [0.742, 0.742, 2.5]}

# in sitk coord
COPD_shape = {"copd1": [512, 512, 121],
              "copd2": [512, 512, 102],
              "copd3": [512, 512, 126],
              "copd4": [512, 512, 126],
              "copd5": [512, 512, 131],
              "copd6": [512, 512, 119],
              "copd7": [512, 512, 112],
              "copd8": [512, 512, 115],
              "copd9": [512, 512, 116],
              "copd10":[512, 512, 135]}



"""
before mapping
current COPD_ID;copd1 , and the current_mean 26.33421393688401                      current COPD_ID;copd1 , and the current_mean 26.33421393688401
current COPD_ID;copd2 , and the current_mean 21.785988375950623                     current COPD_ID;copd2 , and the current_mean 21.77096701290744
current COPD_ID;copd3 , and the current_mean 12.6391693237195                       current COPD_ID;copd3 , and the current_mean 12.641456423304232
current COPD_ID;copd4 , and the current_mean 29.583560337310402                     current COPD_ID;copd4 , and the current_mean 29.580001001346986
current COPD_ID;copd5 , and the current_mean 30.082670091996842                     current COPD_ID;copd5 , and the current_mean 30.066294774082003
current COPD_ID;copd6 , and the current_mean 28.456016850531874                     current COPD_ID;copd6 , and the current_mean 28.44935880947926
current COPD_ID;copd7 , and the current_mean 21.601714709640365                     current COPD_ID;copd7 , and the current_mean 16.04527530944317 #
current COPD_ID;copd8 , and the current_mean 26.456861641390127                     current COPD_ID;copd8 , and the current_mean 25.831153412715352 #
current COPD_ID;copd9 , and the current_mean 14.860263389215536                     current COPD_ID;copd9 , and the current_mean 14.860883966778562
current COPD_ID;copd10 , and the current_mean 21.805702262166907                    current COPD_ID;copd10 , and the current_mean 27.608698637477584 #
"""




def read_dirlab(file_path, shape):
    dtype = np.dtype("<i2")
    fid = open(file_path, 'rb')
    data = np.fromfile(fid, dtype)
    img_np = data.reshape(shape)
    return img_np

def save_dirlab_into_niigz(file_path, output_path, fname, is_insp=False):
    img_np = read_dirlab(file_path, np.flipud(COPD_shape[fname]))
    img_sitk = sitk.GetImageFromArray(img_np)
    # img_sitk.SetOrigin()
    img_sitk.SetSpacing(np.array(COPD_spacing[fname]))
    if is_insp:
        saving_path = os.path.join(output_path,COPD_ID[fname]+"_INSP_STD_USD_COPD.nii.gz")
    else:
        saving_path = os.path.join(output_path,COPD_ID[fname]+"_EXP_STD_USD_COPD.nii.gz")
    sitk.WriteImage(img_sitk,saving_path)
    if is_insp:
        saving_path = os.path.join(output_path,fname+"_iBHCT.nii.gz")
    else:
        saving_path = os.path.join(output_path,fname+"_eBHCT.nii.gz")
    sitk.WriteImage(img_sitk,saving_path)
    return saving_path



def clean_and_save_pointcloud(file_path, output_folder,case_name):
    raw_data_dict = read_vtk(file_path)
    data_dict = {}
    data_dict["points"] = raw_data_dict["points"].astype(np.float32)
    try:
        data_dict["weights"] = raw_data_dict["dnn_radius"].astype(np.float32)
    except:
        raise ValueError
    data = pv.PolyData(data_dict["points"])
    data.point_arrays["weights"] = data_dict["weights"][:,None]
    fpath = os.path.join(output_folder,os.path.split(file_path)[-1])
    data.save(fpath)
    fpath = os.path.join(output_folder,case_name+'.vtk')
    data.save(fpath)
    return fpath




def read_img(file_path, return_np=True):
    img_sitk = sitk.ReadImage(file_path)
    spacing_itk = img_sitk.GetSpacing()
    origin_itk = img_sitk.GetOrigin()
    img_np = sitk.GetArrayFromImage(img_sitk)
    if return_np:
        return img_np, np.flipud(spacing_itk),np.array([0.,0.,0])
    else:
        return img_sitk, spacing_itk, np.array([0.,0.,0])


def read_axis_reversed_img(file_path, return_np=True):
    img_sitk = sitk.ReadImage(file_path)
    spacing_itk = img_sitk.GetSpacing()
    origin_itk = img_sitk.GetOrigin()
    direction_itk = img_sitk.GetDirection()
    img_np = sitk.GetArrayFromImage(img_sitk)
    img_np = img_np[::-1]
    if return_np:
        return img_np, np.flipud(spacing_itk), np.array([0.,0.,0])
    else:
        img_sitk = sitk.GetImageFromArray(img_np)
        img_sitk.SetSpacing(spacing_itk)
        img_sitk.SetOrigin(np.array([0.,0.,0]))
        img_sitk.SetDirection(direction_itk)
        return img_sitk, spacing_itk, np.array([0.,0.,0])

def compare_dirlab_and_high_nrrd(high_pair_path,case_id = None):
    high_insp_path, high_exp_path = high_pair_path
    dir_insp_exp_shape = COPD_shape[ID_COPD[case_id]]
    high_insp_np, _, _  = read_img(high_insp_path)
    high_insp_shape = np.flipud(high_insp_np.shape)
    high_exp_np, _, _ = read_img(high_exp_path)
    high_exp_shape = np.flipud(high_exp_np.shape)
    print("{}, {} , exp_sz: {}, insp_sz: {}, copd_sz: {}, copd*4_sz: {}".format(case_id,ID_COPD[case_id], high_exp_shape[-1], high_insp_shape[-1], dir_insp_exp_shape[-1], dir_insp_exp_shape[-1]*4))


def process_high_to_dirlab(high_pair_path,case_id=None, saving_folder=None):
    high_insp_path, high_exp_path = high_pair_path
    high_insp, spacing_itk, _ = read_axis_reversed_img(high_insp_path,return_np=False)
    output_spacing = np.array(spacing_itk)
    #output_spacing[-1] = output_spacing[-1]*4
    output_spacing = COPD_spacing[ID_COPD[case_id]]
    processed_insp = DataProcessing.resample_image_itk_by_spacing_and_size(high_insp, output_spacing = output_spacing, output_size=COPD_shape[ID_COPD[case_id]], output_type=None,
                                               interpolator=sitk.sitkBSpline, padding_value=0, center_padding=False)
    high_exp, spacing_itk, _ = read_axis_reversed_img(high_exp_path,return_np=False)
    processed_exp = DataProcessing.resample_image_itk_by_spacing_and_size(high_exp, output_spacing = output_spacing, output_size=COPD_shape[ID_COPD[case_id]], output_type=None,
                                               interpolator=sitk.sitkBSpline, padding_value=0, center_padding=False)
    saving_path = os.path.join(saving_folder,case_id+"_INSP_STD_USD_COPD.nii.gz")
    sitk.WriteImage(processed_insp,saving_path)
    saving_path = os.path.join(saving_folder, ID_COPD[case_id] +"_iBHCT.nii.gz")
    sitk.WriteImage(processed_insp,saving_path)
    saving_path = os.path.join(saving_folder,case_id+"_EXP_STD_USD_COPD.nii.gz")
    sitk.WriteImage(processed_exp,saving_path)
    saving_path = os.path.join(saving_folder,ID_COPD[case_id]+"_eBHCT.nii.gz")
    sitk.WriteImage(processed_exp,saving_path)





def read_landmark_index(f_path):
    """
    :param f_path: the path to the file containing the position of points.
    Points are deliminated by '\n' and X,Y,Z of each point are deliminated by '\t'.
    :return: numpy list of positions.
    """

    with open(f_path) as fp:
        content = fp.read().split('\n')

        # Read number of points from second
        count = len(content) - 1

        # Read the points
        points = np.ndarray([count, 3], dtype=np.float32)
        for i in range(count):
            if content[i] == "":
                break
            temp = content[i].split('\t')
            points[i, 0] = float(temp[0])
            points[i, 1] = float(temp[1])
            points[i, 2] = float(temp[2])
        return points


def get_img_info(img_path):
    img = sitk.ReadImage(img_path)
    origin_itk = img.GetOrigin()
    spacing_itk = img.GetSpacing()
    img_shape_itk = img.GetSize()
    return img_shape_itk, spacing_itk, origin_itk


def transfer_landmarks_from_dirlab_to_high(dirlab_index, high_shape):
    new_index= dirlab_index.copy()
    new_index[:,-1] =(high_shape[-1]- dirlab_index[:,-1]*4) + 2
    return new_index





def process_points(point_path, img_path, case_id, output_folder, is_insp):
    index = read_landmark_index(point_path)
    img_shape_itk, spacing_itk, origin_itk = get_img_info(img_path)
    copd = ID_COPD[case_id]

    print("origin {}_{}:{}".format(copd,"insp" if is_insp else "exp",origin_itk))
    print("size {}_{}:{}".format(copd,"insp" if is_insp else "exp",img_shape_itk))
    downsampled_spacing_itk = np.copy(spacing_itk)
    downsampled_spacing_itk[-1] = downsampled_spacing_itk[-1]*4
    # downsampled_spacing_itk = COPD_spacing[ID_COPD[case_id]]
    print("spatial ratio corrections:")
    print("{} : {},".format(copd,np.array(COPD_spacing[copd])/downsampled_spacing_itk))
    transfered_index = transfer_landmarks_from_dirlab_to_high(index, img_shape_itk)
    physical_points = transfered_index*spacing_itk+origin_itk
    # for i in range(len(physical_points)):
    #     physical_points[i][-1] = spacing_itk[-1] * img_shape_itk[-1] - index[i][-1]* COPD_spacing[ID_COPD[case_id]][-1] + origin_itk[-1]
    data = pv.PolyData(physical_points)
    data.point_arrays["idx"] = np.arange(1,301)
    suffix = "_INSP_STD_USD_COPD.vtk" if is_insp else "_EXP_STD_USD_COPD.vtk"
    fpath = os.path.join(output_folder,case_id+suffix)
    data.save(fpath)
    suffix = "_INSP.vtk" if is_insp else "_EXP.vtk"
    fpath = os.path.join(output_folder,ID_COPD[case_id]+suffix)
    data.save(fpath)
    return physical_points


def get_center(point_path,case_id, is_insp):
    points = read_vtk(point_path)["points"]
    scale, center = get_scale_and_center(points, percentile=95)
    suffix = "_INSP_STD_USD_COPD" if is_insp else "_EXP_STD_USD_COPD"
    print('"{}":{}'.format(case_id+suffix,center[0]))


def compute_nn_dis_between_landmark_and_point_cloud(ldm_path, pc_path, case_id):
    import torch
    from shapmagn.utils.knn_utils import KNN
    from shapmagn.modules_reg.networks.pointconv_util import index_points_group
    landmark = read_vtk(ldm_path)["points"]
    raw_data_dict = read_vtk(pc_path)
    landmark[:,2] = landmark[:,2]+0.5
    pc_tensor = torch.Tensor(raw_data_dict["points"][None]).cuda()
    landmark_tensor = torch.Tensor(landmark[None]).cuda()
    knn = KNN(return_value=False)
    index = knn(landmark_tensor, pc_tensor,K=1)
    nn_pc = index_points_group(pc_tensor, index)
    diff = (landmark.squeeze() - nn_pc.squeeze().cpu().numpy())
    print("the current median shift of the case {} is {}".format(case_id, np.median(diff,0)))
    print("the current std shift of the case {} is {}".format(case_id, np.std(diff,0)))
    print("the current std shift of the case {} is {}".format(case_id,np.mean(np.linalg.norm(diff, ord=2, axis=1))))
    return diff


save_dirlab_IMG_into_niigz = False
get_dirlab_high_shape_info = False
map_high_to_dirlab = False
project_landmarks_from_dirlab_to_high = True
save_cleaned_pointcloud = False
compute_shift = True

root_path = "/home/zyshen/data/dirlab_data" #/playpen-raid1/Data
pc_folder_path = os.path.join(root_path,"DIRLABVascular")
low_folder_path =os.path.join(root_path,"copd")
high_folder_path = os.path.join(root_path,"DIRLABCasesHighRes")
landmark_insp_key = "*_300_iBH_xyz_r1.txt"
img_insp_key = "*_iBHCT.img"
insp_key = "*_INSP_STD_*"

processed_output_path = os.path.join(root_path,"copd/processed_current")
os.makedirs(processed_output_path,exist_ok=True)
pc_insp_path_list= glob(os.path.join(pc_folder_path,insp_key))
pc_exp_path_list = [path.replace("INSP","EXP") for path in pc_insp_path_list]
for exp_path in pc_exp_path_list:
    assert os.path.isfile(exp_path),"the file {} is not exist".format(exp_path)
print("num of {} pair detected".format(len(pc_insp_path_list)))
id_list = [os.path.split(path)[-1].split("_")[0] for path in pc_insp_path_list]
landmark_insp_path_list = [os.path.join(low_folder_path,ID_COPD[_id],ID_COPD[_id],ID_COPD[_id]+"_300_iBH_xyz_r1.txt") for _id in id_list]
landmark_exp_path_list = [os.path.join(low_folder_path,ID_COPD[_id],ID_COPD[_id],ID_COPD[_id]+"_300_eBH_xyz_r1.txt") for _id in id_list]

high_img_insp_path_list = [os.path.join(high_folder_path,_id+"_INSP_STD_USD_COPD.nrrd") for _id in id_list]
high_img_exp_path_list = [os.path.join(high_folder_path,_id+"_EXP_STD_USD_COPD.nrrd") for _id in id_list]

low_processed_folder = os.path.join(processed_output_path, "dirlab")
os.makedirs(low_processed_folder, exist_ok=True)

low_img_insp_path_list = [os.path.join(low_processed_folder,_id+"_INSP_STD_USD_COPD.nii.gz") for _id in id_list]
low_img_exp_path_list = [os.path.join(low_processed_folder,_id+"_EXP_STD_USD_COPD.nii.gz") for _id in id_list]

if get_dirlab_high_shape_info:
    for i, _id in enumerate(id_list):
        high_img_insp_path, high_img_exp_path = high_img_insp_path_list[i], high_img_exp_path_list[i]
        compare_dirlab_and_high_nrrd(high_pair_path=[high_img_insp_path, high_img_exp_path],case_id = _id)

high_to_dirlab_processed_folder =  os.path.join(processed_output_path, "process_to_dirlab")
os.makedirs(high_to_dirlab_processed_folder, exist_ok=True)

landmark_processed_folder =  os.path.join(processed_output_path, "landmark_processed_colored")
os.makedirs(landmark_processed_folder, exist_ok=True)
if project_landmarks_from_dirlab_to_high:
    landmark_insp_physical_pos_list = [ process_points(landmark_insp_path_list[i], high_img_insp_path_list[i], id_list[i],landmark_processed_folder, is_insp=True) for i in range(len(id_list))]
    landmark_exp_physical_pos_list = [ process_points(landmark_exp_path_list[i], high_img_exp_path_list[i],id_list[i],landmark_processed_folder, is_insp=False) for i in range(len(id_list))]
    init_diff_list = []
    for i in range(len(id_list)):
        copid = "copd{}".format(i+1)
        index = id_list.index(COPD_ID[copid])
        diff = np.linalg.norm(landmark_insp_physical_pos_list[index]-landmark_exp_physical_pos_list[index],2,1).mean()
        init_diff_list.append(diff)
        print("COPD_ID;{} , and the current mse is {}".format(copid,diff))
    print("overall mean {}".format(np.mean(init_diff_list)))
    print("overall median {}".format(np.median(init_diff_list)))

cleaned_pc_folder = os.path.join(processed_output_path, "cleaned_pointcloud")
os.makedirs(cleaned_pc_folder, exist_ok=True)
if save_cleaned_pointcloud:
    for i, _id in enumerate(id_list):
        try:
            clean_and_save_pointcloud(pc_insp_path_list[i], cleaned_pc_folder,ID_COPD[_id]+"_INSP")
            clean_and_save_pointcloud(pc_exp_path_list[i], cleaned_pc_folder,ID_COPD[_id]+"_EXP")
        except:
            print("id_{} failed".format(_id))


shift_diff = []
if compute_shift:
    for i,_id in enumerate(id_list):
        cleaned_insp_path = os.path.join(cleaned_pc_folder,ID_COPD[_id]+"_INSP"+".vtk")
        cleaned_exp_path = os.path.join(cleaned_pc_folder,ID_COPD[_id]+"_EXP"+".vtk")
        landmark_insp_path =  os.path.join(landmark_processed_folder,ID_COPD[_id]+"_INSP"+".vtk")
        landmark_exp_path =  os.path.join(landmark_processed_folder,ID_COPD[_id]+"_EXP"+".vtk")
        insp_diff = compute_nn_dis_between_landmark_and_point_cloud(landmark_insp_path,cleaned_insp_path,_id)
        exp_diff = compute_nn_dis_between_landmark_and_point_cloud(landmark_exp_path,cleaned_exp_path,_id)
        shift_diff.append(insp_diff)
        shift_diff.append(exp_diff)
    shift_diff = np.concatenate(shift_diff,0)
    print("the current median shift of all dirlab cases is {}".format( np.median(shift_diff,0)))
    print("the current std shift of all dirlab cases is {}".format( np.std(shift_diff,0)))
    print("overall dist  of all dirlab mean {}".format(np.mean(np.linalg.norm(shift_diff, ord=2, axis=1))))





















"""
num of 10 pair detected
origin copd1_insp:(-148.0, -145.0, -310.625)
size copd1_insp:(512, 512, 482)
spatial ratio corrections:
copd1 : [1. 1. 1.],
origin copd5_insp:(-145.9, -175.9, -353.875)
size copd5_insp:(512, 512, 522)
spatial ratio corrections:
copd5 : [1.00079816 1.00079816 1.        ],
origin copd8_insp:(-142.3, -147.4, -313.625)
size copd8_insp:(512, 512, 458)
spatial ratio corrections:
copd8 : [1.00010581 1.00010581 1.        ],
origin copd4_insp:(-124.1, -151.0, -308.25)
size copd4_insp:(512, 512, 501)
spatial ratio corrections:
copd4 : [1.00026448 1.00026448 1.        ],
origin copd6_insp:(-158.4, -162.0, -299.625)
size copd6_insp:(512, 512, 474)
spatial ratio corrections:
copd6 : [1.00029709 1.00029709 1.        ],
origin copd9_insp:(-156.1, -170.0, -310.25)
size copd9_insp:(512, 512, 461)
spatial ratio corrections:
copd9 : [0.99990664 0.99990664 1.        ],
origin copd2_insp:(-176.9, -165.0, -254.625)
size copd2_insp:(512, 512, 406)
spatial ratio corrections:
copd2 : [1.00072766 1.00072766 1.        ],
origin copd7_insp:(-150.7, -160.0, -301.375)
size copd7_insp:(512, 512, 446)
spatial ratio corrections:
copd7 : [1. 1. 1.],
origin copd3_insp:(-149.4, -167.0, -343.125)
size copd3_insp:(512, 512, 502)
spatial ratio corrections:
copd3 : [0.99947267 0.99947267 1.        ],
origin copd10_insp:(-189.0, -176.0, -355.0)
size copd10_insp:(512, 512, 535)
spatial ratio corrections:
copd10 : [0.99974669 0.99974669 1.        ],
origin copd1_exp:(-148.0, -145.0, -305.0)
size copd1_exp:(512, 512, 473)
spatial ratio corrections:
copd1 : [1. 1. 1.],
origin copd5_exp:(-145.9, -175.9, -353.875)
size copd5_exp:(512, 512, 522)
spatial ratio corrections:
copd5 : [1.00079816 1.00079816 1.        ],
origin copd8_exp:(-142.3, -147.4, -294.625)
size copd8_exp:(512, 512, 426)
spatial ratio corrections:
copd8 : [1.00010581 1.00010581 1.        ],
origin copd4_exp:(-124.1, -151.0, -283.25)
size copd4_exp:(512, 512, 461)
spatial ratio corrections:
copd4 : [1.00026448 1.00026448 1.        ],
origin copd6_exp:(-158.4, -162.0, -291.5)
size copd6_exp:(512, 512, 461)
spatial ratio corrections:
copd6 : [1.00029709 1.00029709 1.        ],
origin copd9_exp:(-156.1, -170.0, -259.625)
size copd9_exp:(512, 512, 380)
spatial ratio corrections:
copd9 : [0.99990664 0.99990664 1.        ],
origin copd2_exp:(-177.0, -165.0, -237.125)
size copd2_exp:(512, 512, 378)
spatial ratio corrections:
copd2 : [1.00072766 1.00072766 1.        ],
origin copd7_exp:(-151.0, -160.0, -284.25)
size copd7_exp:(512, 512, 407)
spatial ratio corrections:
copd7 : [1. 1. 1.],
origin copd3_exp:(-149.4, -167.0, -319.375)
size copd3_exp:(512, 512, 464)
spatial ratio corrections:
copd3 : [0.99947267 0.99947267 1.        ],
origin copd10_exp:(-189.0, -176.0, -346.25)
size copd10_exp:(512, 512, 539)
spatial ratio corrections:
copd10 : [0.99974669 0.99974669 1.        ],
current COPD_ID;copd1 , and the current_mean 26.33421393688401
current COPD_ID;copd2 , and the current_mean 21.77096701290744
current COPD_ID;copd3 , and the current_mean 12.641456423304232
current COPD_ID;copd4 , and the current_mean 29.580001001346986
current COPD_ID;copd5 , and the current_mean 30.066294774082003
current COPD_ID;copd6 , and the current_mean 28.44935880947926
current COPD_ID;copd7 , and the current_mean 16.04527530944317
current COPD_ID;copd8 , and the current_mean 25.831153412715352
current COPD_ID;copd9 , and the current_mean 14.860883966778562
current COPD_ID;copd10 , and the current_mean 27.608698637477584
average mean 23.31883032844186

Process finished with exit code 0

"""