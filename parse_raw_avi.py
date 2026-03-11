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

from enum import Enum
import struct
import subprocess
import os
debug_global = 0

# Convert to AVI (Xvid is best for datamoshing)
def convert_to_avi(input_file, output_file, compression=3):
    cmd = f'ffmpeg -i "{input_file}" -y -c:v libxvid -q:v {compression} -an "{output_file}"'
    subprocess.run(cmd, shell=True)

class FrameType(Enum):
    UncompressedVideoFrame = b'db'
    CompressedVideoFrame = b'dc'
    PaletteChange = b'pc'
    AudioData = b'wb'

    # I-frames
    I = b'\xb0'
    P = b'\xb6'

def collect_riff_data(avi_data):
    riff_start = avi_data.find(b"RIFF")
    riff_size = int.from_bytes(avi_data[riff_start + 4:riff_start + 8], "little")
    riff_data = avi_data[riff_start:riff_start + riff_size + 8]
    fileSize = int.from_bytes(avi_data[4:8], "little")
    fileType = avi_data[8:12].decode("utf-8")
    return {"start": riff_start, "size": riff_size, "data": riff_data, "fileSize": fileSize, "fileType": fileType}

def collect_avih_data(avi_data, hdrl_start):
    avih_start = avi_data.find(b"avih", hdrl_start)
    avih_size = int.from_bytes(avi_data[avih_start + 4:avih_start + 8], "little")
    avih_data = avi_data[avih_start:avih_start + avih_size + 8]
    microsec_per_frame = int.from_bytes(avi_data[avih_start + 8:avih_start + 12], "little")
    max_bytes_per_sec = int.from_bytes(avi_data[avih_start + 12:avih_start + 16], "little")
    padding_granularity = int.from_bytes(avi_data[avih_start + 16:avih_start + 20], "little")
    flags = int.from_bytes(avi_data[avih_start + 20:avih_start + 24], "little")
    total_frames = int.from_bytes(avi_data[avih_start + 24:avih_start + 28], "little")
    initial_frames = int.from_bytes(avi_data[avih_start + 28:avih_start + 32], "little")
    streams = int.from_bytes(avi_data[avih_start + 32:avih_start + 36], "little")
    suggested_buffer_size = int.from_bytes(avi_data[avih_start + 36:avih_start + 40], "little")
    width = int.from_bytes(avi_data[avih_start + 40:avih_start + 44], "little")
    height = int.from_bytes(avi_data[avih_start + 44:avih_start + 48], "little")
    reserved = int.from_bytes(avi_data[avih_start + 48:avih_start + 52], "little")
    return {"start": avih_start, "size": avih_size, "data": avih_data, "microsec_per_frame": microsec_per_frame, "max_bytes_per_sec": max_bytes_per_sec, "padding_granularity": padding_granularity, "flags": flags, "total_frames": total_frames, "initial_frames": initial_frames, "streams": streams, "suggested_buffer_size": suggested_buffer_size, "width": width, "height": height, "reserved": reserved}

def collect_strl_data(avi_data, hdrl_start):
    strl_start = avi_data.find(b"strl", hdrl_start)
    strl_size = int.from_bytes(avi_data[strl_start + 4:strl_start + 8], "little")
    strl_data = avi_data[strl_start:strl_start + strl_size + 8]
    return {"start": strl_start, "size": strl_size, "data": strl_data}

def collect_strh_data(avi_data, hdrl_start):
    strh_start = avi_data.find(b"strh", hdrl_start)
    strh_size = int.from_bytes(avi_data[strh_start + 4:strh_start + 8], "little")
    strh_data = avi_data[strh_start:strh_start + strh_size + 8]
    return {"start": strh_start, "size": strh_size, "data": strh_data}

def collect_strf_data(avi_data, hdrl_start):
    strf_start = avi_data.find(b"strf", hdrl_start)
    strf_size = int.from_bytes(avi_data[strf_start + 4:strf_start + 8], "little")
    strf_data = avi_data[strf_start:strf_start + strf_size + 8]
    return {"start": strf_start, "size": strf_size, "data": strf_data}

