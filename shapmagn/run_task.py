""" run shape registration

"""

import os, sys
import shutil
sys.path.insert(0,os.path.abspath('..'))
sys.path.insert(0,os.path.abspath('.'))
sys.path.insert(0,os.path.abspath('../shapmagn'))
import torch
torch.backends.cudnn.benchmark=True
import shapmagn.utils.module_parameters as pars
from abc import ABCMeta, abstractmethod
from shapmagn.pipeline.run_pipeline import run_one_task



class BaseTask():
    __metaclass__ = ABCMeta
    def __init__(self,name):
        self.name = name

    @abstractmethod
    def save(self):
        pass

class ModelTask(BaseTask):
    """
    base module for task setting files (.json)
    """
    def __init__(self,name,path='../settings/base_task_settings.json'):
        super(ModelTask,self).__init__(name)
        self.task_par = pars.ParameterDict()
        self.task_par.load_JSON(path)

    def save(self,path= '../settings/task_settings.json'):
        self.task_par.write_ext_JSON(path)





def init_task_env(setting_path,output_root_path, task_name):
    """
    create task environment.

    :param setting_path: the path to load 'task_setting.json'
    :param output_root_path: the output path
    :param task_name: task name i.e. run_unet, run_with_ncc_loss
    :return:
    """
    tsm_json_path = os.path.join(setting_path, 'task_setting.json')
    assert os.path.isfile(tsm_json_path),"task setting not exists"
    tsm = ModelTask('task_reg',tsm_json_path)
    tsm.task_par['tsk_set']['task_name'] = task_name
    tsm.task_par['tsk_set']['output_root_path'] = output_root_path
    return tsm






def __do_registration(args):
    """
    set running env and run the task

    :param args: the parsed arguments
    :param pipeline:a Pipeline object
    :return: a Pipeline object
    """

    output_root_path = args.output_root_path
    dataset_path =args.dataset_folder
    task_name = args.task_name
    setting_folder_path = args.setting_folder_path
    task_output_path = os.path.join(output_root_path,task_name)
    os.makedirs(task_output_path, exist_ok=True)
    shutil.copytree(dataset_path,output_root_path)
    tsm = init_task_env(setting_folder_path,output_root_path,task_name)
    if args.eval:
        tsm = addition_test_setting(args,tsm)
    tsm.task_par['tsk_set']['gpu_ids'] = args.gpus
    tsm_json_path = os.path.join(task_output_path, 'task_setting.json')
    tsm.save(tsm_json_path)
    pipeline = run_one_task(tsm_json_path, not args.eval)
    return pipeline

def addition_test_setting(args, tsm):
    model_path = args.model_path
    if model_path is not None:
        assert os.path.isfile(model_path), "the model {} not exist".format_map(model_path)
        tsm.task_par['tsk_set']['model_path'] = model_path
    tsm.task_par['tsk_set']['train'] = False
    tsm.task_par['tsk_set']['continue_train'] = False
    tsm.task_par['tsk_set']['smooth_label'] = 0.0
    return tsm


def do_registration(args):
    """

    :param args: the parsed arguments
    :return: None
    """
    task_name = args.task_name
    args.task_name_record = task_name
    __do_registration(args)







if __name__ == '__main__':
    """
        An interface for shape registration approaches.
        Assume there is two level folder, task_root_folder/task_name
        Arguments: 
            --eval: run in inference mode
            --dataset_folder/ -ds: the path including the dataset splits, which contains train/val/test/debug subfolders
            --output_root_folder/ -o: the path of output root folder, we assume the tasks under this folder share the same dataset
            --task_name / -tn: task name i.e. run_training_vsvf_task, run_training_rdmm_task
            --setting_folder_path/ -ts: path of the folder where settings are saved,should include task_setting.json
            --gpu_id/ -g: gpu_id to use
    """
    import argparse

    parser = argparse.ArgumentParser(description="An easy interface for training classification models")
    parser.add_argument('--eval', action='store_true', help='training the task')
    parser.add_argument('-ds', '--dataset_folder', required=False, type=str,
                        default=None, help='the path of dataset splits')
    parser.add_argument('-o', '--output_root_folder', required=False, type=str,
                        default=None,help='the path of output root folder')
    parser.add_argument('-tn', '--task_name', required=False, type=str,
                        default=None,help='the name of the task')
    parser.add_argument('-ts', '--setting_folder_path', required=False, type=str,
                        default=None,help='path of the folder where settings are saved,should include task_setting.json')
    parser.add_argument('-m', "--model_path", required=False, default=None, help='the path of trained model')
    parser.add_argument('-g', '--gpus', default=None, nargs='+', type=int, metavar='N',
                     help='list of gpu ids to use')
    args = parser.parse_args()
    print(args)
    do_registration(args)
