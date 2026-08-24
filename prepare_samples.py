import os
import wave
import xml.etree.ElementTree as ET
import json
import math

RAW_DIR = "data/ami_raw"
EVAL_DIR = "data/evaluation"

TESTS = [
    {"id": "test_01", "meeting": "EN2001a", "type": "Normal", "start_min": 0, "end_min": 7, "downsample": False},
    {"id": "test_02", "meeting": "EN2002a", "type": "Technical", "start_min": 10, "end_min": 18, "downsample": False},
    {"id": "test_03", "meeting": "EN2002a", "type": "Business", "start_min": 20, "end_min": 28, "downsample": False},
    {"id": "test_04", "meeting": "ES2002a", "type": "Discussion", "start_min": 5, "end_min": 12, "downsample": False},
    {"id": "test_05", "meeting": "ES2002a", "type": "No Assignee", "start_min": 15, "end_min": 22, "downsample": False},
    {"id": "test_06", "meeting": "ES2008a", "type": "No Deadline", "start_min": 10, "end_min": 17, "downsample": False},
    {"id": "test_07", "meeting": "ES2008a", "type": "Noisy", "start_min": 1, "end_min": 8, "downsample": False},
    {"id": "test_08", "meeting": "EN2001a", "type": "Long", "start_min": 10, "end_min": 30, "downsample": True},
]

def slice_audio(input_path, output_path, start_sec, end_sec, downsample=False):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return False
        
    with wave.open(input_path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        
        total_duration = n_frames / framerate
        if start_sec >= total_duration:
            print(f"Start time {start_sec} exceeds audio duration {total_duration}")
            return False
            
        end_sec = min(end_sec, total_duration)
        
        start_frame = int(start_sec * framerate)
        end_frame = int(end_sec * framerate)
        num_frames = end_frame - start_frame
        
        wf.setpos(start_frame)
        audio_data = wf.readframes(num_frames)
        
        out_framerate = framerate // 2 if downsample else framerate
        
        if downsample:
            # simple downsampling by skipping every other frame (assuming 16-bit)
            # each frame is n_channels * sampwidth bytes
            frame_size = n_channels * sampwidth
            downsampled_data = bytearray()
            for i in range(0, len(audio_data), frame_size * 2):
                downsampled_data.extend(audio_data[i:i+frame_size])
            audio_data = bytes(downsampled_data)

    with wave.open(output_path, 'wb') as out_wf:
        out_wf.setnchannels(n_channels)
        out_wf.setsampwidth(sampwidth)
        out_wf.setframerate(out_framerate)
        out_wf.writeframes(audio_data)
        
    return True

def extract_reference_text(meeting, start_sec, end_sec):
    return ""

def main():
    os.makedirs(EVAL_DIR, exist_ok=True)
    
    metadata = []
    
    for t in TESTS:
        print(f"Preparing {t['id']} ...")
        test_dir = os.path.join(EVAL_DIR, t['id'])
        os.makedirs(test_dir, exist_ok=True)
        
        meeting = t['meeting']
        audio_in = os.path.join(RAW_DIR, meeting, 'audio', f"{meeting}.Mix-Headset.wav")
        audio_out = os.path.join(test_dir, "audio.wav")
        ref_out = os.path.join(test_dir, "reference.txt")
        
        start_sec = t['start_min'] * 60
        end_sec = t['end_min'] * 60
        
        if slice_audio(audio_in, audio_out, start_sec, end_sec, downsample=t['downsample']):
            file_size_mb = os.path.getsize(audio_out) / (1024 * 1024)
            print(f"  Generated {audio_out} ({file_size_mb:.2f} MB)")
            
            ref_text = extract_reference_text(meeting, start_sec, end_sec)
            with open(ref_out, "w", encoding="utf-8") as f:
                f.write(ref_text)
                
            metadata.append({
                "test_id": t['id'],
                "meeting": meeting,
                "type": t['type'],
                "duration_sec": end_sec - start_sec,
                "file_size_mb": file_size_mb,
                "audio_path": audio_out,
                "ref_path": ref_out
            })
        else:
            print(f"  Skipped {t['id']}")
            
    with open(os.path.join(EVAL_DIR, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    main()
