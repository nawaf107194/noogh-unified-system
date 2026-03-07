import os
import subprocess
import glob
from PIL import Image
try:
    import pytesseract
except ImportError:
    pytesseract = None

def analyze_video_frames(video_path):
    if not pytesseract:
        print("pytesseract not installed.")
        return []
        
    print(f"🎬 Processing video frames for OCR: {video_path}")
    
    # Create temp folder for frames
    frames_dir = "/home/noogh/projects/noogh_unified_system/src/frames_tmp"
    os.makedirs(frames_dir, exist_ok=True)
    
    # Clear old frames
    for f in glob.glob(f"{frames_dir}/*.jpg"):
        os.remove(f)
        
    # Extract 1 frame per 4 seconds using ffmpeg natively (to avoid cv2 installation)
    cmd = [
        "ffmpeg", "-y", "-i", video_path, 
        "-vf", "fps=1/4", 
        f"{frames_dir}/frame_%03d.jpg"
    ]
    
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception as e:
        print(f"❌ ffmpeg failed: {e}")
        return []
        
    frames = sorted(glob.glob(f"{frames_dir}/*.jpg"))
    print(f"🖼️ Extracted {len(frames)} frames. Running OCR Engine...")
    
    extracted_texts = []
    
    for idx, frame_path in enumerate(frames):
        try:
            img = Image.open(frame_path)
            # OCR using English (and Arabic if needed, but the video seems english docs)
            text = pytesseract.image_to_string(img, lang="eng+ara")
            cleaned_text = " ".join(text.split()).strip()
            
            if len(cleaned_text) > 5:  # Ignore empty or tiny noisy reads
                extracted_texts.append(f"--- Frame {idx+1} Text ---\n{cleaned_text}")
        except Exception as e:
            print(f"OCR Error on frame {idx}: {e}")
            
    # Cleanup frames and video
    for f in frames:
        os.remove(f)
    os.rmdir(frames_dir)
    os.remove(video_path)
    
    print("\n✅ Visiual Analysis Complete:")
    print("\n\n".join(extracted_texts))

if __name__ == "__main__":
    analyze_video_frames("/home/noogh/projects/noogh_unified_system/src/tiktok_test.mp4")
