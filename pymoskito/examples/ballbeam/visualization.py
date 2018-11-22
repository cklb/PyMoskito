# -*- coding: utf-8 -*-
import numpy as np

import pymoskito as pm

import matplotlib as mpl
import matplotlib.patches
import matplotlib.transforms

from . import settings as st

HKS41K100 = '#0b2a51'
HKS44K100 = '#0059a3'
HKS44K80 = '#346FB2'
HKS36K100 = '#512947'
HKS33K100 = '#811a78'
HKS57K100 = '#007a47'
HKS65K100 = '#22ad36'
HKS07K100 = '#e87b14'
HKS07K80 = '#ef9c51'


try:
    import vtk

    class BallBeamVisualizer(pm.VtkVisualizer):

        def __init__(self, renderer):
            pm.VtkVisualizer.__init__(self, renderer)

            # -------- add the beam ----
            # geometry
            self.beam = vtk.vtkCubeSource()
            self.beam.SetXLength(st.visBeamLength)
            self.beam.SetYLength(st.visBeamWidth)
            self.beam.SetZLength(st.visBeamDepth)

            # mapper
            self.beamMapper = vtk.vtkPolyDataMapper()
            self.beamMapper.SetInputConnection(self.beam.GetOutputPort())

            # actor
            self.beamActor = vtk.vtkLODActor()
            self.beamActor.SetMapper(self.beamMapper)

            # make it look nice
            self.beamProp = self.beamActor.GetProperty()
            self.beamProp.SetColor(101 / 255, 123 / 255, 131 / 255)

            self.ren.AddActor(self.beamActor)

            # -------- add the ball ----
            # geometry
            self.ball = vtk.vtkSphereSource()
            self.ball.SetRadius(st.visR)
            self.ball.SetThetaResolution(20)
            self.ball.SetPhiResolution(20)

            # mapper
            self.ballMapper = vtk.vtkPolyDataMapper()
            self.ballMapper.SetInputConnection(self.ball.GetOutputPort())

            # actor
            self.ballActor = vtk.vtkLODActor()
            self.ballActor.SetMapper(self.ballMapper)

            # make it look nice
            self.ballProp = self.ballActor.GetProperty()
            self.ballProp.SetColor(255 / 255, 255 / 255, 0)
            self.ballProp.SetAmbient(0.2)
            self.ballProp.SetDiffuse(0.8)
            self.ballProp.SetSpecular(0.5)
            self.ballProp.SetSpecularPower(0.5)

            self.ren.AddActor(self.ballActor)

            # add background
            self.ren.GradientBackgroundOn()
            self.ren.SetBackground(228 / 255, 232 / 255, 213 / 255)
            self.ren.SetBackground2(38 / 255, 139 / 255, 210 / 255)

            # apply some sane initial state
            self.update_scene(np.array([0, 0, 0, 0]))

            # get everybody into the frame
            self.ren.ResetCamera()
            self.ren.GetActiveCamera().Zoom(1.7)

            # save this view
            self.save_camera_pose()

        @staticmethod
        def calc_positions(x):
            """
            Calculate stationary vectors and rot. matrices for bodies
            """
            # beam
            t_beam = np.array([[np.cos(x[2]), -np.sin(x[2]), 0],
                               [np.sin(x[2]), np.cos(x[2]), 0],
                               [0, 0, 1]])
            r_beam0 = np.array([0, -st.visR - st.visBeamWidth / 2, 0])
            r_beam = np.dot(t_beam, r_beam0)

            # ball
            r_ball0 = np.array([x[0], 0, 0])
            r_ball = np.dot(t_beam, r_ball0)
            phi = x[0] / st.visR
            t_ball = np.array([[np.cos(phi), -np.sin(phi), 0],
                               [np.sin(phi), np.cos(phi), 0],
                               [0, 0, 1]])

            return [r_beam, t_beam, r_ball, t_ball]

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
            r_beam, t_beam, r_ball, t_ball = self.calc_positions(x)
            self.set_body_state(self.beamActor, r_beam, t_beam)
            self.set_body_state(self.ballActor, r_ball, t_ball)

    pm.register_visualizer(BallBeamVisualizer)

except ImportError as e:
    vtk = None
    print("BallBeam Visualizer:")
    print(e)
    print("VTK Visualization not available.")


class MplBallBeamVisualizer(pm.MplVisualizer):

    def __init__(self, q_widget, q_layout):
        pm.MplVisualizer.__init__(self, q_widget, q_layout)
        self.axes.set_xlim(st.x_min_plot, st.x_max_plot)
        self.axes.set_ylim(st.y_min_plot, st.y_max_plot)
        self.axes.set_aspect("equal")

        self.ball_base = mpl.patches.Circle(
            xy=[0, 0],
            radius=st.visR,
            color=HKS44K100,
            zorder=1)
        self.ball_highlight = mpl.patches.Wedge(
            center=[0, 0],
            r=st.visR,
            theta1=0,
            theta2=90,
            color=HKS07K100,
            zorder=2)
        self.beam = mpl.patches.Rectangle(
            xy=[-st.visBeamLength/2, -(st.visR + st.visBeamWidth)],
            width=st.visBeamLength,
            height=st.visBeamWidth,
            color=HKS41K100,
            zorder=0)

        self.axes.add_patch(self.ball_base)
        self.axes.add_patch(self.ball_highlight)
        self.axes.add_patch(self.beam)

    def update_scene(self, x):
        x_ball, dx_ball, theta_beam, dtheta_beam = x
        theta_ball = -x_ball / st.visR

        t_beam = (mpl.transforms.Affine2D().rotate_around(0, 0, theta_beam)
                  + self.axes.transData)
        t_ball = (mpl.transforms.Affine2D().rotate_around(0, 0, theta_ball)
                  + mpl.transforms.Affine2D().translate(x_ball, 0)
                  + t_beam)

        # ball
        self.ball_base.set_transform(t_ball)
        self.ball_highlight.set_transform(t_ball)

        # beam
        self.beam.set_y(-(st.visR + st.visBeamWidth))
        self.beam.set_transform(t_beam)

        self.canvas.draw()


pm.register_visualizer(MplBallBeamVisualizer)
