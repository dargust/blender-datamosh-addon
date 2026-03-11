# Blender Datamosh Addon
web usable tool at https://dacus.uk/datamosh/

This Blender addon allows users to perform datamoshing on video clips rendered from Blender's Video Sequence Editor (VSE). It automatically identifies transition points between clips and applies the datamoshing effect to the rendered video.

## Features

- Automatically detects transition points between video clips in the VSE.
- Processes the rendered MP4 video to create a datamoshed version.

## Installation

1. Download or clone the repository.
2. Zip the repository
3. Open Blender and navigate to `Edit > Preferences > Add-ons`.
4. Click on `Install...` and select the zip file.
5. Enable the addon by checking the box next to its name in the Add-ons list.

## Usage

1. Render your video using Blender's Video Sequence Editor as an mp4.
2. Open the Video Sequence Editor and locate the panel for the Datamosh addon.
3. Click the "Get Start Frames" button to let blender auto detect the transitions, or populate them manually.
4. Click the "Run Datamosh" button to start the datamoshing process, this can take some time and stalls/hangs blender while it's running
5. The addon will automatically import the new datamoshed avi file into the video sequence editor, make sure to disable the proxy if you want to preview it

## Standalone Usage

1. Change the input file and frame data in the parse_raw_avi.py file
2. Run the parse_raw_avi.py as a standalone python script

## Dependencies

- Blender 2.8 or higher
- Python 3.7 or higher
