from __future__ import print_function
# coding: utf-8
# Copyright (c) Max-Planck-Institut für Eisenforschung GmbH - Computational Materials Design (CM) Department
# Distributed under the terms of "New BSD License", see the LICENSE file.

import numpy as np
import inspect
from importlib import import_module

"""
Code used by the image library which isn't specific to the task of images, but which doesn't have a home anywhere else
yet.
"""

__author__ = "Liam Huber"
__copyright__ = "Copyright 2019, Max-Planck-Institut für Eisenforschung GmbH " \
                "- Computational Materials Design (CM) Department"
__version__ = "0.0"
__maintainer__ = "Liam Huber"
__email__ = "huber@mpie.de"
__status__ = "development"
__date__ = "Feb 3, 2020"


class ModuleScraper:
    """
    A class which scrapes through a module and applies classes and primitives found as attributes of itself, functions
    found as methods of itself, and sub-modules found recursively as new `ModuleScraper` attributes of itself.

    A decorator can optionally be applied to all functions found.

    Note:
        Doesn't do anything until its `activate` method is called.

    Attributes:
        safe (bool): Whether to skip values beginning with an underscore. (Default is True, do skip.)
        recursive (bool): Whether to recursively activate submodules. (Default is False: submodules are noted by
            creating a new `ModuleScraper` instance and setting it as an attribute, but contents cannot be accessed
            until the submodule itself is explicitly activated.)
        scrape_functions (bool): Whether to look for functions in the module. (Default is True.)
        scrape_classes (bool): Whether to look for class definitions in the module. (Default is True.)
        scrape_primitives (bool): Whether to look for primitives in the module. (Default is True.)
        primitives_list (tuple/list): A list of which types count as primitive. (Default is None, which uses `(int,
            float, bool, numpy.ndarray)`.)
    """

    def __init__(
            self,
            module,
            decorator=None,
            decorator_args=None,
            safe=True,
            recursive=True,
            scrape_functions=True,
            scrape_classes=True,
            scrape_primitives=True,
            primitives_list=None
    ):
        """
        Args:
            module (module/str): The module from which to scrape, or the name of the module from which to escape, e.g.
                `skimage.filters` or `'skimage.filters'`.
            decorator (fnc): A decorator function to apply to scraped functions. (Default is None, no decorator.)
            decorator_args (tuple/list): Arguments to pass to the decorator. (Default is None, no args.)
            safe (bool): Whether to skip values beginning with an underscore. (Default is True, do skip.)
            recursive (bool): Whether to recursively activate submodules. (Default is False: submodules are noted by
                creating a new `ModuleScraper` instance and setting it as an attribute, but contents cannot be accessed
                until the submodule itself is explicitly activated.)
            scrape_functions (bool): Whether to look for functions in the module. (Default is True.)
            scrape_classes (bool): Whether to look for class definitions in the module. (Default is True.)
            scrape_primitives (bool): Whether to look for primitives in the module. (Default is True.)
            primitives_list (tuple/list): A list of which types count as primitive. (Default is None, which uses `(int,
                float, bool, numpy.ndarray)`.)
        """
        self._module = module
        self._decorator = decorator
        self._decorator_args = decorator_args or ()
        self._activated = False
        self.safe = safe
        self.recursive = recursive
        self.scrape_functions = scrape_functions
        self.scrape_classes = scrape_classes
        self.scrape_primitives = scrape_primitives
        self.primitives_list = primitives_list or (int, float, bool, np.ndarray)

    def activate(self):
        """
        Parse the module assigned at instantiation, using decorator information assigned at instantiation.
        """
        if inspect.ismodule(self._module):
            module = self._module
        else:
            module = import_module(self._module)

        for name, obj in inspect.getmembers(module):
            if self.safe and name[0] == '_':
                continue
            elif self.recursive and inspect.ismodule(obj) and obj.__package__ == module.__package__:
                # Behave recursively for submodules
                submodule = ModuleScraper(
                    obj,
                    decorator=self._decorator,
                    decorator_args=self._decorator_args,
                    safe=self.safe,
                    recursive=self.recursive,
                    scrape_functions=self.scrape_functions,
                    scrape_classes=self.scrape_classes,
                    scrape_primitives=self.scrape_primitives,
                    primitives_list=self.primitives_list
                )
                setattr(self, name, submodule)
                if self.recursive:
                    submodule.activate()
            elif self.scrape_functions and inspect.isfunction(obj):
                # Set all module functions as methods
                if self._decorator is not None:
                    fnc = self._decorator(*self._decorator_args)(obj)
                else:
                    fnc = obj
                setattr(self, name, fnc)
            elif self.scrape_classes and inspect.isclass(obj):
                setattr(self, name, obj)
            elif self.scrape_primitives and isinstance(obj, self.primitives_list):
                setattr(self, name, obj)

    def __getattr__(self, item):
        try:
            super(self.__class__, self).__getattribute__(item)
        except AttributeError:
            if inspect.ismodule(self._module):
                name = self._module.__name__.split('.')[-1]
            else:
                name = self._module.split('.')[-1]
            raise AttributeError(
                "'{0}' has no attribute '{1}'. Try running '....{0}.activate()' first.".format(name, item))

    def to_hdf(self):
        pass

    def from_hdf(self):
        pass
