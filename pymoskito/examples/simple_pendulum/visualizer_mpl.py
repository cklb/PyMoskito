# -*- coding: utf-8 -*-
import numpy as np
import pymoskito as pm

import matplotlib as mpl
import matplotlib.patches
import matplotlib.transforms


class MplPendulumVisualizer(pm.MplVisualizer):

    # parameters
    x_min_plot = -.85
    x_max_plot = .85
    y_min_plot = -.6
    y_max_plot = .6

    cart_height = .1
    cart_length = .2

    beam_height = .01
    beam_length = 1

    pendulum_shaft_height = 0.027
    pendulum_shaft_radius = 0.020

    pendulum_height = 0.5
    pendulum_radius = 0.005
    # end parameters

    def __init__(self, q_widget, q_layout):
        # setup canvas
        pm.MplVisualizer.__init__(self, q_widget, q_layout)
        self.axes.set_xlim(self.x_min_plot, self.x_max_plot)
        self.axes.set_ylim(self.y_min_plot, self.y_max_plot)
        self.axes.set_aspect("equal")

        # create patches
        self.beam = mpl.patches.Rectangle(xy=[-self.beam_length/2,
                                              -(self.beam_height
                                                + self.cart_height/2)],
                                          width=self.beam_length,
                                          height=self.beam_height,
                                          color="lightgrey")

        self.cart = mpl.patches.Rectangle(xy=[-self.cart_length/2,
                                              -self.cart_height/2],
                                          width=self.cart_length,
                                          height=self.cart_height,
                                          color="dimgrey")

        self.pendulum_shaft = mpl.patches.Circle(
            xy=[0, 0],
            radius=self.pendulum_shaft_radius,
            color="lightgrey",
            zorder=3)

        t = mpl.transforms.Affine2D().rotate_deg(180) + self.axes.transData
        self.pendulum = mpl.patches.Rectangle(
            xy=[-self.pendulum_radius, 0],
            width=2*self.pendulum_radius,
            height=self.pendulum_height,
            color=pm.colors.HKS07K100,
            zorder=2,
            transform=t)

        # add all to canvas
        self.axes.add_patch(self.beam)
        self.axes.add_patch(self.cart)
        self.axes.add_patch(self.pendulum_shaft)
        self.axes.add_patch(self.pendulum)

    # update callback
    def update_scene(self, x):
        cart_pos = x[0]
        phi = np.rad2deg(x[1])

        # cart and shaft
        self.cart.set_x(cart_pos - self.cart_length/2)
        self.pendulum_shaft.center = (cart_pos, 0)

        # pendulum
        ped_trafo = (mpl.transforms.Affine2D().rotate_deg(phi)
                     + mpl.transforms.Affine2D().translate(cart_pos, 0)
                     + self.axes.transData)
        self.pendulum.set_transform(ped_trafo)

        # update canvas
        self.canvas.draw()

