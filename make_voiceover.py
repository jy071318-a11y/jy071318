"""SRT 자막 타이밍에 맞춰 한국어 TTS 내레이션을 만들고 영상에 합칩니다.

사용법:
  # ElevenLabs (환경변수 ELEVENLABS_API_KEY 필요)
  python make_voiceover.py --engine elevenlabs --voice <voice_id>
  # 무료 대체 (Microsoft Edge 신경망 음성)
  python make_voiceover.py --engine edge --voice ko-KR-SunHiNeural
"""
import argparse, asyncio, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
DL = Path.home() / "Downloads"


def parse_srt(path):
    cues = []
    for block in re.split(r"\r?\n\r?\n", path.read_text(encoding="utf-8-sig").strip()):
        lines = block.splitlines()
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        h, mi, s, ms = map(int, m.groups()[:4])
        start = h * 3600 + mi * 60 + s + ms / 1000
        cues.append((start, " ".join(l.strip() for l in lines[2:])))
    return cues


def duration(path):
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)], capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def tts_elevenlabs(text, out, voice):
    key = os.environ["ELEVENLABS_API_KEY"]
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "language_code": "ko",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
        data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        out.write_bytes(r.read())


def tts_edge(text, out, voice):
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, voice).save(str(out)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["elevenlabs", "edge"], default="elevenlabs")
    ap.add_argument("--voice", default="EXAVITQu4vr4xnSDxMaL")  # ElevenLabs 기본 음성 'Sarah' (무료 플랜 API 사용 가능)
    ap.add_argument("--video", default=str(DL / "KDIS_시연_자막편집_초안.mp4"))
    ap.add_argument("--srt", default=str(DL / "KDIS_시연_자막.srt"))
    ap.add_argument("--out", default="KDIS_시연_음성포함.mp4")
    ap.add_argument("--bgm", help="배경음 mp3 경로 (생략하면 배경음 없음)")
    ap.add_argument("--bgm-volume", type=float, default=0.25, help="배경음 크기 (0.15 아주 작게 / 0.25 적당히 / 0.35 조금 크게)")
    a = ap.parse_args()

    cues = parse_srt(Path(a.srt))
    video_len = duration(a.video)
    clip_dir = Path(f"tts_clips_{a.engine}_{a.voice}"); clip_dir.mkdir(exist_ok=True)
    tts = tts_elevenlabs if a.engine == "elevenlabs" else tts_edge

    inputs, filters = [], []
    for i, (start, text) in enumerate(cues):
        clip = clip_dir / f"{i + 1:02d}.mp3"
        if not clip.exists():
            print(f"[{i + 1}/{len(cues)}] {text}")
            tts(text, clip, a.voice)
        # 다음 자막 시작 전까지 말이 끝나도록, 넘치면 최대 1.3배까지 빠르게
        slot = (cues[i + 1][0] if i + 1 < len(cues) else video_len) - start - 0.15
        speed = min(max(duration(clip) / slot, 1.0), 1.3)
        inputs += ["-i", str(clip)]
        delay = int(start * 1000)
        filters.append(f"[{i + 1}:a]atempo={speed:.3f},adelay={delay}|{delay}[a{i}]")
        if speed > 1.0:
            print(f"  #{i + 1} 길이 초과 -> {speed:.2f}배속")

    mix = "".join(f"[a{i}]" for i in range(len(cues)))
    fc = ";".join(filters) + f";{mix}amix=inputs={len(cues)}:normalize=0"
    if a.bgm:
        # 배경음: 영상 길이만큼 반복, 앞뒤 페이드, 내레이션이 나올 때 자동으로 작아짐(ducking)
        inputs += ["-stream_loop", "-1", "-i", a.bgm]
        fade_out = max(video_len - 4, 0)
        fc += (f",asplit=2[voice][key];"
               f"[{len(cues) + 1}:a]volume={a.bgm_volume},afade=t=in:d=2,afade=t=out:st={fade_out:.2f}:d=4[bgm];"
               f"[bgm][key]sidechaincompress=threshold=0.02:ratio=6:attack=30:release=600[ducked];"
               f"[voice][ducked]amix=inputs=2:normalize=0")
    fc += ",loudnorm=I=-16:TP=-1.5[aout]"
    cmd = [FFMPEG, "-y", "-i", a.video, *inputs, "-filter_complex", fc,
           "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
           "-t", f"{video_len:.3f}", a.out]
    subprocess.run(cmd, check=True)
    print("완료:", Path(a.out).resolve())


if __name__ == "__main__":
    main()
