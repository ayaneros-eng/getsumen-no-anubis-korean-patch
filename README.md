# 월면의 아누비스 한글패치 — 검수 수정판

슈퍼패미컴(SNES) **월면의 아누비스 / 月面のアヌビス / Getsumen no Anubis**의 기존 한글 v1.10을 검수하고 문장부호 표시를 보정한 패치입니다.

**[배포 ZIP 다운로드](https://github.com/ayaneros-eng/getsumen-no-anubis-korean-patch/releases/latest)** → Assets에서 `Anubis_KR_v1.10_QA2_patch.zip`을 받으세요.

게임 ROM은 제공하지 않습니다. 직접 준비한 지원 ROM에 패치를 적용하세요.

## 적용 방법 (Windows)

1. ZIP을 풀어 주세요.
2. 지원 ROM을 `apply_patch.cmd` 위로 끌어 놓으세요.
3. 입력 ROM 옆에 생성된 `Anubis_KR_refined.sfc`를 실행하세요.

원본은 덮어쓰지 않습니다. 출력 파일이 이미 있거나 입력 해시가 지원 목록과 다르면 중단합니다. 다음 명령으로도 적용할 수 있습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\apply_patch.ps1 -SourceRom "original.sfc" -OutputRom "Anubis_KR_refined.sfc"
```

다른 운영체제에서는 지원 입력에 맞는 IPS를 IPS 적용기로 적용한 뒤 출력 SHA-256을 확인하세요.

## 지원 입력

| 입력 판본 | 크기 | 적용할 IPS |
|---|---:|---|
| 일본어 원본, 헤더 없음 | 3,145,728바이트 | `Anubis_KR_refined_from_JP.ips` |
| 기존 한글 v1.10 검수 입력본 | 4,194,304바이트 | `Anubis_refined_from_v1.10.ips` |
| 이전 문장부호 수정판 | 4,194,304바이트 | `Anubis_refined_from_punctuation_stage3.ips` |

파일 이름만으로 호환 여부를 판단하지 않습니다. 정확한 입력·패치 해시는 [patch_manifest.json](patch_manifest.json)을 확인하세요. Windows 적용기는 해시를 확인해 자동 선택합니다.

일본어 원본 SHA-256:
```
4187f17b8095d510bc207a7ba36aeb011556be6885a42dc48704af3128e5166c
```
완성 ROM SHA-256 (4,194,304바이트):
```
fdd3e6804d640041af4f654b58a3ee1038e2fe4c8a8e6c73bb45374e77a7d5a5
```

## 이번 수정

- 줄 끝에서 마침표만 다음 줄로 내려가는 표시를 보정했습니다. 음절과 마침표를 합친 글리프 27개, 치환 8,941곳을 사용합니다.
- 문장 끝의 중복·단독 마침표 48곳을 정리했습니다.
- 선택지 앞의 `나는。` 14곳을 `나는,`로 수정했습니다.
- 번역 글자, 제어 명령, 텍스트 길이와 분기 주소를 보존하고 ROM 체크섬을 갱신했습니다.

## 확인한 범위

Mesen 에뮬레이터에서 본편 한 경로를 End까지 진행했고, 추가 선택 경로를 스태프롤까지 확인했습니다. 최종 수정본에서 후반부를 다시 진행하고, 게임 내 저장 → 정상 종료 → 새 실행 → 이어하기, 기록 화면 복귀와 START를 누르지 않았을 때의 자동 프롤로그도 확인했습니다.

이는 모든 분기·모든 번역 문장·물리 SNES 기기의 전수 검증을 뜻하지 않습니다. 음성·오디오 검수도 포함하지 않습니다. 자세한 범위는 [QA.md](QA.md)에 있습니다.

일반 게임 저장은 이어하기 검수를 통과했습니다. 에뮬레이터 세이브스테이트는 같은 빌드에서만 사용하세요.

## 수정 재현 (개발자용)

Python 3의 표준 라이브러리만 사용합니다. 기존 한글 v1.10 입력본과 지정 일본어 원본을 각각 준비하세요. 이 빌더는 **이번 문장부호 수정**을 재현하며, 초기 한글 번역의 전체 제작 도구는 아닙니다.

```text
python -X utf8 build_refined.py --base-rom base_v1.10.sfc --japanese-rom original.sfc --output refined.sfc
```

정적 검증기는 패키지 폴더에 완성 ROM을 `월면의_아누비스_한글_v1.10_추가검수수정.sfc` 이름으로 준비한 뒤 사용합니다.

```text
python -X utf8 verify_refined.py --base-rom base_v1.10.sfc --release .
```

`punctuation_build.json`의 `runtime_verified: false`는 빌더가 에뮬레이터를 실행하지 않는다는 뜻입니다. 별도 플레이 검수 범위는 QA 문서를 확인하세요.

## 출처 및 권리

원작과 기존 번역의 권리는 각각의 권리자에게 있습니다. 이 배포판은 기존 한글 v1.10의 검수 수정판이며 신규 전체 번역으로 표기하지 않습니다. 초기 번역 제작자·번역 원본·배포 조건을 확인할 별도 자료는 확보하지 못했습니다. 원작 및 기존 번역에 대한 권리를 주장하거나 별도의 이용 허락을 부여하지 않습니다.

게임 이미지, 개인 저장 파일, 에뮬레이터 상태 파일과 원시 검수 로그는 배포하지 않습니다.
