# -*- coding: utf-8 -*-
import numpy as np
import matplotlib as mpl
import matplotlib.patches

import pymoskito as pm

from . import settings as st

try:
    import vtk

    class BallInTubeVisualizer(pm.VtkVisualizer):

        def __init__(self, renderer):
            pm.VtkVisualizer.__init__(self, renderer)

            # -------- add a line ----
            # geometry
            self.line = vtk.vtkLineSource()
            self.line.SetPoint1(0, 0, 0)
            self.line.SetPoint2(0, +st.visTubeLength, 0)

            # mapper
            self.lineMapper = vtk.vtkPolyDataMapper()
            self.lineMapper.SetInputConnection(self.line.GetOutputPort())

            # actor
            self.lineActor = vtk.vtkLODActor()
            self.lineActor.SetMapper(self.lineMapper)

            # make it look nice
            self.lineProp = self.lineActor.GetProperty()
            self.lineProp.SetOpacity(0.0)

            self.ren.AddActor(self.lineActor)

            # -------- add a tube around the line ----
            # geometry
            self.tube = vtk.vtkTubeFilter()
            self.tube.SetNumberOfSides(100)
            self.tube.SetInputConnection(self.line.GetOutputPort())
            self.tube.SetRadius(st.visTubeDiameter/2)

            # mapper
            self.tubeMapper = vtk.vtkPolyDataMapper()
            self.tubeMapper.SetInputConnection(self.tube.GetOutputPort())

            # actor
            self.tubeActor = vtk.vtkLODActor()
            self.tubeActor.SetMapper(self.tubeMapper)

            # make it look nice
            self.tubeProp = self.tubeActor.GetProperty()
            self.tubeProp.SetColor(101/255, 123/255, 131/255)
            self.tubeProp.SetOpacity(0.5)

            self.ren.AddActor(self.tubeActor)

            # -------- add the ball ----
            # geometry
            self.ball = vtk.vtkSphereSource()
            self.ball.SetRadius(st.visBallDiameter/2)
            self.ball.SetThetaResolution(30)
            self.ball.SetPhiResolution(30)
            self.ball.SetCenter(0, st.visBallDiameter/2, 0)

            # mapper
            self.ballMapper = vtk.vtkPolyDataMapper()
            self.ballMapper.SetInputConnection(self.ball.GetOutputPort())

            # actor
            self.ballActor = vtk.vtkLODActor()
            self.ballActor.SetMapper(self.ballMapper)

            # make it look nice
            self.ballProp = self.ballActor.GetProperty()
            self.ballProp.SetColor(255/255, 255/255, 0)
            self.ballProp.SetAmbient(0.2)
            self.ballProp.SetDiffuse(0.8)
            self.ballProp.SetSpecular(0.5)
            self.ballProp.SetSpecularPower(0.5)

            self.ren.AddActor(self.ballActor)

            # -------- add background ----
            self.ren.GradientBackgroundOn()
            self.ren.SetBackground(228/255, 232/255, 213/255)
            self.ren.SetBackground2(38/255, 139/255, 210/255)

            # get everybody into the frame
            self.ren.ResetCamera()
            self.ren.GetActiveCamera().Zoom(1.0)

            # save this view
            self.save_camera_pose()

        @staticmethod
        def calc_positions(x):
            """
            Calculate stationary vectors and rot. matrices for bodies
            """
            # not used, because the fan is not visualized
            # r_fan = np.zeros(3)
            # t_fan = np.zeros((3, 3))

            r_ball = np.array([0, x[2]/st.scale, 0])
            t_ball = np.eye(3)

            return [r_ball, t_ball]

        @staticmethod
        def set_body_state(actor, r, t):
            poke = vtk.vtkMatrix4x4()

            for i in range(3):
                for n in range(3):
                    poke.SetElement(i, n, t[i, n])
                poke.SetElement(i, 3, r[i])

            actor.PokeMatrix(poke)

        def update_scene(self, x):
            """
            update the body states
            """
            r_ball, t_ball = self.calc_positions(x)
            self.set_body_state(self.ballActor, r_ball, t_ball)

    pm.register_visualizer(BallInTubeVisualizer)

except ImportError as e:
    vtk = None
    print("BallTube Visualizer:")
    print(e)
    print("VTK Visualization not available.")


class MplBallInTubeVisualizer(pm.MplVisualizer):

    def __init__(self, q_widget, q_layout):
        pm.MplVisualizer.__init__(self, q_widget, q_layout)

        self.axes.set_xlim(-0.3, 0.3)
        self.axes.set_ylim(-0.05, 1.55)
        self.axes.set_aspect("equal")
        self.axes.get_xaxis().set_visible(False)
#        tube = mpl.patches.Rectangle(xy=[-st.d_R*st.scale/2.0, 0],
#                                     width=st.d_R*st.scale,
#                                     height=st.tube_length,
#                                     fill=False)
#        self.axes.add_patch(tube)
        tube_out = mpl.patches.Rectangle(xy=[-st.d_R_out * st.scale / 2.0, 0],
                                         width=st.d_R_out * st.scale,
                                         height=st.tube_length,
                                         linewidth=1,
                                         fill=False)
        self.axes.add_patch(tube_out)

        self.ball = mpl.patches.Circle(xy=[0, st.d_B*st.scale/2.0],
                                       radius=st.d_B*st.scale/2.0,
                                       color="#0059A3",
                                       linewidth=1)
        self.ball.set_edgecolor("black")
        self.axes.add_patch(self.ball)

    def update_scene(self, x):

        self.ball.center = (0, x[2] + st.d_R*st.scale/2.0)
        self.canvas.draw()


pm.register_visualizer(MplBallInTubeVisualizer)
