# KDIS 시연 영상 내레이션

SRT 자막 타이밍에 맞춰 한국어 TTS 내레이션을 만들고 영상에 합칩니다.

## 준비

```bash
python -m pip install imageio-ffmpeg edge-tts
```

## 실행

```bash
# 무료 음성 (Microsoft Edge 신경망 음성)
python make_voiceover.py --engine edge --voice ko-KR-SunHiNeural

# ElevenLabs (환경변수 ELEVENLABS_API_KEY 필요)
python make_voiceover.py --engine elevenlabs --voice <voice_id>
```

기본 입력은 `~/Downloads/KDIS_시연_자막편집_초안.mp4`, `~/Downloads/KDIS_시연_자막.srt`이며 `--video`, `--srt`, `--out`으로 바꿀 수 있습니다.
