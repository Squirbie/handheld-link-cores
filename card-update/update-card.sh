#!/bin/bash
# Update the prebuilt cores on a KNULLI SD card from a Mac (or a Linux PC).
# 맥(또는 리눅스 PC)에서 KNULLI SD 카드 안의 코어를 새 판으로 바꿔요.
#
#   curl -fsSL https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/card-update/update-card.sh | bash
#   (or double-click update-card-mac.command from card-update.zip)
#
# It looks for <card>/system/hanbang_cores/ on the mounted cards, reads card-updates.txt (from the folder
# this script is in when the files are there, as in an offline package; otherwise from the latest release), and replaces only the files whose md5 is a known older build. A file it does not
# recognise is left alone. The new file is written and checked first; the old one is kept in
# <card>/system/hanbang_cores/backup/.
#
# Test switches (environment): HB_BASE_URL = where the release files are, HB_CARD_ROOTS = card
# folders to look at (separated by ':'), HB_YES=1 = do not ask.
set -u
BASE=${HB_BASE_URL:-https://github.com/Squirbie/handheld-link-cores/releases/latest/download}
YES=${HB_YES:-0}
OS=$(uname -s)

say() { printf '%s\n' "$*"; }
die() { say ""; say "!! $*"; exit 1; }
md5of() { if command -v md5 >/dev/null 2>&1; then md5 -q "$1"; else md5sum "$1" | cut -d' ' -f1; fi; }
sha256of() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi; }
copy() {  # no extended attributes on macOS, so no "._" files end up on the card
  if [ "$OS" = Darwin ]; then cp -X "$1" "$2"; else cp "$1" "$2"; fi
}
ask() {  # yes unless the answer starts with n; no answer possible = no (nothing is changed)
  [ "$YES" = 1 ] && return 0
  printf '%s ' "$1"
  ans=""
  if { read -r ans < /dev/tty; } 2>/dev/null; then :
  elif [ -t 0 ] && read -r ans; then :
  else say ""; say "답을 읽을 수 없어 그만뒀어요(HB_YES=1 로 다시) · cannot read an answer, stopped"; return 1
  fi
  case "$ans" in n|N|no|No|NO|아니*) return 1 ;; esac
  return 0
}

say "== 코어 업데이트 · Core update =="
# files next to this script (an offline package) are used before anything is downloaded
LOCAL=""
SELF=${BASH_SOURCE[0]:-}
if [ -z "${HB_BASE_URL:-}" ] && [ -n "$SELF" ] && [ -f "$SELF" ]; then
  d=$(cd "$(dirname "$SELF")" && pwd)
  [ -f "$d/card-updates.txt" ] && [ -f "$d/SHA256SUMS.txt" ] && LOCAL=$d
fi
fetch() {  # fetch NAME DEST
  if [ -n "$LOCAL" ] && [ -f "$LOCAL/$1" ]; then cp "$LOCAL/$1" "$2"; else curl -fsSL "$BASE/$1" -o "$2"; fi
}
[ -n "$LOCAL" ] && say "이 폴더의 파일을 써요 · Using the files in this folder: $LOCAL"
[ -n "$LOCAL" ] || command -v curl >/dev/null 2>&1 || die "curl 이 없어요 · curl is missing"
command -v unzip >/dev/null 2>&1 || die "unzip 이 없어요 · unzip is missing"

# ---- 1. find the cards
CARDS=()
add_card() { [ -d "$1/system/hanbang_cores" ] && CARDS+=("${1%/}"); }
if [ -n "${HB_CARD_ROOTS:-}" ]; then
  IFS=':' read -r -a _roots <<< "$HB_CARD_ROOTS"
  for d in "${_roots[@]}"; do add_card "$d"; done
