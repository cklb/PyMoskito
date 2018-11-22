from abc import ABCMeta, abstractmethod
from scipy.interpolate import interp1d

from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
from matplotlib.figure import Figure

__all__ = ["VtkVisualizer", "MplVisualizer"]

try:
    import vtk
    from vtk.qt.QVTKRenderWindowInteractor import *

    class QVTKRenderWindowInteractor(QVTKRenderWindowInteractor):
        """
        overload class to patch problem with zooming in vtk window
        the reason is that the QWheelEvent in PyQt5 hasn't the function delta()
        so we have to replace that with angleDelta()
        the error is caused by vtk 7.0.0
        """
        # override function
        def wheelEvent(self, ev):
            if ev.angleDelta().y() >= 0:
                self._Iren.MouseWheelForwardEvent()
            else:
                self._Iren.MouseWheelBackwardEvent()

except ImportError as e:
    QVTKRenderWindowInteractor = None


class Visualizer(metaclass=ABCMeta):
    """
    Base Class for animation
    """

    def __init__(self):
        self._data = None
        self._state_interp = None
        # self._input_interp = None

        self.can_reset_view = False

    @staticmethod
    def _build_interpolator(t_values, data):
        interp = interp1d(t_values,
                          data,
                          axis=0,
                          bounds_error=False,
                          fill_value=(data[0], data[-1]))
        return interp

    def update_simulation_data(self, data):
        """
        Update internal interpolators.

        Overwrite this method and add all attributes that are needed for porper
        visualization.

        Args:
            data(dict): Simulation results.

        """
        self._data = data
        t_values = data["results"]["time"]
        self._state_interp = self._build_interpolator(
            t_values, data["results"]["Solver"])
        # self._input_interp = self._build_interpolator(
        #     t_values, data["results"]["ModelMixer"])

    def update_time_frame(self, t):
        """
        Update the current visualization time.

        This method is called by the GUI if a new time frame has to be
        visualized.

        Args:
            t(float): Current simulation time.

        """
        q = self._state_interp(t)
        # u = self._input_interp(t)

        self.update_scene(q)

    @abstractmethod
    def update_scene(self, x):
        """
        Update the visualization.

        This is a simple version which gets called every time the simulation
        time frame changes. If access to more results is needed, replace
        `update_time_frame`.

        Args:
            x(array): Current model state.

        """
        pass


class VtkVisualizer(Visualizer):
    """
    Base Class with some functionality the help visualizing the system using vtk
    """

    def __init__(self, renderer):
        Visualizer.__init__(self)

        assert isinstance(renderer, vtk.vtkRenderer)
        self.ren = renderer

        self.can_reset_view = False
        self.position = None
        self.focal_point = None
        self.view_up = None
        self.view_angle = None
        self.parallel_projection = None
        self.parallel_scale = None
        self.clipping_range = None

    def reset_camera(self):
        """
        Reset camera to original view.
         
        Will be available if you implement the attributes below and set the
        'can_reset_view' flag.
        """
        if self.can_reset_view:
            camera = self.ren.GetActiveCamera()
            camera.SetPosition(self.position)
            camera.SetFocalPoint(self.focal_point)
            camera.SetViewUp(self.view_up)
            camera.SetViewAngle(self.view_angle)
            camera.SetParallelProjection(self.parallel_projection)
            camera.SetParallelScale(self.parallel_scale)
            camera.SetClippingRange(self.clipping_range)
        else:
            self.ren.ResetCamera()

    def save_camera_pose(self):
            # add camera reset functionality
            camera = self.ren.GetActiveCamera()
            self.position = camera.GetPosition()
            self.focal_point = camera.GetFocalPoint()
            self.view_up = camera.GetViewUp()
            self.view_angle = camera.GetViewAngle()
            self.parallel_projection = camera.GetParallelProjection()
            self.parallel_scale = camera.GetParallelScale()
            self.clipping_range = camera.GetClippingRange()

            self.can_reset_view = True


class MplVisualizer(Visualizer):
    """
    Base Class with some function the help visualizing the system using matplotlib
    """

    def __init__(self, q_widget, q_layout):
        Visualizer.__init__(self)
        self.qWidget = q_widget
        self.qLayout = q_layout
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), facecolor='white', dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.qWidget)
        self.axes = self.fig.add_subplot(111)
        self.qLayout.addWidget(self.canvas)
        self.qWidget.setLayout(self.qLayout)
