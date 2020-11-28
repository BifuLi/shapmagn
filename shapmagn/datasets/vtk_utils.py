import vtk
from vtk.util import numpy_support as ns



def read_vtk(path):
    reader = vtk.vtkGenericDataObjectReader()
    reader.SetFileName(path)
    reader.Update()
    pointData = reader.GetOutput()
    pointData.GetNumberOfPoints()
    data_dict = {}
    data_dict["points"] = ns.vtk_to_numpy(pointData.GetPoints().GetData())
    # data_dict["lines"] = ns.vtk_to_numpy(pointData.GetLines().GetData())
    assosciatedData = pointData.GetPointData()
    for j in range(assosciatedData.GetNumberOfArrays()):
        attr_name = assosciatedData.GetArrayName(j)
        attr_val = ns.vtk_to_numpy(assosciatedData.GetAbstractArray(j))
        data_dict[attr_name] = attr_val
    return data_dict


def save_vtk(filename, points):
    cell_array = vtk.vtkCellArray()
    points_array = ns.numpy_to_vtk(points, deep=True)

    poly_data = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(points_array)
    poly_data.SetPoints(vtk_points)
    poly_data.SetLines(cell_array)
    poly_data.BuildCells()
    writer = vtk.vtkPolyDataWriter()
    writer.SetFileTypeToBinary()
    writer.SetFileName(filename)
    writer.SetInputData(poly_data)
    writer.Write()


#
# def read_vtk_op(path):
#     import pyvista as pv
#     data = pv.read(path)
#     print(data)


if __name__ == "__main__":
    file_path = "/playpen-raid1/Data/UNC_vesselParticles/10005Q_EXP_STD_NJC_COPD_wholeLungVesselParticles.vtk"
    data_dict = read_vtk(file_path)
    for key, val in data_dict.items():
        print("attri {} with size {}".format(key, val.shape))

    save_vtk("/playpen-raid1/zyshen/debug/saving_vtk_debug.vtk",data_dict["points"]+1)