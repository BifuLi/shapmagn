from time import time
from shapmagn.utils.net_utils import get_test_model, update_res
import os
import numpy as np



def eval_model(opt,model,dataloaders,device, task_name=""):
    model_path = opt['tsk_set']['path']['model_load_path']
    since = time()
    record_path = opt['tsk_set']['path']['record_path']
    running_range=opt['tsk_set'][('running_range',[-1],"max running number, set -1 if not limited")]  # todo should be [-1]
    visual_opt = opt['tsk_set'][('visual', {}, "settings for visualziation")]
    save_visual_results = visual_opt[
        ('save_visual_results', False, 'save the visualizatio results during the evaluation')]
    running_part_data = running_range[0]>=0
    if running_part_data:
        print("running part of the test data from range {}".format(running_range))
    phases = ['val','test']
    if len(model_path):
        #todo  check  model loading for data parallel
        get_test_model(model_path, model.network,  model.optimizer)
    else:
        print("Warning, the model is not manual loaded, make sure your model itself has been initialized")

    model.set_cur_epoch(-1)
    for phase in phases:
        num_samples = len(dataloaders[phase])
        if running_part_data:
            num_samples = len(running_range)
        records_score_np = np.zeros(num_samples)
        records_time_np = np.zeros(num_samples)
        runing_detailed_scores = {}
        running_test_score = 0
        time_total= 0
        batch_size_list = []
        for idx, data in enumerate(dataloaders[phase]):
            i= idx
            if running_part_data:
                if i not in running_range:
                    continue
                i = i - running_range[0]

            batch_size = len(data['fname'])
            batch_size_list.append(batch_size)
            is_train = False
            if model.network is not None:
                model.network.train(False)
            model.set_test()
            input_data = model.set_input(data, device, is_train)
            ex_time = time()
            test_res = model.get_evaluation(input_data)
            batch_time = time() - ex_time
            time_total += batch_time
            print("the batch prediction takes {} to complete".format(batch_time))
            records_time_np[i] = batch_time
            score, detailed_scores = model.analyze_res(test_res,cache_res=True)
            update_res(detailed_scores,runing_detailed_scores,mode="append")
            print("the loss_detailed is {}".format(detailed_scores))
            running_test_score += score * batch_size
            records_score_np[i] = score
            sum_batch = sum(batch_size_list)
            print("id {} and current name is : {}".format(i,data['fname']))
            print('the current running_score:{}'.format(score))
            print('the current average running_score:{}'.format(running_test_score/sum_batch))
            print('the current average running detailed score:{}'.format({metric:np.sum(score)/sum_batch for metric, score in runing_detailed_scores.items()}))
            model.save_visual_res(save_visual_results, input_data, test_res, phase)

        test_score = running_test_score / len(dataloaders[phase].dataset)
        time_per_img = time_total / len((dataloaders[phase].dataset))
        print('the average {}_score: {:.4f}'.format(phase, test_score))
        print("the average time for per image is {}".format(time_per_img))
        time_elapsed = time() - since
        print('the size of {} is {}, evaluation complete in {:.0f}m {:.0f}s'.format(len(dataloaders[phase].dataset),phase,
                                                                                           time_elapsed // 60,
                                                                                           time_elapsed % 60))
        np.save(os.path.join(record_path,task_name+'records'),records_score_np)
        model.save_res(phase)
        extract_and_save_interested_loss(runing_detailed_scores,batch_size_list, record_path)
        np.save(os.path.join(record_path,task_name+'records_time'),records_time_np)
    return model


def extract_and_save_interested_loss(detailed_scores,batch_size_list, record_path):
    """" multi_metric_res:{loss:  acc:} ,"""
    assert len(detailed_scores)>0
    sample_num = sum(batch_size_list)
    if isinstance(detailed_scores,dict):
        for metric, score_list in detailed_scores.items():
            records_detail_np = np.zeros([sample_num, 1])
            sample_count = 0
            for i, score in enumerate(score_list):
                batch_len = batch_size_list[i]
                records_detail_np[sample_count:sample_count+batch_len,:] = score
                sample_count += batch_len
            np.save(os.path.join(record_path, metric+ '_records_detail'), records_detail_np)

    else:
        records_detail_np=np.array([-1])
        np.save(os.path.join(record_path, "non" + '_records_detail'), records_detail_np)