elif [ "$OS" = Darwin ]; then
  for d in /Volumes/*/; do add_card "$d"; done
else
  for d in /media/*/*/ /run/media/*/*/ /mnt/*/; do [ -d "$d" ] && add_card "$d"; done
fi
if [ ${#CARDS[@]} -eq 0 ]; then
  die "카드를 못 찾았어요. 게임 카드(system/hanbang_cores 폴더가 있는 카드)를 PC 에 꽂고 다시 해 주세요.
   No card found. Insert the card that has system/hanbang_cores and run this again."
fi

# ---- 2. what the latest release has
TMP=$(mktemp -d "${TMPDIR:-/tmp}/hb-card.XXXXXX") || die "임시 폴더를 못 만들었어요 · cannot make a temp folder"
trap 'rm -rf "$TMP"' EXIT
say "새 판 목록 읽는 중 · Reading the update list..."
fetch card-updates.txt "$TMP/card-updates.txt" || die "목록을 못 받았어요(인터넷 연결을 확인해 주세요) · could not download card-updates.txt"
fetch SHA256SUMS.txt "$TMP/SHA256SUMS.txt" || die "지문 목록을 못 받았어요 · could not download SHA256SUMS.txt"

# ---- 3. compare every card file with the list
PLAN="$TMP/plan.txt"; : > "$PLAN"
for card in "${CARDS[@]}"; do
  say ""
  say "카드 · Card: $card"
  while IFS=$'\t' read -r file olds new zip inzip; do
    case "$file" in ''|'#'*) continue ;; esac
    f="$card/system/hanbang_cores/$file"
    [ -f "$f" ] || continue
    cur=$(md5of "$f")
    if [ "$cur" = "$new" ]; then
      say "  이미 새 판 · already new   $file"
    elif printf ',%s,' "$olds" | grep -q ",$cur,"; then
      say "  바꿈 · will update          $file (${cur:0:8} -> ${new:0:8})"
      printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$card" "$file" "$cur" "$new" "$zip" "$inzip" >> "$PLAN"
    else
      say "  모르는 판이라 그대로 · unknown build, left alone   $file (${cur:0:8})"
    fi
  done < "$TMP/card-updates.txt"
done

if [ ! -s "$PLAN" ]; then
  say ""
  say "바꿀 것이 없어요 · Nothing to update."
  exit 0
fi
say ""
ask "바꿀까요? 그냥 Enter = 예 · n = 아니요 · Update now? Enter = yes, n = no:" || { say "그만뒀어요 · Cancelled."; exit 0; }

# ---- 4. get and check the new files
while IFS=$'\t' read -r card file cur new zip inzip; do
  [ -f "$TMP/new_$file" ] && continue
  if [ ! -f "$TMP/$zip" ]; then
    say "새 코어 준비 중 · Getting $zip ..."
    fetch "$zip" "$TMP/$zip" || die "$zip 을 못 받았어요 · download failed"
    want=$(awk -v z="$zip" '$2 == z {print $1}' "$TMP/SHA256SUMS.txt")
    [ -n "$want" ] && [ "$(sha256of "$TMP/$zip")" = "$want" ] || die "$zip 지문이 안 맞아요 · checksum mismatch"
  fi
  unzip -p "$TMP/$zip" "$inzip" > "$TMP/new_$file" || die "$zip 안에 $inzip 이 없어요 · not in the zip"
  [ "$(md5of "$TMP/new_$file")" = "$new" ] || die "새 $file 의 지문이 목록과 달라요 · md5 does not match the list"
done < "$PLAN"

# ---- 5. replace: write the new file next to the old one, check it, then swap
fail=0
while IFS=$'\t' read -r card file cur new zip inzip; do
  dir="$card/system/hanbang_cores"
  f="$dir/$file"
  if ! copy "$TMP/new_$file" "$f.hbnew" || [ "$(md5of "$f.hbnew")" != "$new" ]; then
    rm -f "$f.hbnew"; say "  !! 카드에 쓰지 못했어요(카드가 잠겼거나 꽉 찼나요?) · could not write $file"; fail=1; continue
  fi
  mkdir -p "$dir/backup"
  bak="$dir/backup/$file"
  if [ -f "$bak" ] && [ "$(md5of "$bak")" != "$cur" ]; then bak="$dir/backup/$file.${cur:0:8}"; fi
  if [ ! -f "$bak" ] && ! mv "$f" "$bak"; then
    rm -f "$f.hbnew"; say "  !! 옛 판을 backup 으로 못 옮겨서 그대로 뒀어요 · could not back up $file, left as it was"; fail=1; continue
  fi
  if mv -f "$f.hbnew" "$f" && [ "$(md5of "$f")" = "$new" ]; then
    if [ "$OS" = Darwin ]; then  # macOS tags new files (com.apple.provenance); on exFAT that becomes a "._" file
      xattr -c "$f" "$bak" "$dir/backup" 2>/dev/null
      rm -f "$dir/._$file" "$dir/._backup" "$dir/backup/._${bak##*/}"
    fi
    say "  바꿨어요 · updated   $file   (옛 판 · old: system/hanbang_cores/backup/)"
  else
    [ -f "$f" ] || copy "$bak" "$f"
    say "  !! 바꾸지 못해서 옛 판을 그대로 뒀어요 · failed, the old file is back"; fail=1
  fi
done < "$PLAN"
sync

say ""
if [ "$fail" = 0 ]; then
  say "끝났어요. 카드를 꺼내서(추출) 기기에 다시 꽂으세요. 같이하기는 두 기기 카드를 모두 바꿔야 돼요."
  say "Done. Eject the card and put it back in the handheld. For netplay, update both devices' cards."
else
  die "일부를 못 바꿨어요. 위 메시지를 봐 주세요 · Some files were not updated (see above)."
fi
