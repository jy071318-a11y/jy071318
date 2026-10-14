"""시연 영상에서 핵심 장면만 골라 세로(1080x1920) 쇼츠로 편집합니다.

make_voiceover.py로 만든 ElevenLabs 내레이션 클립을 재사용합니다.
  python make_shorts.py
"""
import argparse, re, subprocess
from pathlib import Path

import imageio_ffmpeg

from make_voiceover import DL, duration, parse_srt

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
TOP = 330                      # 위쪽 제목 영역 높이
CROP_W, CROP_H, CROP_Y = 640, 750, 140   # 원본에서 잘라낼 세로 영역 (브라우저 상단·구운 자막 제외)
VID_H = round(CROP_H * W / CROP_W)       # 1266
GREEN = r"{\c&H5EC522&}"
WHITE = r"{\c&HFFFFFF&}"
VOICE_SPEED = 1.1              # 쇼츠 템포에 맞춰 내레이션을 살짝 빠르게
GAP = 0.15

# (원본 시작초, 잘라낼 x 또는 "fit", 내레이션 자막 번호, 태그, 제목)
SEGMENTS = [
    (124.0, 640, [1], "", f"사진 한 장 올리면\\N{GREEN}쿠팡 상세페이지{WHITE} 완성"),
    (19.5, 250, [4], "STEP 1", "상품 사진 업로드"),
    (25.5, 640, [5], "STEP 2", f"AI가 {GREEN}라벨을 자동으로{WHITE} 읽어요"),
    (43.5, 640, [7, 8], "STEP 3", f"섹션별 {GREEN}초안 자동 완성"),
    (144.2, 640, [19], "STEP 4", f"{GREEN}AI 연출{WHITE} 후기 사진"),
    (200.5, 480, [23], "STEP 5", f"{GREEN}780px JPG{WHITE}로 바로 저장"),
    (205.0, 480, [24], "", f"쿠팡 윙에 올리면 {GREEN}끝"),
    (228.0, "fit", [25], "kdis-editor-app.vercel.app", f"지금 가입하면\\N{GREEN}무료 크레딧 5개"),
]


def ts(t):
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def wrap(text, width=15):
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur] if cur else lines


def caption_events(text, start, dur):
    """긴 문장은 2줄씩 나눠 글자 수 비율로 시간 배분."""
    lines = wrap(text)
    chunks = ["\\N".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
    total = sum(len(c) for c in chunks)
    out, t = [], start
    for c in chunks:
        d = dur * len(c) / total
        out.append((t, t + d, c))
        t += d
    return out


def run(cmd):
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *cmd], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=str(DL / "KDIS_시연_자막편집_초안.mp4"))
    ap.add_argument("--srt", default=str(DL / "KDIS_시연_자막.srt"))
    ap.add_argument("--clips", default="tts_clips_elevenlabs_EXAVITQu4vr4xnSDxMaL")
    ap.add_argument("--bgm", default="bgm/Local Forecast - Elevator.mp3")
    ap.add_argument("--bgm-volume", type=float, default=0.3)
    ap.add_argument("--out", default="KDIS_쇼츠.mp4")
    a = ap.parse_args()

    cues = parse_srt(Path(a.srt))
    work = Path("shorts_work"); work.mkdir(exist_ok=True)

    # 1) 타임라인 계산
    placed, events, seg_files, t = [], [], [], 0.0
    for n, (src, crop, cue_ids, tag, head) in enumerate(SEGMENTS):
        seg_start, cursor = t, t + 0.1
        for cid in cue_ids:
            clip = Path(a.clips) / f"{cid:02d}.mp3"
            d = duration(clip) / VOICE_SPEED
            placed.append((clip, cursor))
            events += [("Cap", s, e, c) for s, e, c in caption_events(cues[cid - 1][1], cursor, d)]
            cursor += d + GAP
        seg_dur = cursor - seg_start + 0.2
        if tag:
            events.append(("Tag", seg_start, seg_start + seg_dur, tag))
        events.append(("Head", seg_start, seg_start + seg_dur, head))

        if crop == "fit":
            vf = f"scale={W}:-2,pad={W}:{H}:0:(oh-ih)/2:color=0x0F0F0F"
        else:
            vf = f"crop={CROP_W}:{CROP_H}:{crop}:{CROP_Y},scale={W}:{VID_H},pad={W}:{H}:0:{TOP}:color=0x0F0F0F"
        f = work / f"seg{n:02d}.mp4"
        run(["-ss", f"{src}", "-t", f"{seg_dur:.3f}", "-i", a.video, "-an",
             "-vf", f"{vf},setsar=1,fps=30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(f)])
        seg_files.append(f)
        t = seg_start + seg_dur
    total = t
    print(f"쇼츠 길이: {total:.1f}초")

    # 2) 자막(ASS)
    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
        "Style: Tag,Malgun Gothic,40,&H005EC522,&H00000000,&H00000000,1,1,0,0,8,40,40,60",
        "Style: Head,Malgun Gothic,74,&H00FFFFFF,&H00000000,&H00000000,1,1,0,0,8,40,40,115",
        "Style: Cap,Malgun Gothic,60,&H00FFFFFF,&H00000000,&H96000000,1,1,6,0,2,40,40,80",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    ass += [f"Dialogue: 0,{ts(s)},{ts(e)},{st},,0,0,0,,{txt}" for st, s, e, txt in events]
    (work / "shorts.ass").write_text("\n".join(ass), encoding="utf-8-sig")

    # 3) 영상 이어붙이기
    (work / "list.txt").write_text("".join(f"file '{f.name}'\n" for f in seg_files), encoding="utf-8")
    run(["-f", "concat", "-safe", "0", "-i", str(work / "list.txt"), "-c", "copy", str(work / "joined.mp4")])

    # 4) 자막 입히기 + 내레이션/배경음 믹스
    inputs, filters = [], []
    for i, (clip, start) in enumerate(placed):
        inputs += ["-i", str(clip)]
        ms = int(start * 1000)
        filters.append(f"[{i + 1}:a]atempo={VOICE_SPEED},adelay={ms}|{ms}[a{i}]")
    b = len(placed) + 1
    inputs += ["-stream_loop", "-1", "-i", a.bgm]
    mix = "".join(f"[a{i}]" for i in range(len(placed)))
    fc = (";".join(filters)
          + f";{mix}amix=inputs={len(placed)}:normalize=0,asplit=2[voice][key]"
          + f";[{b}:a]volume={a.bgm_volume},afade=t=out:st={total - 2:.2f}:d=2[bgm]"
          + ";[bgm][key]sidechaincompress=threshold=0.02:ratio=6:attack=30:release=500[ducked]"
          + ";[voice][ducked]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[aout]"
          + ";[0:v]subtitles=shorts.ass:fontsdir='C\\:/Windows/Fonts'[vout]")
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", "joined.mp4",
                    *[p if not p.endswith(".mp3") else str(Path(p).resolve()) for p in inputs],
                    "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-t", f"{total:.3f}",
                    "-movflags", "+faststart", str(Path(a.out).resolve())],
                   check=True, cwd=work)
    print("완료:", Path(a.out).resolve())


if __name__ == "__main__":
    main()
