#!/bin/bash
# RimMolt writes every screenshot to ~/Library/Application Support/RimWorld/RimMoltScreenshots and never
# cleans it (it has no setting for the folder). This puts that folder on a RAM disk through a symbolic link.
#
#   tools/ramdisk_screenshots.sh install-app   # build "RimMolt 램디스크.app" in ~/Applications (asks in a dialog)
#   tools/ramdisk_screenshots.sh status        # one line per part: the RAM disk, the link
#   tools/ramdisk_screenshots.sh setup         # make the RAM disk if missing, move the old folder aside, link
#   tools/ramdisk_screenshots.sh clear         # delete the PNGs on the RAM disk
#   tools/ramdisk_screenshots.sh teardown      # remove the link (an empty real folder again), eject the RAM disk
#
# A RAM disk is gone after a restart: run setup again (or open the app). Overrides for a test run:
# RAMDISK_NAME, RAMDISK_MB, SHOTS_DIR.
set -euo pipefail

NAME="${RAMDISK_NAME:-RAMDisk}"
SIZE_MB="${RAMDISK_MB:-100}"
VOL="/Volumes/$NAME"
TARGET="$VOL/RimMoltScreenshots"
SHOTS="${SHOTS_DIR:-$HOME/Library/Application Support/RimWorld/RimMoltScreenshots}"
APP="$HOME/Applications/RimMolt 램디스크.app"

mounted() { mount | grep -q " on $VOL ("; }
mb() { du -sm "$1" 2>/dev/null | cut -f1; }

status() {
  if mounted; then
    df -m "$VOL" | awk -v v="$VOL" 'NR == 2 {printf "램디스크: %s, %d MB 중 %d MB 사용\n", v, $2, $3}'
  else
    echo "램디스크: 없음"
  fi
  if [ -L "$SHOTS" ]; then
    if [ "$(readlink "$SHOTS")" = "$TARGET" ]; then
      if mounted; then echo "링크: 램디스크로 연결됨"; else echo "링크: 램디스크로 연결됨 (램디스크가 없어 지금은 끊김)"; fi
    else
      echo "링크: 다른 곳으로 연결됨 ($(readlink "$SHOTS"))"
    fi
  elif [ -d "$SHOTS" ]; then
    echo "링크: 없음 (일반 폴더, 파일 $(find "$SHOTS" -type f | wc -l | tr -d ' ')개, $(mb "$SHOTS") MB)"
  else
    echo "링크: 없음 (폴더 없음)"
  fi
}

ready() { mounted && [ -L "$SHOTS" ] && [ "$(readlink "$SHOTS")" = "$TARGET" ]; }

setup() {
  if ! mounted; then
    dev=$(hdiutil attach -nomount "ram://$((SIZE_MB * 2048))" | awk '{print $1}')
    diskutil erasevolume HFS+ "$NAME" "$dev" >/dev/null
  fi
  mkdir -p "$TARGET"
  moved=""
  if [ -L "$SHOTS" ]; then
    rm "$SHOTS"
  elif [ -d "$SHOTS" ]; then
    moved="$SHOTS.old-$(date +%Y%m%d-%H%M%S)"
    mv "$SHOTS" "$moved"
  fi
  mkdir -p "$(dirname "$SHOTS")"
  ln -s "$TARGET" "$SHOTS"
  echo "설정했어요: 스크린샷은 이제 $TARGET 에 저장돼요."
  [ -n "$moved" ] && echo "기존 스크린샷 폴더는 $(basename "$moved") 로 옮겨 두었어요."
  return 0
}

clear_shots() {
  mounted || { echo "램디스크가 없어요."; return 0; }
  n=$(find "$TARGET" -maxdepth 1 -type f -name '*.png' | wc -l | tr -d ' ')
  find "$TARGET" -maxdepth 1 -type f -name '*.png' -delete
  echo "램디스크의 스크린샷 ${n}개를 지웠어요."
}

teardown() {
  if [ -L "$SHOTS" ]; then rm "$SHOTS"; mkdir -p "$SHOTS"; fi
  if mounted; then diskutil eject "$VOL" >/dev/null; fi
  echo "해제했어요: 스크린샷은 다시 일반 폴더에 저장돼요."
}

install_app() {
  self="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
  src=$(mktemp -t ramdisk_app).applescript
  cat > "$src" <<APPLESCRIPT
set shellCmd to "/bin/bash " & quoted form of "$self"
try
  set statusText to do shell script shellCmd & " status"
  set isReady to (do shell script shellCmd & " ready; echo \$?") is "0"
  if isReady then
    set choice to button returned of (display dialog "RimMolt 스크린샷이 램디스크에 저장되고 있어요." & return & return & statusText buttons {"해제", "비우기", "닫기"} default button "닫기" with title "RimMolt 램디스크")
    if choice is "비우기" then display dialog (do shell script shellCmd & " clear") buttons {"확인"} default button "확인" with title "RimMolt 램디스크"
    if choice is "해제" then display dialog (do shell script shellCmd & " teardown") buttons {"확인"} default button "확인" with title "RimMolt 램디스크"
  else
    set choice to button returned of (display dialog "램디스크(${SIZE_MB}MB)를 만들고 RimMolt 스크린샷 폴더를 거기로 연결할까요?" & return & return & statusText buttons {"취소", "설정"} default button "설정" with title "RimMolt 램디스크")
    if choice is "설정" then display dialog (do shell script shellCmd & " setup") & return & return & (do shell script shellCmd & " status") buttons {"확인"} default button "확인" with title "RimMolt 램디스크"
  end if
on error msg number n
  if n is not -128 then display dialog "문제가 생겼어요: " & msg buttons {"확인"} default button "확인" with icon caution with title "RimMolt 램디스크"
end try
APPLESCRIPT
  mkdir -p "$(dirname "$APP")"
  rm -rf "$APP"
  osacompile -o "$APP" "$src"
  rm -f "$src"
  echo "$APP"
}

case "${1:-status}" in
  status) status ;;
  ready) ready ;;
  setup) setup ;;
  clear) clear_shots ;;
  teardown) teardown ;;
  install-app) install_app ;;
  *) echo "usage: $0 status|setup|clear|teardown|install-app" >&2; exit 2 ;;
esac