def collect_hdrl_data(avi_data):
    hdrl_start = avi_data.find(b"hdrl")
    hdrl_size = int.from_bytes(avi_data[hdrl_start + 4:hdrl_start + 8], "little")
    hdrl_data = avi_data[hdrl_start:hdrl_start + hdrl_size + 8]
    avih_data = collect_avih_data(avi_data, hdrl_start)
    strl_data = collect_strl_data(avi_data, hdrl_start)
    strh_data = collect_strh_data(avi_data, hdrl_start)
    strf_data = collect_strf_data(avi_data, hdrl_start)
    return {"start": hdrl_start, "size": hdrl_size, "data": hdrl_data, "avih": avih_data, "strl": strl_data, "strh": strh_data, "strf": strf_data}

def collect_frame_data(avi_data, movi_start, total_frames):
    #global debug_global
    frame_data = []
    frame_types = []
    current_pos = movi_start + 8  # Skip "movi" + size header
    
    for i in range(total_frames):
        # Find next frame chunk
        frame_start = avi_data.find(b"00dc", current_pos)
        if frame_start == -1:
            print(f"Warning: Could not find frame {i} at position {current_pos}")
            break
            
        frame_size = int.from_bytes(avi_data[frame_start + 4:frame_start + 8], "little")
        frame_end = frame_start + frame_size + 8
        
        # Ensure we don't read beyond the data
        if frame_end > len(avi_data):
            print(f"Warning: Frame {i} extends beyond file boundary")
            break
            
        frame_data.append({
            "start": frame_start, 
            "size": frame_size, 
            "data": avi_data[frame_start:frame_end]
        })
        
        # Work out if the frame is an I frame or a B/P frame
        if frame_start + 11 < len(avi_data):
            frame_type = avi_data[frame_start + 11:frame_start + 12]
        else:
            frame_type = b'\x00'  # Default if we can't read
        frame_types.append(frame_type)
        
        # Move to next frame (include padding if odd size)
        current_pos = frame_end
        if frame_size % 2 == 1:
            current_pos += 1  # Skip padding byte
        
    return {"frame_data": frame_data, "frame_types": frame_types}
    
def collect_movi_data(avi_data, total_frames):
    movi_start = avi_data.find(b"movi")
    movi_size = int.from_bytes(avi_data[movi_start + 4:movi_start + 8], "little")
    movi_data = avi_data[movi_start:movi_start + movi_size + 8]
    frame_data = collect_frame_data(avi_data, movi_start, total_frames)
    return {"start": movi_start, "size": movi_size, "data": movi_data, "frame_data": frame_data}

def collect_idx1_data(avi_data):
    idx1_start = avi_data.find(b"idx1")
    idx1_size = int.from_bytes(avi_data[idx1_start + 4:idx1_start + 8], "little")
    idx1_data = avi_data[idx1_start:idx1_start + idx1_size + 8]
    idx1_entries = []
    entry_size = 16  # Each idx1 entry is 16 bytes long
    idx1_end = 0
    for i in range(0, idx1_size, entry_size):
        entry_start = idx1_start + 8 + i
        chunk_id = avi_data[entry_start:entry_start + 4]
        flags = int.from_bytes(avi_data[entry_start + 4:entry_start + 8], "little")
        offset = int.from_bytes(avi_data[entry_start + 8:entry_start + 12], "little")
        size = int.from_bytes(avi_data[entry_start + 12:entry_start + 16], "little")
        idx1_entries.append({"chunk_id": chunk_id, "flags": flags, "offset": offset, "size": size})
        idx1_end = entry_start + entry_size
    return {"start": idx1_start, "size": idx1_size, "data": idx1_data, "entries": idx1_entries, "end": idx1_end}

