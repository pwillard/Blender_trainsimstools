# SPDX-License-Identifier: MIT
# __init__.py for TrainSimTools Blender Add-on
#
# This file wraps trainsimtools.py so the add-on can be installed
# as a folder (standard Blender add-on format).
#
# Author: Peter Willard (pwillard)
# Version: 1.3.0

bl_info = {
    "name": "TrainSimTools",
    "author": "Peter Willard",
    "version": (1, 3, 1),
    "blender": (3, 0, 0),
    "location": "3D Viewport > N-Panel > TrainSimTools",
    "description": "Utilities for train-sim content: texture filename changer and collection management.",
    "category": "3D View",
}

from importlib import reload
import importlib
import bpy
from . import trainsimtools

# Auto-reload support in Blender's text editor
if "bpy" in locals():
    importlib.reload(trainsimtools)


def register():
    trainsimtools.register()


def unregister():
    trainsimtools.unregister()


if __name__ == "__main__":
    register()
