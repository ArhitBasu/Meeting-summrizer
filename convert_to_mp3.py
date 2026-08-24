import os
import wave
import lameenc

DIRECTORIES = [
    "data/ami_raw",
    "data/evaluation"
]

def convert_to_mp3(file_path):
    mp3_path = file_path.rsplit(".", 1)[0] + ".mp3"
    print(f"Converting {file_path} to {mp3_path}...")
    try:
        with wave.open(file_path, 'rb') as f:
            channels = f.getnchannels()
            sample_rate = f.getframerate()
            sample_width = f.getsampwidth()
            n_frames = f.getnframes()
            pcm_data = f.readframes(n_frames)
            
        if sample_width != 2:
            print(f"Skipping {file_path} because sample width is not 16-bit")
            return
            
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(128)
        encoder.set_in_sample_rate(sample_rate)
        encoder.set_channels(channels)
        encoder.set_quality(2)
        
        mp3_data = encoder.encode(pcm_data)
        mp3_data += encoder.flush()
        
        with open(mp3_path, 'wb') as f:
            f.write(mp3_data)
            
        print(f"Success: {mp3_path}")
        os.remove(file_path)
        print(f"Removed original {file_path}")
    except Exception as e:
        print(f"Failed to convert {file_path}: {e}")

def main():
    for directory in DIRECTORIES:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(".wav"):
                    file_path = os.path.join(root, file)
                    convert_to_mp3(file_path)

if __name__ == "__main__":
    main()
