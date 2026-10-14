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

# ElevenLabs + 배경음 (환경변수 ELEVENLABS_API_KEY 필요, 기본 음성 Sarah)
python make_voiceover.py --engine elevenlabs --bgm "bgm/Local Forecast - Elevator.mp3" --bgm-volume 0.25
```

PowerShell에서는 파일 이름만 입력하면 실행되지 않으니 반드시 `python make_voiceover.py ...` 형태로 실행하세요.

기본 입력은 `~/Downloads/KDIS_시연_자막편집_초안.mp4`, `~/Downloads/KDIS_시연_자막.srt`이며 `--video`, `--srt`, `--out`으로 바꿀 수 있습니다.

- ElevenLabs 무료 플랜은 API로 라이브러리 음성을 쓸 수 없으므로 기본 제공(premade) 음성만 사용하세요.
- 배경음은 영상 길이만큼 반복되고, 내레이션이 나올 때 자동으로 작아지며, 끝에서 페이드아웃됩니다.
- 배경음 mp3는 저장소에 포함하지 않습니다. https://incompetech.com 에서 받아 `bgm/` 폴더에 넣으세요.

## 배경음 출처 (영상 설명란에 표기 필요)

```
Local Forecast - Elevator by Kevin MacLeod (incompetech.com)
Licensed under Creative Commons: By Attribution 4.0 License
http://creativecommons.org/licenses/by/4.0/
```
