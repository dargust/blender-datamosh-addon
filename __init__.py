#############################################################################
# Datamosh addon for blender                                                #
# Copyright (C) 2025 Dan Argust                                             #
#                                                                           #
#    This program is free software: you can redistribute it and/or modify   #
#    it under the terms of the GNU General Public License as published by   #
#    the Free Software Foundation, either version 3 of the License, or      #
#    (at your option) any later version.                                    #
#                                                                           #
#    This program is distributed in the hope that it will be useful,        #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#    GNU General Public License for more details.                           #
#                                                                           #
#    You should have received a copy of the GNU General Public License      #
#    along with this program.  If not, see <https://www.gnu.org/licenses/>. #
#############################################################################

bl_info = {
    "name": "Datamosh Video",
    "author": "Dan Argust",
    "version": (0, 3, 7),
    "blender": (2, 82, 0),
    "category": "Video Tools",
}

if "bpy" in locals():
    import importlib as imp
    imp.reload(operator)
    imp.reload(panel)
else:
    from . import operator
    from . import panel

import bpy

def register():
    operator.register()
    panel.register()

def unregister():
    operator.unregister()
    panel.unregister()