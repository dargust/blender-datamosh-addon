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

import bpy # type: ignore
import os
import subprocess
from bpy.props import StringProperty, BoolProperty # type: ignore
from bpy.types import Operator, Panel # type: ignore
from .parse_raw_avi import convert_to_avi, extract_avi_data, create_datamoshed_avi

class DATAMOSH_OT_run_datamosh(bpy.types.Operator):
    bl_idname = "datamosh.run_datamosh"
    bl_label = "Run Datamosh"
    bl_description = "Run the datamoshing script on the rendered video"

    _timer = None
    _progress = 0.0

    def execute(self, context):
        print(f"Running datamosh script by Dan Argust")
        scene = context.scene

        self.rendered_video = scene.render.frame_path()
        print(f"frame path: {self.rendered_video}")

        if not os.path.exists(self.rendered_video):
            self.report({'ERROR'}, "Rendered video file does not exist.")
            return {'CANCELLED'}
        
        self.input_file = self.rendered_video
        self.temp_file = os.path.splitext(self.input_file)[0] + "_temp.avi"
        self.output_file = os.path.splitext(self.input_file)[0] + "_glitched.avi"

        if self.input_file[:-4] == ".avi":
            self.temp_file = self.input_file

        self.sequence_editor = scene.sequence_editor
        if not self.sequence_editor:
            self.report({'ERROR'}, "No sequence editor found in the current scene.")
            return {'CANCELLED'}

        self.start_frames = [int(x) for x in scene.datamosh_start_frames.split(',')]
        self.start_points = [int(x) for x in scene.datamosh_start_points.split(',')]
        self.end_points = [int(x) for x in scene.datamosh_end_points.split(',')]

        self.steps = [
            self.convert_to_avi_step,
            self.extract_avi_data_step,
            self.create_datamoshed_avi_step,
            self.add_movie_strip_step,
            self.cleanup_temp_files
        ]
        if self.input_file == self.temp_file:
            self.steps = self.steps[1:]

        self.current_step = 0

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'TIMER':
            if self.current_step < len(self.steps):
                self.steps[self.current_step]()
                self.current_step += 1
                self._progress = self.current_step / len(self.steps)
                context.area.tag_redraw()
            else:
                self.report({'INFO'}, "Datamoshing complete")
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
                return {'FINISHED'}
        return {'RUNNING_MODAL'}

    def convert_to_avi_step(self):
        print(f"Converting to AVI: {self.input_file}")
        convert_to_avi(self.input_file, self.temp_file)

    def extract_avi_data_step(self):
        print(f"Extracting AVI data: {self.temp_file}")
        self.avi_data = extract_avi_data(self.temp_file)

    def create_datamoshed_avi_step(self):
        print(f"Creating datamoshed AVI: {self.output_file}")
        create_datamoshed_avi(self.avi_data, self.temp_file, self.output_file, start_at=self.start_points, end_at=self.end_points, duplicated_p_frames=1, transition_frames=self.start_frames)

    def add_movie_strip_step(self):
        print(f"Adding movie strip: {self.output_file}")
        sequences_before = set(self.sequence_editor.sequences_all)
        bpy.ops.sequencer.movie_strip_add(filepath=self.output_file, frame_start=1)
        sequences_after = set(self.sequence_editor.sequences_all)
        new_sequence = (sequences_after - sequences_before).pop()
        if new_sequence.type == 'MOVIE':
            new_sequence.use_proxy = False
            new_sequence.proxy.build_25 = False
            new_sequence.proxy.build_50 = False
            new_sequence.proxy.build_75 = False
            new_sequence.proxy.build_100 = False
            new_sequence.proxy.quality = 50
    
    def cleanup_temp_files(self):
        print(f"Cleaning up temp files: {self.temp_file}")
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        else:
            print("Temp file not found")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Datamoshing in progress...")
        layout.prop(self, "_progress", text="Progress")

class DATAMOSH_OT_get_start_frames(bpy.types.Operator):
    bl_idname = "datamosh.get_start_frames"
    bl_label = "Get Start Frames"
    bl_description = "Get the start frames of all movie sequences in the sequencer"

    def execute(self, context):
        scene = context.scene
        sequence_editor = scene.sequence_editor

        if not sequence_editor:
            self.report({'ERROR'}, "No sequence editor found in the current scene.")
            return {'CANCELLED'}

        start_frames = []
        for sequence in sequence_editor.sequences_all:
            if sequence.type == 'MOVIE':
                frame = int(sequence.frame_final_start) - 1
                if frame > 11:
                    start_frames.append(frame)

        scene.datamosh_start_frames = ','.join(map(str, start_frames))
        scene.datamosh_start_points = ','.join(map(str, [frame - 10 for frame in start_frames]))
        scene.datamosh_end_points = ','.join(map(str, [frame + 60 for frame in start_frames]))
        self.report({'INFO'}, f"Start frames: {start_frames}")
        self.report({'INFO'}, f"Start points: {scene.datamosh_start_points}")
        self.report({'INFO'}, f"End points: {scene.datamosh_end_points}")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DATAMOSH_OT_run_datamosh)
    bpy.utils.register_class(DATAMOSH_OT_get_start_frames)

def unregister():
    bpy.utils.unregister_class(DATAMOSH_OT_run_datamosh)
    bpy.utils.unregister_class(DATAMOSH_OT_get_start_frames)

if __name__ == "__main__":
    register()
