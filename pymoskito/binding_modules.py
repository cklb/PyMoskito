# -*- coding: utf-8 -*-

import logging
import os
import subprocess
from pathlib import Path
import importlib.util

from PyQt5.QtCore import QObject

__all__ = ["CppBase"]

BUILD_DIR = "_build"
LIB_DIR = "_lib"
CMAKE_LISTS = "CMakeLists.txt"


class BindingException(Exception):
    """
    Exception to be raised if the cpp binding raises.
    """
    pass


class CppBase(QObject):
    """
    Mix-in class for modules written in C++.

    This class uses pybind and cmake to automatically compile and link the
    provided sources and load them as an python module.

    Args:
        :module_path: Path to directory that contains the sources.
        :module_name: Name of the cpp class to use
        :binding_class_name: Name of the file including the binding defintion

    Warn:
        The `module_name` will be used to generate the cmake configuration an,
        thus, expects ${module_name}.cpp and ${module_name}.h files.
        *Every other file* is ignored by this routine so far.

    """
    def __init__(self,
                 module_path=None,
                 module_name=None,
                 binding_class_name=None):
        QObject.__init__(self, None)
        self._logger = logging.getLogger(self.__class__.__name__)

        # adapt to os-specific extensions
        if os.name == 'nt':
            self.sfx = '.pyd'
        else:
            self.sfx = '.so'

        if module_name is None:
            self._logger.error("Instantiation of binding class without"
                               " module_name is not allowed!")
            raise BindingException("Instantiation of binding class without"
                                   " module_name is not allowed!")
        self.module_name = module_name

        if module_path is None:
            self._logger.error("Instantiation of binding class without"
                               " module_path is not allowed!")
            raise BindingException("Instantiation of binding class without"
                                   " module_path is not allowed!")
        self.module_path = Path(module_path)
        self.module_stem = self.module_path / self.module_name
        self.module_inc_path = self.module_stem.with_suffix(".h")
        self.module_src_path = self.module_stem.with_suffix(".cpp")
        self.cmake_lists_path = self.module_path / CMAKE_LISTS
        self.module_build_path = self.module_path / BUILD_DIR
        self.module_lib_path = self.module_path / LIB_DIR

        if binding_class_name is None:
            self._logger.error("Instantiation of binding class without"
                               " binding_class_name is not allowed!")
            raise BindingException("Instantiation of binding class without"
                                   " binding_class_name is not allowed!")
        self.binding_class_name = binding_class_name

        if self.create_binding_config():
            self.build_binding()
            # self.install_binding()

    def create_binding_config(self):
        # check if folder exists
        if not self.module_path.is_dir():
            self._logger.error("Module directory '{}' could not be found."
                               "".format(self.module_path))
            return False

        if not self.module_src_path.is_file():
            self._logger.error("CPP binding '{}' could not be found in the "
                               "given module path '{}'."
                               "".format(self.module_src_path,
                                         self.module_path))
            return False

        if not self.module_inc_path.is_file():
            self._logger.error("Header file '{}' could not be found in the "
                               "given module path '{}'."
                               "".format(self.module_inc_path,
                                         self.module_path))
            return False

        if not self.cmake_lists_path.is_file():
            self._logger.warning("CMakeLists.txt not found in module path.")
            self._logger.info("Generating new CMake config.")
            self.create_cmake_lists()

        config_changed = self.update_binding_config()
        if config_changed:
            self.build_config()

        return True

    def create_cmake_lists(self):
        """
        Create the stub of a `CMakeLists.txt` .

        Returns:

        """
        c_make_lists = "cmake_minimum_required(VERSION 3.4)\n"
        c_make_lists += "project(Bindings)\n\n"

        c_make_lists += "set( CMAKE_CXX_STANDARD 11 )\n\n"
        c_make_lists += "find_package(PythonLibs REQUIRED)\n\n"

        c_make_lists += "set( CMAKE_RUNTIME_OUTPUT_DIRECTORY . )\n"
        c_make_lists += "set( CMAKE_LIBRARY_OUTPUT_DIRECTORY . )\n"
        c_make_lists += "set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY . )\n\n"

        c_make_lists += "foreach( OUTPUTCONFIG ${CMAKE_CONFIGURATION_TYPES} )\n"
        c_make_lists += "\tstring( TOUPPER ${OUTPUTCONFIG} OUTPUTCONFIG )\n"
        c_make_lists += "\tset( CMAKE_RUNTIME_OUTPUT_DIRECTORY_${OUTPUTCONFIG} . )\n"
        c_make_lists += "\tset( CMAKE_LIBRARY_OUTPUT_DIRECTORY_${OUTPUTCONFIG} . )\n"
        c_make_lists += "\tset( CMAKE_ARCHIVE_OUTPUT_DIRECTORY_${OUTPUTCONFIG} . )\n"
        c_make_lists += "endforeach( OUTPUTCONFIG CMAKE_CONFIGURATION_TYPES )\n\n"

        c_make_lists += "include_directories(${PYTHON_INCLUDE_DIRS})\n"

        with open(self.cmake_lists_path, "w") as f:
            f.write(c_make_lists)

    def update_binding_config(self):
        """
        Add the module config to the cmake lists.

        Returns:
            bool: True if build config has been changed and cmake has to be
            rerun.
        """
        config_line = "add_library({} SHARED {} {})\n".format(
            self.module_name,
            self.module_src_path.as_posix(),
            self.binding_class_name + '.cpp'
        )
        config_line += "set_target_properties({} PROPERTIES PREFIX \"\" OUTPUT_NAME \"{}\" SUFFIX \"{}\")\n".format(
            self.module_name,
            self.module_name,
            self.sfx
        )
        config_line += "target_link_libraries({} ${{PYTHON_LIBRARIES}})\n".format(
            self.module_name
        )
        config_line += "install(FILES {}/{} DESTINATION {})".format(
            BUILD_DIR,
            self.module_name + self.sfx,
            self.module_lib_path
        )
        with open(self.cmake_lists_path, "r") as f:
            if config_line in f.read():
                return False

        self._logger.info("Appending build info for '{}'".format(self.module_name))
        with open(self.cmake_lists_path, "a") as f:
            f.write("\n")
            f.write(config_line)

        return True

    def build_config(self):
        # generate config
        if os.name == 'nt':
            cmd = ['cmake', '-A', 'x64', '-S .', '-B', BUILD_DIR]
        else:
            cmd = ['cmake', '-DCMAKE_BUILD_TYPE=Debug',
                   '-S', '.', '-B', BUILD_DIR]
        result = subprocess.run(cmd, cwd=self.module_path)

        if result.returncode != 0:
            self._logger.error("Generation of binding config failed.")
            raise BindingException("Generation of binding config failed.")

    def build_binding(self):
        # build
        if os.name == 'nt':
            cmd = ['cmake', '--build', BUILD_DIR, '--config', 'Release']
        else:
            cmd = ['cmake', '--build', BUILD_DIR]
        result = subprocess.run(cmd, cwd=self.module_path)

        if result.returncode != 0:
            self._logger.error("Build failed!")
            raise BindingException("Build failed!")

    def install_binding(self):
        # generate config
        if os.name == 'nt':
            cmd = ['cmake', '--install', BUILD_DIR]
        else:
            cmd = ['cmake', '--install', BUILD_DIR]
        result = subprocess.run(cmd, cwd=self.module_path)

        if result.returncode != 0:
            self._logger.error("Installation of bindings failed.")
            raise BindingException("Installation of bindings failed.")

    def get_class_from_module(self):
        try:
            spec = importlib.util.spec_from_file_location(
                self.module_name,
                (self.module_lib_path / self.module_name).with_suffix(self.sfx))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except ImportError as e:
            self._logger.error("Cannot load module: {}".format(e))
            raise e
