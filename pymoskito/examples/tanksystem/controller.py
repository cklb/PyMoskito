# -*- coding: utf-8 -*-

import os
from collections import OrderedDict

import numpy as np

import pymoskito as pm


class OpenLoop(pm.Controller):
    """
    manual pwm input
    """
    public_settings = OrderedDict([("uA", 10),
                                   ("tick divider", 1)])

    def __init__(self, settings):
        # add specific "private" settings
        settings.update(input_order=0)
        settings.update(output_dim=1)
        settings.update(input_type="system_state")

        pm.Controller.__init__(self, settings)

    def _control(self, time, trajectory_values=None, feedforward_values=None,
                 input_values=None, **kwargs):

        u = self._settings["uA"]
        return np.array(u)


class CppPIDController(pm.Controller, pm.CppBase):
    """
    PID Controller implemented in cpp with pybind11
    """
    public_settings = OrderedDict([
        ("Kp", 12),
        ("Ti", 12),
        ("Td", 12),
        ("dt [s]", 0.1),
        ("output_limits", [0, 255]),
        ("input_state", [0]),
        ("tick divider", 1),
    ])

    def __init__(self, settings):
        # add specific "private" settings
        settings.update(input_order=0)
        settings.update(output_dim=1)
        settings.update(input_type="system_state")

        proj_dir = os.path.abspath(os.path.dirname(__file__))
        m_path = os.sep.join([proj_dir, "src"])

        pm.Controller.__init__(self, settings)
        pm.CppBase.__init__(self,
                            module_path=m_path,
                            module_name='PIDController',
                            binding_class_name="binding_PIDController")

        self.lastTime = 0
        self.lastU = 0

        self.pid = self.get_class_from_module().PIDController(self._settings["Kp"],
                                                              self._settings["Ti"],
                                                              self._settings["Td"],
                                                              self._settings["output_limits"][0],
                                                              self._settings["output_limits"][1],
                                                              self._settings['dt [s]'])

    def _control(self,
                 time,
                 trajectory_values=None,
                 feedforward_values=None,
                 input_values=None,
                 **kwargs):
        # step size
        dt = time - self.lastTime

        # input abbreviations
        x = np.zeros((len(self._settings["input_state"]),))
        for idx, state in enumerate(self._settings["input_state"]):
            x[idx] = input_values[int(state)]

        if np.isclose(dt, self._settings['dt [s]']):
            # save last control time
            self.lastTime = time

            yd = trajectory_values

            u = self.pid.compute(x, yd)
        else:
            u = self.lastU

        self.lastU = u

        return u


pm.register_simulation_module(pm.Controller, OpenLoop)
pm.register_simulation_module(pm.Controller, CppPIDController)
