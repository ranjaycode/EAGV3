"""Convert recorded animated WebP video to standard MP4 video format."""

import sys
import os
import glob
from pathlib import Path
from PIL import Image, ImageSequence
import numpy as np

ARTIFACTS_DIR = Path(r"C:\Users\dell\.gemini\antigravity-ide\brain\ae1bdfc8-2992-4335-a0ea-a3e79b9a5a03")
WORKSPACE = Path(r"c:\Users\dell\Desktop\EAGV3\Session17Assignment")


def main():
    webp_files = list(ARTIFACTS_DIR.glob("*.webp"))
    if not webp_files:
        print("No WebP files found in artifacts directory.")
        sys.exit(1)

    latest_webp = max(webp_files, key=lambda f: f.stat().st_mtime)
    print(f"Reading animated WebP: {latest_webp}")

    img = Image.open(latest_webp)
    frames = []
    durations = []

    for frame in ImageSequence.Iterator(img):
        frames.append(frame.convert("RGB"))
        durations.append(frame.info.get("duration", 100))

    avg_duration = sum(durations) / len(durations) if durations else 100
    fps = max(1, int(round(1000.0 / avg_duration))) if avg_duration > 0 else 10
    print(f"Extracted {len(frames)} frames. Calculated FPS: {fps}")

    # Output MP4 targets
    mp4_artifact = ARTIFACTS_DIR / "demo_video.mp4"
    mp4_workspace = WORKSPACE / "demo_video.mp4"

    try:
        import imageio
        print("Writing MP4 using imageio...")
        writer = imageio.get_writer(str(mp4_artifact), fps=fps)
        for frame in frames:
            writer.append_data(np.array(frame))
        writer.close()

        # Also copy to workspace
        import shutil
        shutil.copyfile(mp4_artifact, mp4_workspace)
        print(f"[SUCCESS] Successfully converted WebP to MP4:\n  * Artifact: {mp4_artifact}\n  * Workspace: {mp4_workspace}")
        return
    except Exception as e:
        print(f"imageio failed ({e}), trying OpenCV...")

    try:
        import cv2
        height, width = frames[0].size[1], frames[0].size[0]
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(mp4_workspace), fourcc, float(fps), (width, height))
        for f in frames:
            cv2_img = cv2.cvtColor(np.array(f), cv2.COLOR_RGB2BGR)
            out.write(cv2_img)
        out.release()
        import shutil
        shutil.copyfile(mp4_workspace, mp4_artifact)
        print(f"✅ Successfully converted WebP to MP4 using OpenCV:\n  • Workspace: {mp4_workspace}")
    except Exception as e:
        print(f"OpenCV failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
