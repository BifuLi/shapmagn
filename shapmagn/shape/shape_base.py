import os.path
import numpy as np
import torch
class ShapeBase(object):
    """
    This class is designed for batch based processing.
    For each batch, we assume the num of nodes  are the same

    """

    ####################################################################################################################
    ### Constructor:
    ####################################################################################################################

    # Constructor.
    def __init__(self):
        """

        :param points: BxNxD
        """
        self.type = 'ShapeBase'
        self.batch = None
        self.dimension = None
        self.points = None
        self.weights = None
        self.npoints = None
        self.label = None
        self.seg = None
        self.name_list = []
        self.compute_bd = False
        self.landmarks = None
        self.pointfea = None
        #self.update_bounding_box()

    def update_info(self):
        points = self.points
        points_shape = points.shape
        self.batch = points_shape[0]
        self.dimension = points.shape[-1]
        self.points = points
        self.npoints = points_shape[1]
        if self.weights is None:
            self.weights = torch.ones(self.batch,self.npoints,1)/self.npoints
        if self.compute_bd:
            self.update_bounding_box()



    def set_data(self, points, weights=None, landmarks=None, pointfea=None, label=None, seg=None, *args):
        """

        :param points: BxNxD
        :param args:
        :return:
        """
        assert len(points.shape) == 3
        self.points = points
        self.weights = weights
        self.landmarks = landmarks
        self.pointfea = pointfea
        self.label = label
        self.seg = seg
        self.update_info()

    def set_weights(self, weights):
        """
        point weight
        :param weights: BxNx1
        :return:
        """
        self.weights = weights

    def set_label(self, label):
        """

        :param label: Bx1
        :return:
        """
        self.label = label

    def set_seg(self, seg):
        """

        :param seg:BxN
        :return:
        """
        self.seg = seg

    def set_landmarks(self, landmarks):
        """
        general landmarks, can be corresponding points or feature
        :param landmarks: B x Numlandmarks x landmarksDim
        :return:
        """
        self.landmarks = landmarks

    def set_pointfea(self, pointfea):
        """
        point feature, has one to one relationship to points
        :param pointfea: B x N x FeaDim
        :return:
        """
        self.pointfea = pointfea



    def set_name_list(self, name_list):
        self.name_list = name_list


    def get_point(self):
        return self.points

    def get_label(self):
        return self.label

    def get_landmarks(self):
        return self.landmarks



    # Compute a tight bounding box that contains all the landmarks data.
    def update_bounding_box(self):
        """

        :return: bounding box: BxNx2
        """
        self.bounding_box = np.zeros((self.batch, self.dimension, 2))
        for b in range(self.batch):
            for d in range(self.dimension):
                self.bounding_box[b, d, 0] = np.min(self.points[b,:, d])
                self.bounding_box[b, d, 1] = np.max(self.points[b,:, d])



    def write(self, output_dir):
        if self.points is not None:
            points = self.points.cpu().numpy().detach()
            for b in range(self.batch):
                with open(os.path.join(output_dir, self.name_list[b]), 'w', encoding='utf-8') as f:
                    f.write(s)
                    for p in points[b]:
                        str_p = [str(elt) for elt in p]
                        if len(p) == 2:
                            str_p.append(str(0.))
                        s = ' '.join(str_p) + '\n'
                        f.write(s)