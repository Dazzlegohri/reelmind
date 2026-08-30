from dataclasses import dataclass

from app.services.video import probe, extract_audio, render_optimized
from app.services.transcribe import transcribe
from app.services.ai import analyze_with_llm, chat


@dataclass
class ReelAgent:

    def analyze(self, video_path: str, work_audio: str):
        meta = probe(video_path)

        transcript = ""

        try:
            extract_audio(video_path, work_audio)
            transcript = transcribe(work_audio)
        except Exception as e:
            print(f"[ReelMind] Transcription unavailable: {e}")

        analysis = analyze_with_llm(
            transcript,
            meta["duration"]
        )

        return meta, transcript, analysis

    def optimize(
        self,
        video_path: str,
        output_path: str,
        duration: float,
        analysis: dict = None
    ):
        if analysis is None:
            analysis = {}

        print("=" * 60)
        print("[ReelMind] OPTIMIZATION AGENT")
        print("=" * 60)

        print(f"Input: {video_path}")
        print(f"Output: {output_path}")
        print(f"Duration: {duration:.2f}s")

        issues = analysis.get("issues", [])

        print(f"Issues detected: {len(issues)}")

        render_optimized(
            video_path,
            output_path,
            duration,
            analysis
        )

        print("[ReelMind] Optimization completed.")
        print("=" * 60)

        return output_path

    def chat(
        self,
        message: str,
        analysis: dict = None
    ):
        if analysis is None:
            analysis = {}

        return chat(
            message,
            analysis
        )