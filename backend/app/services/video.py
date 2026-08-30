import json
import subprocess
from pathlib import Path


def probe(path: str) -> dict:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        data = json.loads(result.stdout)
        fmt = data.get("format", {})

        return {
            "duration": float(fmt.get("duration", 0)),
            "size": int(fmt.get("size", 0)),
        }

    except Exception as e:
        print(f"[ReelMind] ffprobe failed: {e}")

        return {
            "duration": 0,
            "size": 0,
        }


def extract_audio(video_path: str, audio_path: str):
    Path(audio_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        audio_path,
    ]

    subprocess.run(
        cmd,
        capture_output=True,
        check=True,
    )


def _run_ffmpeg(cmd):
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("[ReelMind] FFmpeg ERROR:")
        print(result.stderr[-5000:])

        raise RuntimeError(
            "FFmpeg optimization failed."
        )

    return result


def render_optimized(
    input_path: str,
    output_path: str,
    duration: float,
    analysis=None,
):
    if analysis is None:
        analysis = {}

    issues = analysis.get("issues", [])

    issue_types = {
        str(issue.get("type", "")).lower()
        for issue in issues
        if isinstance(issue, dict)
    }

    hook_issue = "hook" in issue_types
    pacing_issue = "pacing" in issue_types
    cta_issue = "cta" in issue_types

    # ---------------------------------------------------------
    # 1. Decide opening trim
    # ---------------------------------------------------------

    if duration >= 10:
        start = 1.0 if hook_issue else 0.5

    elif duration >= 5:
        start = 0.7 if hook_issue else 0.3

    else:
        start = 0.0

    # Never remove too much from a very short Reel.
    max_start = max(0.0, duration - 2.5)

    start = min(start, max_start)

    output_duration = max(
        0.1,
        duration - start
    )

    # ---------------------------------------------------------
    # 2. Video improvements
    # ---------------------------------------------------------

    filters = [
        # Slight punch-in.
        "scale=1134:2016:force_original_aspect_ratio=increase",

        # Center crop back to vertical 1080x1920.
        "crop=1080:1920",

        # Small visual improvement.
        "eq=contrast=1.05:saturation=1.06:brightness=0.01",

        # Mild sharpening.
        "unsharp=5:5:0.35:5:5:0.0",
    ]

    # ---------------------------------------------------------
    # 3. CTA overlay
    # ---------------------------------------------------------

    if cta_issue:

        font = "C\\:/Windows/Fonts/arialbd.ttf"

        cta_filter = (
            "drawtext="
            f"fontfile='{font}':"
            "text='FOLLOW FOR MORE':"
            "fontcolor=white:"
            "fontsize=72:"
            "borderw=5:"
            "bordercolor=black:"
            "x=(w-text_w)/2:"
            "y=h-260:"
            f"enable='gte(t,{max(0, output_duration - 1.8):.2f})'"
        )

        filters.append(cta_filter)

    # ---------------------------------------------------------
    # 4. Audio
    # ---------------------------------------------------------

    audio_filter = (
        "loudnorm="
        "I=-14:"
        "LRA=11:"
        "TP=-1.5"
    )

    # ---------------------------------------------------------
    # 5. FFmpeg command
    # ---------------------------------------------------------

    cmd = [
        "ffmpeg",
        "-y",

        "-ss",
        f"{start:.2f}",

        "-i",
        input_path,

        "-t",
        f"{output_duration:.2f}",

        "-vf",
        ",".join(filters),

        "-af",
        audio_filter,

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "20",

        "-c:a",
        "aac",

        "-b:a",
        "160k",

        "-movflags",
        "+faststart",

        output_path,
    ]

    print("=" * 60)
    print("[ReelMind] OPTIMIZATION")
    print("=" * 60)

    print(f"Original duration : {duration:.2f}s")
    print(f"Trim from         : {start:.2f}s")
    print(f"Output duration   : {output_duration:.2f}s")

    print(f"Hook issue        : {hook_issue}")
    print(f"Pacing issue      : {pacing_issue}")
    print(f"CTA issue         : {cta_issue}")

    print("Visual enhancement: YES")
    print("Audio enhancement : YES")
    print(
        f"CTA overlay       : {'YES' if cta_issue else 'NO'}"
    )

    print(f"Output            : {output_path}")

    print("=" * 60)

    _run_ffmpeg(cmd)

    # ---------------------------------------------------------
    # 6. Validate output
    # ---------------------------------------------------------

    output = Path(output_path)

    if not output.exists():
        raise RuntimeError(
            "Optimized video was not created."
        )

    if output.stat().st_size < 10000:
        raise RuntimeError(
            "Optimized video appears to be empty."
        )

    print(
        "[ReelMind] Optimized Reel created successfully."
    )

    return output_path