def extract_avi_data(input_file):
    with open(input_file, "rb") as f_in:
        avi_data = f_in.read()

        riff_data = collect_riff_data(avi_data)
        print(f"riff start: {riff_data['start']}, size: {riff_data['size']}")
        print(f"    file size: {riff_data['fileSize']}")
        print(f"    file type: {riff_data['fileType']}")

        hdrl_data = collect_hdrl_data(avi_data)
        total_frames = hdrl_data["avih"]["total_frames"]
        print(f"hdrl start: {hdrl_data['start']}, size: {hdrl_data['size']}")
        print(f"    total frames: {total_frames}")
        print(f"    video dimensions: {hdrl_data['avih']['width']}x{hdrl_data['avih']['height']}")

        movi_data = collect_movi_data(avi_data, total_frames)
        print(f"movi start: {movi_data['start']}, size: {movi_data['size']}")
        print("    number of I frames: {}".format(movi_data['frame_data']['frame_types'].count(b'\xb0')))
        print("    number of P frames: {}".format(movi_data['frame_data']['frame_types'].count(b'\xb6')))
        i = 0
        for frame in movi_data['frame_data']['frame_data']:
            if i < 3:
                print(f"        frame start: {frame['start']}, size: {frame['size']}")
            i += 1
        if i > 3:
            print("        ...")

        idx1_data = collect_idx1_data(avi_data)
        print(f"idx1 start: {idx1_data['start']}, size: {idx1_data['size']}")
        i = 0
        for entry in idx1_data['entries']:
            if i < 3:
                print(f"        chunk id: {entry['chunk_id']}, offset: {entry['offset']}, size: {entry['size']}")
            i += 1
        if i > 3:
            print("        ...")

    return {"riff": riff_data, "hdrl": hdrl_data, "movi": movi_data, "idx1": idx1_data}

