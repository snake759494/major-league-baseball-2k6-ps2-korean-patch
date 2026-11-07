# 재빌드 방법

필요한 것: Python 3.10+ (Pillow), .NET 6 SDK 이상(압축 도구 `vcx` 빌드용), xdelta3. 검증용 `tools/emu.py`는 Windows용 PCSX2 v2.x를 씁니다.

## 준비

도구는 저장소를 `work`라는 폴더로 두고, 그 상위 폴더에 원본 ISO와 글꼴이 있다고 가정합니다.

```
<작업 폴더>/
  Major League Baseball 2K6 (USA).iso   해시가 README 표와 일치하는 원본
  Galmuri11.ttf                          갈무리11
  NanumSquareNeo-cBd.ttf                 나눔스퀘어 네오 Bold
  work/                                  이 저장소
    tools/ translation/ ...
```

글꼴 파일은 저장소에 없으므로 따로 받으세요(`docs/FONT_CREDITS.md`).

VC 아카이브 압축 도구를 빌드합니다.

```
dotnet publish work/tools/vcx/vcx.csproj -c Release -o work/tools/bin
```

## 빌드

```
python work/tools/build.py
```

결과는 `Major League Baseball 2K6 (USA) (Korean).iso`입니다. 크기는 원본과 같습니다. 이미 결과 ISO가 있으면 복사를 건너뛰고 덮어씁니다.

xdelta는 다음 옵션으로 만듭니다(압축·2차 압축·경로 헤더 없음).

```
xdelta3 -e -0 -S none -A -s "Major League Baseball 2K6 (USA).iso" "Major League Baseball 2K6 (USA) (Korean).iso" MLB_2K6_PS2_KO_v1.3.xdelta
```

시험용 환경 변수(`build.py`):
- `KO_TARGETS`: 쉼표로 구분한 아카이브 항목 번호만 고칩니다.
- `KO_NOELF`, `KO_NOCODE`, `KO_NOFONT`: 실행파일 문자열 / 코드 패치 / 폰트를 건너뜁니다.
- `KO_EXCL`: 쉼표로 구분한 아카이브 항목 번호를 고치지 않습니다.
- `KO_SAMETEX`: 모든 폰트 텍스처를 원래 크기로 둡니다. `KO_GROW`: 쉼표로 구분한 폰트 이름만 텍스처를 키웁니다(멈춤 원인 폰트를 좁힐 때 사용).
- `KO_LITE`: 라이트판(한글 세트 모두 1비트 저장)으로 빌드합니다.
- `KO_ELFR`: 실행파일 문자열 번역 범위(16진 `시작,끝`)를 제한합니다. 멈춤 원인을 이분 탐색할 때 썼습니다.

## 와이드 패치

빌드한 실행파일(또는 원본 실행파일)에서 pnach를 만듭니다. 파일 이름의 CRC는 실행파일에서 계산합니다.

```
python work/tools/widescreen.py SLUS_212.35 work/patches
```

**새 빌드를 릴리즈할 때는 항상 와이드 패치를 다시 만들어 같은 릴리즈에 첨부합니다.** 실행파일이 바뀌면 한글판 CRC가 바뀌기 때문입니다.

## 번역 수정

`translation/<묶음>__<번호>.json`은 `{영문: 한글}`입니다. 값이 빈 문자열이나 `null`이면 원문을 그대로 둡니다. 지침은 `translation/STYLE.md`입니다.

| 묶음 | 내용 |
| --- | --- |
| `elf` | 실행파일 UTF-16 문자열 |
| `elfa` | 실행파일 ASCII 문자열 |
| `help`, `manual` | 도움말, 게임 내 매뉴얼 |
| `email`, `gm`, `scout` | 프랜차이즈 이메일, 단장 메시지, 스카우트 리포트 |
| `trivia` | 야구 퀴즈 |
| `team` | 팀 이름(약자·도시 제외) |
| `name` | 선수 이름(이름·성 낱말 단위) |
| `namepair` | 한국·일본·대만 선수 전체 이름. 키는 `이름|성`, 결과는 성 칸에 넣고 이름 칸은 비웁니다 |
| `data` | 그 밖의 데이터 문자열 |

- 고정 칸 문자열은 원문 길이를 넘을 수 없습니다. UTF-16 칸은 글자 수, ASCII 칸은 바이트 수(한글 1자 = 2바이트)로 셉니다. 넘친 번역은 빌드 로그에 `[too long]`으로 나오고 원문이 남습니다.
- 한 단어짜리 영문은 게임이 내부 열쇠로 쓸 수 있어 실행파일 ASCII 문자열에서는 바꾸지 않습니다. 도시 이름, 카메라 이름 표, 실행파일의 구장·유니폼 이름 구간도 바꾸지 않습니다(`docs/TECHNICAL.md`).

원문 목록은 `tools/wstrs.py`·`tools/elfcand.py`(실행파일 후보) → `tools/extract.py`로 `src/<묶음>.json`을 만들고, 나눠 번역한 `tr/<묶음>_<번호>.json`을 `tools/merge.py`로 `translation/`에 합칩니다. `merge.py`는 서식 토큰(`%s`, `|CROSS|`, `{0}`)과 길이를 검사합니다.

## 검증

`tools/emu.py`는 PCSX2를 다른 창을 가리지 않게 띄우고, 키 입력·창 캡처·세이브 스테이트 메모리 읽기를 합니다. PCSX2는 `work/emu/`에 휴대용으로 두거나 `PCSX2_DIR` 환경 변수로 지정하세요. 실행 파일 이름은 `pcsx2-mlb2k6.exe`로 바꿔 둡니다(다른 PCSX2와 구분).

`tools/ingame.py <ISO> <태그> [횟수]`는 부팅 후 시범 경기로 들어가 일정 간격으로 화면을 캡처합니다(키: ✕=K, ○=L, □=J, △=I, START=Enter). 경기 설정 화면에서는 ✕와 START를 번갈아 눌러야 경기가 시작됩니다.

폰트나 텍스처를 바꿨다면 경기 조건 화면에서 날씨를 **OVERCAST(흐림)**, 시간을 **DAYTIME(낮)**으로 맞춰 경기 진입을 꼭 시험하세요. GS 메모리를 가장 많이 쓰는 조건이라 v1.0은 여기서 멈췄습니다. 날씨 목록은 오른쪽으로 RAINY → CLEAR → OVERCAST 순서이고, 시간대를 바꾸면 날씨가 다시 정해지므로 시간대를 먼저 고릅니다.
