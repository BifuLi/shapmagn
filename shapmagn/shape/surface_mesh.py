import torch

from shapmagn.shape.shape_base import ShapeBase

class SurfaceMesh(ShapeBase):
    """
    This class is designed for batch based processing.
    3D Triangular mesh.
    For each batch, we assume nodes are subsampled into the same size

    """

    ####################################################################################################################
    ### Constructor:
    ####################################################################################################################

    # Constructor.
    def __init__(self):

        super(SurfaceMesh,self).__init__()
        self.type = 'surfacemesh'
        self.faces =None
        self.index = None
        self.points_mode_on = False
        """the mesh sampling is not implemented, if the topology changed, only points related operators are allowed"""


    def set_data(self, **args):
        """

        :param points: BxNxD
        :param faces: BxNx2
        :param index: [index_a_list, index_b_list], each is an overbatch index list with B*N length
        :param reindex: generate index over batch for two ends
        :return:
        """
        ShapeBase.set_data(self,**args)
        faces = args["faces"]
        assert faces is not None
        self.faces = faces
        index = args["index"] if "index" in args else None
        reindex = args["reindex"] if "reindex" in args else False
        if index is not None:
            self.index = index
        if self.index is None or reindex:
            index_a_list = []
            index_b_list = []
            index_c_list = []
            for b in range(self.nbatch):
                index_a_list += faces[b,0]+ b*self.npoints
                index_b_list += faces[b,1]+ b*self.npoints
                index_c_list += faces[b,2]+ b*self.npoints
            self.index = [index_a_list, index_b_list, index_c_list]
        self.update_info()


    def set_data_with_refer_to(self, points, mesh):
        self.points = points
        self.faces = mesh.faces
        self.index= mesh.index
        self.label = mesh.label
        self.name_list = mesh.name_list
        self.landmarks = mesh.landmarks
        self.pointfea = mesh.pointfea
        self.weights = mesh.weights
        self.seg = mesh.seg
        self.scale = mesh.scale
        self.points_mode_on = self.scale != -1

        self.update_info()
        return self



    def get_faces(self):
        return self.faces



    def get_centers_and_normals(self):
        """

        :return: centers:BxNxD, normals: BxNxD
        """
        if self.points_mode_on:
            raise NotImplemented("the topology of the shape has changed, only point related operators are allowed")
        a = self.points.view(-1)[self.index[0]]
        b = self.points.view(-1)[self.index[1]]
        c = self.points.view(-1)[self.index[2]]
        centers = (a + b + c) / 3.
        normals = torch.cross(b - a, c - a) / 2  # BxNxdim
        zero_normal_index = torch.nonzero(torch.norm(normals, 2, 2) == 0)
        if zero_normal_index.shape[0]>0:
            normals.data[zero_normal_index] = 1e-7
            print(" {} zero normal is detected, set the zero value to 1e-7".format(len(zero_normal_index)))
        return centers.view([self.nbatch,-1, self.dimension]), normals.view([self.nbatch,-1, self.dimension])