def create_datamoshed_avi(avi_data, input_filename, output_filename, start_at=[0], end_at=[999999], duplicated_p_frames=0, transition_frames=None):
    print("#### Datamoshing AVI file...")
    print(f"start_at: {start_at}, end_at: {end_at}, transitions: {transition_frames}")
    transition_frames = transition_frames or []

    with open(input_filename, "rb") as f_in:
        raw_data = f_in.read()

    # Validate input data
    if not raw_data.startswith(b"RIFF"):
        raise ValueError("Invalid AVI file: Missing RIFF header")
    
    if b"AVI " not in raw_data[:12]:
        raise ValueError("Invalid AVI file: Not an AVI file")

    riff_start = avi_data["riff"]["start"]
    hdrl_start = avi_data["hdrl"]["start"]
    movi_start = avi_data["movi"]["start"]
    idx1_start = avi_data["idx1"]["start"]
    frame_count = len(avi_data["movi"]["frame_data"]["frame_data"])
    
    if frame_count == 0:
        raise ValueError("No frames found in AVI file")

    new_file = bytearray()
    new_file.extend(raw_data[riff_start:hdrl_start])       # RIFF chunk
    new_file.extend(raw_data[hdrl_start:movi_start])       # HDRL chunk

    # MOVI chunk header
    first_frame_start = avi_data["movi"]["frame_data"]["frame_data"][0]["start"]
    new_file.extend(raw_data[movi_start:first_frame_start])
    
    # Track where movi data starts in the new file (after movi header)
    movi_data_start_in_new_file = len(new_file)

    new_idx1_entries = []
    last_p_frame_binary = None

    def get_offset():
        return len(new_file) - movi_data_start_in_new_file  # Offset from start of movi data

    def add_padding_if_needed():
        # Ensure word alignment (2-byte boundary)
        if len(new_file) % 2 == 1:
            new_file.extend(b'\x00')

    def idx_size_from_chunk(chunk: bytes) -> int:
        # Size reported in the chunk header
        if len(chunk) < 8:
            return 0
        header_size = struct.unpack("<I", chunk[4:8])[0]
        # Actual payload length (exclude 8-byte header, and exclude 1-byte padding if present)
        payload_len = max(0, len(chunk) - 8)
        if payload_len % 2 == 1:
            payload_len -= 1  # drop padding for idx1 size
        # Use the smaller of the declared and actual (defensive)
        return max(0, min(header_size, payload_len))

    def chunk_id_from_chunk(chunk: bytes) -> bytes:
        return chunk[0:4] if len(chunk) >= 4 else b"00dc"

    # Start processing frames
    for i in range(frame_count):
        frame_info = avi_data["movi"]["frame_data"]["frame_data"][i]
        frame_start = frame_info["start"]
        next_start = avi_data["movi"]["frame_data"]["frame_data"][i + 1]["start"] if i + 1 < frame_count else idx1_start
        frame_type = avi_data["movi"]["frame_data"]["frame_types"][i]
        original_frame = raw_data[frame_start:next_start]

        should_glitch = any(start_at[j] <= i <= end_at[j] for j in range(len(start_at)))
        is_transition = i in transition_frames

        if is_transition:
            print(f"Skipping frame {i} for transition.")
            continue

        if frame_type == FrameType.P.value:
            last_p_frame_binary = original_frame

        if should_glitch and frame_type == FrameType.I.value:
            print(f"Replacing I-frame at {i}...")
            if last_p_frame_binary:
                for _ in range(1 + duplicated_p_frames):
                    offset = get_offset()
                    new_file.extend(last_p_frame_binary)
                    add_padding_if_needed()
                    new_idx1_entries.append({
                        "chunk_id": chunk_id_from_chunk(last_p_frame_binary),
                        "flags": 0x00,  # duplicated P => not keyframe
                        "offset": offset,
                        "size": idx_size_from_chunk(last_p_frame_binary)
                    })
            else:
                print(f"  ⚠️ No P-frame available to replace I-frame at {i}, skipping.")
        else:
            offset = get_offset()
            new_file.extend(original_frame)
            add_padding_if_needed()
            new_idx1_entries.append({
                "chunk_id": chunk_id_from_chunk(original_frame),
                "flags": 0x10 if frame_type == FrameType.I.value else 0x00,
                "offset": offset,
                "size": idx_size_from_chunk(original_frame)
            })

    # Calculate and update MOVI chunk size
    movi_data_size = len(new_file) - movi_data_start_in_new_file
    # Make offset relative to start of new_file (which begins at riff_start)
    movi_size_offset = (movi_start - riff_start) + 4
    struct.pack_into('<I', new_file, movi_size_offset, movi_data_size)

    # Add idx1 chunk
    new_file.extend(b"idx1")
    new_file.extend(struct.pack('<I', len(new_idx1_entries) * 16))

    for entry in new_idx1_entries:
        new_file.extend(entry["chunk_id"])
        new_file.extend(struct.pack("<I", entry["flags"]))
        new_file.extend(struct.pack("<I", entry["offset"]))
        # Guard to avoid out-of-range pack
        size_val = entry["size"]
        if size_val < 0:
            size_val = 0
        elif size_val > 0xFFFFFFFF:
            size_val = 0xFFFFFFFF
        new_file.extend(struct.pack("<I", size_val))

    # Fix RIFF header size
    final_file_size = len(new_file)
    riff_size = final_file_size - 8
    struct.pack_into('<I', new_file, 4, riff_size)

    # Fix total frame count in avih
    new_frame_count = len(new_idx1_entries)
    avih_frame_count_offset = avi_data["hdrl"]["avih"]["start"] + 24 - riff_start
    struct.pack_into('<I', new_file, avih_frame_count_offset, new_frame_count)

    print(f"Old frame count: {frame_count}, new frame count: {new_frame_count}")
    print(f"Final file size: {final_file_size} bytes")

    # Basic validation
    if new_frame_count == 0:
        raise ValueError("No frames remaining after datamoshing")
    
    if final_file_size < 1024:  # Very small files are likely corrupted
        raise ValueError("Generated file too small, likely corrupted")

    with open(output_filename, "wb") as f_out:
        f_out.write(new_file)
    print(f"#### Datamosh complete: {output_filename}")
    
    # Verify the output file
    if not os.path.exists(output_filename):
        raise ValueError("Failed to create output file")
    
    output_size = os.path.getsize(output_filename)
    if output_size != final_file_size:
        raise ValueError(f"File size mismatch: expected {final_file_size}, got {output_size}")


if __name__ == "__main__":
    # Example usage
    convert_to_avi("test.mp4", "temp.avi", compression=15)
    input_file = "temp.avi"
    output_file = "output_glitched.avi"
    avi_data = extract_avi_data(input_file)
    create_datamoshed_avi(avi_data, input_file, output_file, start_at=[143,275,545,673], end_at=[243,325,665,723], duplicated_p_frames=0, transition_frames=[153,285,555,683])