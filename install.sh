#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-or-later
#
# install.sh - install or remove handheld-link-cores packages on KNULLI.
#
# Run it on the device (over SSH) as root:
#   wget -qO- https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/install.sh | sh -s -- gba-mgba-dual
#   sh install.sh --list
#
# It follows the install steps in each package README (cores/<package>/README.md and
# knulli-scripts/README.md) and nothing else:
#   - cores go to /userdata/system/hanbang_cores/ and are symlinked into /usr/lib/libretro/
#   - .info files (new-name cores only) go to /usr/share/libretro/info/
#   - a file that this script would overwrite and did not put there itself is moved to
#     /userdata/system/hanbang_cores/backup/ first, and put back by --uninstall
#   - what was installed is recorded in /userdata/system/hanbang_cores/installed.txt
# It never edits knulli.conf. Running it again, or removing twice, is safe.
#
# POSIX sh (BusyBox ash is fine). No bash-only syntax.

set -eu

REPO="Squirbie/handheld-link-cores"
TAB=$(printf '\t')
HCL=/userdata/system/hanbang_cores          # where cores live (default path baked into the prebuilt files)
REC=$HCL/installed.txt                       # install record
CLAUDE_DIR=/userdata/system/claude           # helper scripts (default path baked into the prebuilt files)
DSP_DIR=/userdata/system/configs/dsperate
DRASTIC_LAUNCH=/userdata/system/configs/advanced_drastic/launch.sh
FORK_BEGIN='# >>> handheld-link-cores: DSperate hand-over (added by install.sh) >>>'
FORK_END='# <<< handheld-link-cores: DSperate hand-over <<<'

ALL_PKGS="ds-melonds-ds ds-dsperate gb-gambatte-link gba-mgba-dual gba-gpsp-rfu wswan-mednafen-dual ngp-mednafen-dual gg-genesisplusgx-dual msx-bluemsx nes-fceumm-mapper14 dos-dosbox-pure-ipx arcade-mame2003-plus arcade-fbneo arcade-mahjong-pad knulli-scripts"

ROOT=""          # --root: prefix for every absolute path (testing)
FROM=""          # --from: use zips from this folder instead of downloading
DRY=0
FORCE=0
MODE=install     # install | uninstall | list
WANT_ALL=0
RELEASE=""
PKGS=""
TMP=""
RW_DONE=0
SYS_TOUCHED=0
SUMS=""
DONE_PKGS=""

say()  { printf '%s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

save_overlay() {
  # KNULLI keeps /usr in an overlay; this makes links and .info files survive a reboot.
  if [ "$SYS_TOUCHED" = 1 ] && [ -z "$ROOT" ] && [ "$DRY" = 0 ]; then
    mount -o remount,rw / 2>/dev/null || true
    if command -v knulli-save-overlay >/dev/null 2>&1; then
      say "Saving the overlay so the changes under /usr survive a reboot ..."
      knulli-save-overlay || warn "knulli-save-overlay failed; run it by hand"
    fi
    SYS_TOUCHED=0
  fi
}

cleanup() {
  cl_rc=$?
  trap - EXIT
  if [ "$cl_rc" -ne 0 ]; then save_overlay; fi     # stopped half way: keep what was done consistent with installed.txt
  if [ -n "$TMP" ] && [ -d "$TMP" ]; then rm -rf "$TMP"; fi
  exit "$cl_rc"
}
trap cleanup EXIT
trap 'exit 130' INT TERM HUP

usage() {
  cat <<'EOF'
Usage:
  sh install.sh                      pick packages from a numbered list (needs a terminal)
  sh install.sh PACKAGE...           install the named packages
  sh install.sh --all                install every package
  sh install.sh --list               show the packages and what is installed
  sh install.sh --uninstall PACKAGE... | --uninstall --all
                                     remove packages and put the original files back

Options:
  --dry-run       show what would happen; change nothing
  --root DIR      put DIR in front of every absolute path (for testing off-device);
                  remount and knulli-save-overlay are skipped
  --from DIR      use the zip files in DIR instead of downloading them
                  (checked against DIR/SHA256SUMS.txt when that file is there)
  --release TAG   download a specific release (for example 2026.10.29) instead of the latest
  --force         skip the "is this KNULLI on aarch64?" check
  -h, --help      this text

Environment: HB_BASE_URL replaces the folder the zip files are downloaded from.

Run "sh install.sh --list" to see the package names. Both devices need the same packages.
The script never edits knulli.conf; each package README says how to choose a core per game.
EOF
}

# ---------------------------------------------------------------- package table
# Sets M_SYS M_DESC M_LIBS M_INFOS M_HINT for a package.
#  M_LIBS items:  <file in zip>=<name in /usr/lib/libretro>   a trailing ! means "replaces the stock core of that name"
pkg_meta() {
  M_SYS=""; M_DESC=""; M_LIBS=""; M_INFOS=""; M_HINT=""
  case "$1" in
    ds-melonds-ds)
      M_SYS="Nintendo DS"; M_DESC="melonDS DS: big ROMs, steady netplay, DraStic-style controls (replaces the stock core)"
      M_LIBS="melondsds_libretro.so=melondsds_libretro.so!"
      M_HINT='nds["<ROM file>"].emulator=libretro and nds["<ROM file>"].core=melondsds, or pick "melonDS DS" in the game'"'"'s settings' ;;
    ds-dsperate)
      M_SYS="Nintendo DS"; M_DESC="DSperate: two-device DS local wireless over Wi-Fi (standalone emulator + launcher glue)"
      M_HINT="edit $DSP_DIR/games.txt (one DS ROM name per line, no extension; the supplied list is only an example); dsperate.ini is not shipped, see the package README (Core options)" ;;
    gb-gambatte-link)
      M_SYS="Game Boy / Color"; M_DESC="link cable and GBC infrared over netplay (replaces the stock gambatte)"
      M_LIBS="gambatte_libretro.so=gambatte_libretro.so!"
      M_HINT="none needed: it replaces gambatte under its own name" ;;
    gba-mgba-dual)
      M_SYS="Game Boy Advance"; M_DESC="two GBAs and a link cable inside one core (new core: mGBA Dual)"
      M_LIBS="mgba_dual_libretro.so=mgba_dual_libretro.so"; M_INFOS="mgba_dual_libretro.info"
      M_HINT='gba["<ROM file>"].core=mgba_dual for link-cable games; add <core name="mgba_dual" features="netplay" /> to es_features_*.cfg to get "start netplay game"' ;;
    gba-gpsp-rfu)
      M_SYS="Game Boy Advance"; M_DESC="a Wireless Adapter that survives Wi-Fi, for Pokemon trades (replaces the stock gpSP)"
      M_LIBS="gpsp_libretro.so=gpsp_libretro.so!"
      M_HINT='gba["<ROM file>"].core=gpsp and gba["<ROM file>"].retroarchcore.gpsp_serial=rfu, only for games that use the Wireless Adapter' ;;
    wswan-mednafen-dual)
      M_SYS="WonderSwan"; M_DESC="link cable for two devices (new core: Beetle WonderSwan Dual)"
      M_LIBS="mednafen_wswan_dual_libretro.so=mednafen_wswan_dual_libretro.so"; M_INFOS="mednafen_wswan_dual_libretro.info"
      M_HINT='wswanc["<ROM file>"].core=mednafen_wswan_dual (wswan[...] for monochrome); add <core name="mednafen_wswan_dual" features="netplay" /> to es_features_*.cfg' ;;
    ngp-mednafen-dual)
      M_SYS="Neo Geo Pocket"; M_DESC="link cable for two devices (new core: Beetle NeoPop Dual)"
      M_LIBS="mednafen_ngp_dual_libretro.so=mednafen_ngp_dual_libretro.so"; M_INFOS="mednafen_ngp_dual_libretro.info"
      M_HINT='ngpc["<ROM file>"].core=mednafen_ngp_dual (ngp[...] for monochrome); add <core name="mednafen_ngp_dual" features="netplay" /> to es_features_*.cfg' ;;
    gg-genesisplusgx-dual)
      M_SYS="Game Gear"; M_DESC="Gear-to-Gear cable for two devices (new core: Genesis Plus GX GG Dual; non-commercial)"
      M_LIBS="genesisplusgx_gg_dual_libretro.so=genesisplusgx_gg_dual_libretro.so"; M_INFOS="genesisplusgx_gg_dual_libretro.info"
      M_HINT='gamegear["<ROM file>"].core=genesisplusgx_gg_dual; add <core name="genesisplusgx_gg_dual" features="netplay" /> to es_features_*.cfg' ;;
    msx-bluemsx)
      M_SYS="MSX"; M_DESC="saves that stick, netplay that stays in sync (replaces the stock blueMSX)"
      M_LIBS="bluemsx_libretro.so=bluemsx_libretro.so!"
      M_HINT="none needed: it replaces blueMSX under its own name" ;;
    nes-fceumm-mapper14)
      M_SYS="NES / Famicom"; M_DESC="work RAM for mapper 14 (replaces the stock FCEUmm)"
      M_LIBS="fceumm_libretro.so=fceumm_libretro.so!"
      M_HINT="none needed: it replaces FCEUmm under its own name" ;;
    dos-dosbox-pure-ipx)
      M_SYS="DOS"; M_DESC="IPX netplay without crashes (replaces the stock DOSBox Pure)"
      M_LIBS="dosbox_pure_hb_ipx_libretro.so=dosbox_pure_libretro.so!"
      M_HINT="none needed: it is linked under the stock name dosbox_pure_libretro.so. A KNULLI update can put the stock core back; run this script again afterwards" ;;
    arcade-mame2003-plus)
      M_SYS="Arcade"; M_DESC="save states that keep netplay in sync (replaces the stock core; non-commercial)"
      M_LIBS="mame2003_plus_libretro.so=mame2003_plus_libretro.so!"
      M_HINT='if it is not the default for arcade: arcade["<ROM file>"].core=mame2003_plus' ;;
    arcade-fbneo)
      M_SYS="Arcade"; M_DESC="leaner netplay states, fixed input table (replaces the stock core; non-commercial)"
      M_LIBS="fbneo_libretro.so=fbneo_libretro.so!"
      M_HINT="none needed; install knulli-scripts too so a netplay guest's EEPROM saves are protected (see the package README)" ;;
    arcade-mahjong-pad)
      M_SYS="Arcade"; M_DESC="mahjong keys on a gamepad (wrapper cores; needs arcade-fbneo and arcade-mame2003-plus; non-commercial)"
      M_LIBS="fbneo_mj_libretro.so=fbneo_mj_libretro.so mame2003_plus_mj_libretro.so=mame2003_plus_mj_libretro.so"
      M_INFOS="fbneo_mj_libretro.info mame2003_plus_mj_libretro.info"
      M_HINT='per mahjong game: arcade["<ROM file>"].core=fbneo_mj (or mame2003_plus_mj) and arcade["<ROM file>"].emulator=libretro; see the package README' ;;
    knulli-scripts)
      M_SYS="KNULLI"; M_DESC="join/solo prompt, per-player saves, DS direct link, services, launcher patch, pixel fonts"
      M_HINT="optional services: add their names (hb_idlesave, hb_wifimem, hb_dsmac, hb_pspadhoc) to system.services in knulli.conf" ;;
    *) return 1 ;;
  esac
}

pkg_zip() {
  if [ "$1" = knulli-scripts ]; then printf '%s' "knulli-scripts.zip"; else printf '%s' "$1-linux-aarch64.zip"; fi
}

valid_pkg() {
  for vp_x in $ALL_PKGS; do
    if [ "$vp_x" = "$1" ]; then return 0; fi
  done
  return 1
}

in_list() { # word list
  for il_x in $2; do
    if [ "$il_x" = "$1" ]; then return 0; fi
  done
  return 1
}

# ---------------------------------------------------------------- install record (installed.txt)
# Tab-separated lines:  KIND  PACKAGE  PATH  [EXTRA]      (paths are the on-device paths, without --root)
#   P  package marker (PATH = zip sha256, EXTRA = date)
#   F  file we placed          L  symlink we made (EXTRA = target)
#   S  symlink over a stock file (EXTRA = target)          B  backup (PATH = original, EXTRA = backup file)
#   C  config file we added and keep if you edited it (EXTRA = sha256 as installed)
#   X  launcher patch applied (PATH = stored copy of the patch)    D  DSperate hand-over lines in launch.sh
rec_file() { printf '%s%s' "$ROOT" "$REC"; }

rec_has() { # kind pkg path
  rh_f=$(rec_file)
  if [ ! -f "$rh_f" ]; then return 1; fi
  awk -F'\t' -v k="$1" -v p="$2" -v q="$3" '$1==k && $2==p && $3==q {f=1} END{exit (f ? 0 : 1)}' "$rh_f"
}

rec_get() { # kind pkg path -> 4th field
  rg_f=$(rec_file)
  if [ ! -f "$rg_f" ]; then return 0; fi
  awk -F'\t' -v k="$1" -v p="$2" -v q="$3" '$1==k && $2==p && $3==q {print $4; exit}' "$rg_f"
}

rec_drop() { # kind pkg path   ("" = any kind / any path)
  if [ "$DRY" = 1 ]; then return 0; fi
  rd_f=$(rec_file)
  if [ ! -f "$rd_f" ]; then return 0; fi
  rd_t="$rd_f.tmp.$$"
  awk -F'\t' -v k="$1" -v p="$2" -v q="$3" '!((k=="" || $1==k) && $2==p && (q=="" || $3==q))' "$rd_f" > "$rd_t"
  mv -f "$rd_t" "$rd_f"
}

rec_add() { # kind pkg path [extra]
  if [ "$DRY" = 1 ]; then return 0; fi
  ra_f=$(rec_file)
  mkdir -p "$(dirname "$ra_f")"
  if [ ! -f "$ra_f" ]; then
    {
      printf '%s\n' "# handheld-link-cores install record, written by install.sh (tab-separated: kind, package, path, extra)."
      printf '%s\n' "# install.sh --uninstall <package> reads this file; do not edit it by hand."
    } > "$ra_f"
  fi
  rec_drop "$1" "$2" "$3"
  if [ -n "${4:-}" ]; then
    printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$ra_f"
  else
    printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$ra_f"
  fi
}

rec_list() { # pkg kind -> lines
  rl_f=$(rec_file)
  if [ ! -f "$rl_f" ]; then return 0; fi
  awk -F'\t' -v p="$1" -v k="$2" '$1==k && $2==p' "$rl_f"
}

is_installed() { # pkg: any record at all
  ii_f=$(rec_file)
  if [ ! -f "$ii_f" ]; then return 1; fi
  awk -F'\t' -v p="$1" '$1 !~ /^#/ && $2==p {f=1} END{exit (f ? 0 : 1)}' "$ii_f"
}

# ---------------------------------------------------------------- small helpers
sha256_of() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 "$1" | awk '{print $NF}'
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    die "need sha256sum or openssl to check downloads"
  fi
}

need_rw() {
  if [ "$RW_DONE" = 0 ]; then
    if [ -z "$ROOT" ] && [ "$DRY" = 0 ]; then
      mount -o remount,rw / 2>/dev/null || warn "could not remount / read-write; continuing"
    fi
    RW_DONE=1
  fi
}

# Call before changing a path: anything outside /userdata is KNULLI's overlay and needs the rw remount + overlay save.
touch_path() {
  case "$1" in
    /userdata/*) ;;
    *) SYS_TOUCHED=1; need_rw ;;
  esac
}

fetch() { # url dest
  if command -v curl >/dev/null 2>&1; then
    if [ -t 2 ]; then
      curl -fL --retry 2 -# -o "$2" "$1" || return 1
    else
      curl -fL --retry 2 -sS -o "$2" "$1" || return 1
    fi
  elif command -v wget >/dev/null 2>&1; then
    if [ -t 2 ]; then
      wget -O "$2" "$1" || return 1
    else
      wget -q -O "$2" "$1" || return 1
    fi
  else
    die "need curl or wget to download (or use --from DIR with the zip files)"
  fi
}

base_url() {
  if [ -n "${HB_BASE_URL:-}" ]; then
    printf '%s' "$HB_BASE_URL"
  elif [ -n "$RELEASE" ]; then
    printf '%s' "https://github.com/$REPO/releases/download/$RELEASE"
  else
    printf '%s' "https://github.com/$REPO/releases/latest/download"
  fi
}

extract_zip() { # zip destdir
  mkdir -p "$2"
  if command -v unzip >/dev/null 2>&1; then
    unzip -oq "$1" -d "$2"
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import sys, zipfile; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])' "$1" "$2"
  else
    die "need unzip or python3 to open the zip files"
  fi
}

# ---------------------------------------------------------------- file placement (with backups)
backup_path() { # path pkg : move whatever is there into hanbang_cores/backup/
  bp_path=$1; bp_pkg=$2
  bp_dir=$HCL/backup
  mkdir -p "$ROOT$bp_dir"
  bp_base=$(basename "$bp_path")
  bp_dest=$bp_dir/$bp_base
  bp_i=0
  while [ -e "$ROOT$bp_dest" ] || [ -L "$ROOT$bp_dest" ]; do
    bp_i=$((bp_i + 1))
    bp_dest=$bp_dir/$bp_base.$bp_i
  done
  mv "$ROOT$bp_path" "$ROOT$bp_dest"
  rec_add B "$bp_pkg" "$bp_path" "$bp_dest"
  say "  backed up      $bp_path -> $bp_dest"
}

place_file() { # src dest mode pkg
  pf_src=$1; pf_dest=$2; pf_mode=$3; pf_pkg=$4
  pf_real=$ROOT$pf_dest
  pf_exists=0
  if [ -e "$pf_real" ] || [ -L "$pf_real" ]; then pf_exists=1; fi
  if [ "$DRY" = 1 ]; then
    if [ "$pf_exists" = 0 ]; then
      say "  would add      $pf_dest"
    elif rec_has F "$pf_pkg" "$pf_dest"; then
      say "  would update   $pf_dest"
    else
      say "  would replace  $pf_dest (the current file is moved to $HCL/backup/ first, unless it is identical)"
    fi
    return 0
  fi
  [ -f "$pf_src" ] || die "the package is missing $(basename "$pf_src")"
  touch_path "$pf_dest"
  mkdir -p "$(dirname "$pf_real")"
  if [ "$pf_exists" = 1 ]; then
    if [ -f "$pf_real" ] && [ ! -L "$pf_real" ] && cmp -s "$pf_src" "$pf_real"; then
      chmod "$pf_mode" "$pf_real"
      rec_add F "$pf_pkg" "$pf_dest"
      say "  up to date     $pf_dest"
      return 0
    fi
    if ! rec_has F "$pf_pkg" "$pf_dest"; then backup_path "$pf_dest" "$pf_pkg"; fi
  fi
  pf_new=$pf_real.hbnew
  if ! cp "$pf_src" "$pf_new"; then rm -f "$pf_new"; die "cannot write $pf_dest (disk full?)"; fi
  if ! cmp -s "$pf_src" "$pf_new"; then rm -f "$pf_new"; die "the copy of $pf_dest does not match the download"; fi
  chmod "$pf_mode" "$pf_new"
  mv -f "$pf_new" "$pf_real"
  rec_add F "$pf_pkg" "$pf_dest"
  say "  installed      $pf_dest"
}

# Config files you are expected to edit: added if missing, never overwritten unless still exactly as we installed them.
place_config() { # src dest mode pkg
  pc_src=$1; pc_dest=$2; pc_mode=$3; pc_pkg=$4
  pc_real=$ROOT$pc_dest
  if [ "$DRY" = 1 ]; then
    if [ -e "$pc_real" ]; then say "  would keep     $pc_dest (already there; replaced only if you never changed it)"; else say "  would add      $pc_dest"; fi
    return 0
  fi
  [ -f "$pc_src" ] || die "the package is missing $(basename "$pc_src")"
  touch_path "$pc_dest"
  mkdir -p "$(dirname "$pc_real")"
  if [ -e "$pc_real" ]; then
    if cmp -s "$pc_src" "$pc_real"; then
      rec_add C "$pc_pkg" "$pc_dest" "$(sha256_of "$pc_real")"
      say "  up to date     $pc_dest"
      return 0
    fi
    pc_was=$(rec_get C "$pc_pkg" "$pc_dest")
    if [ -z "$pc_was" ] || [ "$pc_was" != "$(sha256_of "$pc_real")" ]; then
      say "  kept           $pc_dest (your own version)"
      return 0
    fi
  fi
  cp "$pc_src" "$pc_real.hbnew"
  chmod "$pc_mode" "$pc_real.hbnew"
  mv -f "$pc_real.hbnew" "$pc_real"
  rec_add C "$pc_pkg" "$pc_dest" "$(sha256_of "$pc_real")"
  say "  installed      $pc_dest"
}

place_link() { # target link pkg stock(0|1)
  pl_t=$1; pl_l=$2; pl_pkg=$3; pl_stock=${4:-0}
  pl_real=$ROOT$pl_l
  pl_owned=""
  if rec_has S "$pl_pkg" "$pl_l"; then pl_owned=S; elif rec_has L "$pl_pkg" "$pl_l"; then pl_owned=L; fi
  if [ "$DRY" = 1 ]; then
    if [ -e "$pl_real" ] || [ -L "$pl_real" ]; then
      if [ -L "$pl_real" ] && [ "$(readlink "$pl_real")" = "$pl_t" ]; then
        say "  link is there  $pl_l"
      else
        say "  would link     $pl_l -> $pl_t (the current file is moved to $HCL/backup/ first)"
      fi
    else
      say "  would link     $pl_l -> $pl_t"
    fi
    return 0
  fi
  touch_path "$pl_l"
  mkdir -p "$(dirname "$pl_real")"
  if [ -L "$pl_real" ] && [ "$(readlink "$pl_real")" = "$pl_t" ]; then
    pl_kind=L
    if [ -n "$pl_owned" ]; then pl_kind=$pl_owned; elif [ "$pl_stock" = 1 ]; then pl_kind=S; fi
    rec_drop L "$pl_pkg" "$pl_l"; rec_drop S "$pl_pkg" "$pl_l"
    rec_add "$pl_kind" "$pl_pkg" "$pl_l" "$pl_t"
    say "  link is there  $pl_l"
    return 0
  fi
  pl_kind=${pl_owned:-L}
  if [ -e "$pl_real" ] || [ -L "$pl_real" ]; then
    if [ -L "$pl_real" ] && [ -n "$pl_owned" ]; then
      rm -f "$pl_real"
    else
      backup_path "$pl_l" "$pl_pkg"
      pl_kind=S
    fi
  fi
  ln -sfn "$pl_t" "$pl_real"
  rec_drop L "$pl_pkg" "$pl_l"; rec_drop S "$pl_pkg" "$pl_l"
  rec_add "$pl_kind" "$pl_pkg" "$pl_l" "$pl_t"
  say "  linked         $pl_l -> $pl_t"
}

# ---------------------------------------------------------------- getting a package
get_sums() {
  if [ -n "$SUMS" ]; then return 0; fi
  if [ -n "$FROM" ]; then
    if [ -f "$FROM/SHA256SUMS.txt" ]; then
      SUMS=$FROM/SHA256SUMS.txt
    else
      warn "$FROM/SHA256SUMS.txt not found; the zip files will not be checked"
      SUMS=none
    fi
  else
    say "Downloading SHA256SUMS.txt ..."
    mkdir -p "$TMP/dl"
    fetch "$(base_url)/SHA256SUMS.txt" "$TMP/dl/SHA256SUMS.txt" || die "could not download SHA256SUMS.txt from $(base_url)"
    SUMS=$TMP/dl/SHA256SUMS.txt
  fi
}

prepare_pkg() { # pkg -> PKGDIR, PKGSHA
  pr_zip=$(pkg_zip "$1")
  mkdir -p "$TMP/dl" "$TMP/x"
  if [ -n "$FROM" ]; then
    pr_file=$FROM/$pr_zip
    [ -f "$pr_file" ] || die "$pr_file not found"
  else
    pr_file=$TMP/dl/$pr_zip
    say "  downloading $pr_zip ..."
    fetch "$(base_url)/$pr_zip" "$pr_file" || die "could not download $(base_url)/$pr_zip"
  fi
  PKGSHA=$(sha256_of "$pr_file")
  if [ "$SUMS" != none ]; then
    pr_want=$(awk -v n="$pr_zip" '{f=$2; sub(/^\*/, "", f); if (f==n) {print $1; exit}}' "$SUMS")
    [ -n "$pr_want" ] || die "$pr_zip is not listed in SHA256SUMS.txt"
    if [ "$pr_want" != "$PKGSHA" ]; then
      if [ -z "$FROM" ]; then rm -f "$pr_file"; fi
      die "checksum mismatch for $pr_zip (expected $pr_want, got $PKGSHA); nothing was installed from it"
    fi
    say "  checksum ok    $pr_zip"
  fi
  rm -rf "$TMP/x/$1"
  extract_zip "$pr_file" "$TMP/x"
  PKGDIR=$TMP/x/$1
  [ -d "$PKGDIR" ] || die "$pr_zip does not contain a $1/ folder"
  if [ -z "$FROM" ]; then rm -f "$pr_file"; fi
}

# ---------------------------------------------------------------- install procedures
install_cores() { # pkg   (generic: libs + info files)
  ic_pkg=$1
  for ic_item in $M_LIBS; do
    ic_stock=0
    case "$ic_item" in *'!') ic_stock=1; ic_item=${ic_item%!} ;; esac
    ic_src=${ic_item%%=*}
    ic_link=${ic_item#*=}
    place_file "$PKGDIR/$ic_src" "$HCL/$ic_src" 755 "$ic_pkg"
    place_link "$HCL/$ic_src" "/usr/lib/libretro/$ic_link" "$ic_pkg" "$ic_stock"
  done
  for ic_info in $M_INFOS; do
    place_file "$PKGDIR/$ic_info" "/usr/share/libretro/info/$ic_info" 644 "$ic_pkg"
  done
}

install_dsperate() {
  idp=ds-dsperate
  place_file "$PKGDIR/dsperate" "$DSP_DIR/dsperate" 755 $idp
  place_file "$PKGDIR/glue/hb_dsperate_run.sh" "$DSP_DIR/hb_dsperate_run.sh" 755 $idp
  place_file "$PKGDIR/glue/hb_dsperate.py" "$DSP_DIR/hb_dsperate.py" 755 $idp
  for idp_f in games.txt groups.txt mpenv.txt gamecontrollerdb_rg35xx.txt; do
    place_config "$PKGDIR/glue/$idp_f" "$DSP_DIR/$idp_f" 644 $idp
  done
  # The hand-over at the very top of DraStic's launch.sh (see cores/ds-dsperate/README.md, install step 1).
  idp_real=$ROOT$DRASTIC_LAUNCH
  if [ ! -f "$idp_real" ]; then
    warn "$DRASTIC_LAUNCH not found, so DS games cannot be handed to DSperate yet. Add these lines at the top of that script once it exists:"
    fork_block >&2
    return 0
  fi
  if grep -qF "$FORK_BEGIN" "$idp_real"; then
    say "  hand-over      already in $DRASTIC_LAUNCH"
    rec_add D $idp "$DRASTIC_LAUNCH"
    return 0
  fi
  if grep -q 'hb_dsperate_run.sh' "$idp_real"; then
    say "  hand-over      $DRASTIC_LAUNCH already has its own DSperate lines; left alone"
    return 0
  fi
  if [ "$DRY" = 1 ]; then
    say "  would insert   DSperate hand-over lines at the top of $DRASTIC_LAUNCH (a copy of the script is saved in $HCL/backup/ first)"
    return 0
  fi
  touch_path "$DRASTIC_LAUNCH"
  mkdir -p "$ROOT$HCL/backup"
  if [ ! -e "$ROOT$HCL/backup/launch.sh.before_dsperate" ]; then
    cp -p "$idp_real" "$ROOT$HCL/backup/launch.sh.before_dsperate"
  fi
  fork_block > "$TMP/fork.txt"
  awk 'NR==FNR {b = b $0 "\n"; next}
       FNR==1 && /^#!/ {print; printf "%s", b; next}
       FNR==1 {printf "%s", b}
       {print}' "$TMP/fork.txt" "$idp_real" > "$TMP/launch.new"
  cat "$TMP/launch.new" > "$idp_real"      # same file, same mode
  rec_add D $idp "$DRASTIC_LAUNCH"
  say "  inserted       DSperate hand-over at the top of $DRASTIC_LAUNCH"
}

fork_block() {
  printf '%s\n' "$FORK_BEGIN"
  cat <<'EOF'
HB_DSP=/userdata/system/configs/dsperate
hb_base=`basename "$1"`; hb_base="${hb_base%.*}"
[ ! -e $HB_DSP/off ] && [ -f $HB_DSP/dsperate ] && grep -qxF "$hb_base" $HB_DSP/games.txt 2>/dev/null && exec /bin/bash $HB_DSP/hb_dsperate_run.sh "$1"
EOF
  printf '%s\n' "$FORK_END"
}

patch_gnu_flag() {
  # GNU patch may ask questions on a terminal; -f stops that. Other patch tools do not need it.
  if patch --version 2>/dev/null | grep -qi 'gnu patch'; then printf '%s' "-f"; fi
}

# Is the launcher patch in the file? "patch --dry-run -R" alone is not enough: patch tools answer "Ignore -R?" on a file that
# was never patched and some of them then say yes. So we also look for the patch's own "# hb_..." comment lines in the file.
# Prints: applied | none | partial
patch_state() { # patchfile target
  ps_m=$(mktemp "${TMPDIR:-/tmp}/hbmark.XXXXXX")
  awk '/^\+ *# hb_/ {sub(/^\+ */, ""); print}' "$1" > "$ps_m"
  ps_total=0; ps_found=0
  while IFS= read -r ps_line; do
    [ -n "$ps_line" ] || continue
    ps_total=$((ps_total + 1))
    if grep -qF -e "$ps_line" "$2"; then ps_found=$((ps_found + 1)); fi
  done < "$ps_m"
  rm -f "$ps_m"
  if [ "$ps_total" -gt 0 ] && [ "$ps_found" = "$ps_total" ]; then printf 'applied'
  elif [ "$ps_found" = 0 ]; then printf 'none'
  else printf 'partial'; fi
}

install_scripts() {
  isp=knulli-scripts
  if [ "$DRY" = 1 ] && [ ! -d "$PKGDIR" ]; then
    say "  would install  the .py helpers and fonts/ into $CLAUDE_DIR/"
    say "  would install  nds_save_sync.sh into /userdata/system/scripts/ (it must be the only file there)"
    say "  would install  service wrappers into /userdata/system/services/ (they stay off until named in knulli.conf)"
    say "  would patch    KNULLI's emulatorlauncher.py with launcher/emulatorlauncher.patch (skipped if already applied)"
    return 0
  fi
  for isp_f in "$PKGDIR"/*.py; do
    [ -e "$isp_f" ] || continue
    place_file "$isp_f" "$CLAUDE_DIR/$(basename "$isp_f")" 644 $isp
  done
  for isp_f in "$PKGDIR"/fonts/*; do
    [ -e "$isp_f" ] || continue
    place_file "$isp_f" "$CLAUDE_DIR/fonts/$(basename "$isp_f")" 644 $isp
  done
  place_file "$PKGDIR/nds_save_sync.sh" /userdata/system/scripts/nds_save_sync.sh 755 $isp
  for isp_f in "$PKGDIR"/services/*; do
    [ -e "$isp_f" ] || continue
    place_file "$isp_f" "/userdata/system/services/$(basename "$isp_f")" 755 $isp
  done
  # KNULLI runs every file in the scripts folder, so tell the user about strangers.
  for isp_s in "$ROOT"/userdata/system/scripts/*; do
    [ -e "$isp_s" ] || continue
    if [ "$(basename "$isp_s")" != nds_save_sync.sh ]; then
      warn "$(basename "$isp_s") is also in /userdata/system/scripts/. KNULLI runs every file there; the hook expects to be the only one."
    fi
  done
  # The launcher patch.
  isp_patch=$PKGDIR/launcher/emulatorlauncher.patch
  [ -f "$isp_patch" ] || die "the package is missing launcher/emulatorlauncher.patch"
  isp_tgt=$(awk '/^--- /{print $2; exit}' "$isp_patch")
  isp_tgt=${isp_tgt#a/}
  isp_flag=$(patch_gnu_flag)
  if [ ! -f "$ROOT/$isp_tgt" ]; then
    warn "/$isp_tgt not found, so the launcher patch was skipped (a Join will not start the guest automatically)"
    return 0
  fi
  isp_state=$(patch_state "$isp_patch" "$ROOT/$isp_tgt")
  case "$isp_state" in
    applied)
      say "  launcher patch already applied" ;;
    partial)
      warn "/$isp_tgt contains only part of the launcher patch; left alone. Compare it with knulli-scripts/launcher/emulatorlauncher.patch." ;;
    *)
      # shellcheck disable=SC2086
      if patch $isp_flag --dry-run -p1 -d "${ROOT:-/}" < "$isp_patch" >/dev/null 2>&1; then
        if [ "$DRY" = 1 ]; then
          say "  would patch    /$isp_tgt"
        else
          touch_path "/$isp_tgt"
          mkdir -p "$ROOT$HCL/patches"
          cp "$isp_patch" "$ROOT$HCL/patches/emulatorlauncher.patch"
          # shellcheck disable=SC2086
          patch $isp_flag -p1 -d "${ROOT:-/}" < "$isp_patch" >/dev/null
          if [ "$(patch_state "$isp_patch" "$ROOT/$isp_tgt")" != applied ]; then die "the launcher patch did not take; check /$isp_tgt"; fi
          rec_add X $isp "$HCL/patches/emulatorlauncher.patch"
          say "  patched        /$isp_tgt"
        fi
      else
        warn "the launcher patch does not apply to /$isp_tgt (a different KNULLI version?). Everything else was installed; see knulli-scripts/README.md."
      fi ;;
  esac
}

install_pkg() {
  ip=$1
  pkg_meta "$ip"
  say ""
  say "== $ip: $M_DESC"
  PKGDIR=/nonexistent; PKGSHA=-
  if [ "$DRY" = 0 ] || [ -n "$FROM" ]; then
    prepare_pkg "$ip"
  else
    say "  (dry run: not downloading $(pkg_zip "$ip"))"
  fi
  case "$ip" in
    ds-dsperate)    install_dsperate ;;
    knulli-scripts) install_scripts ;;
    *)              install_cores "$ip" ;;
  esac
  rec_drop P "$ip" ""
  rec_add P "$ip" "$PKGSHA" "$(date '+%Y-%m-%d %H:%M:%S')"
  rm -rf "$TMP/x/$ip"
  DONE_PKGS="$DONE_PKGS $ip"
}

# ---------------------------------------------------------------- uninstall
remove_fork_block() { # launch.sh path (real)
  rfb_f=$1
  rfb_t="$rfb_f.hbtmp.$$"
  awk -v b="$FORK_BEGIN" -v e="$FORK_END" '$0==b {s=1; next} $0==e {s=0; next} !s' "$rfb_f" > "$rfb_t"
  cat "$rfb_t" > "$rfb_f"
  rm -f "$rfb_t"
}

uninstall_pkg() {
  up=$1
  say ""
  say "== $up"
  if ! is_installed "$up"; then
    say "  not installed (nothing recorded in $REC)"
    return 0
  fi
  up_l=$(mktemp "${TMPDIR:-/tmp}/hbun.XXXXXX")
  up_keep=" "
  # 1) symlinks over stock files: only remove the link when the original can be put back
  rec_list "$up" S > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    if rec_has B "$up" "$up_a"; then
      if [ -L "$ROOT$up_a" ]; then touch_path "$up_a"; rm -f "$ROOT$up_a"; say "  removed link   $up_a"; fi
    elif rec_has B "$up" "$up_b"; then
      # the link was already there (pointing at the same file) and the file itself was backed up: keep the link, the file comes back below
      say "  kept link      $up_a (it was there before; its file is put back)"
    else
      warn "$up_a replaced a stock core, but no copy of the original is recorded, so the link and its file stay (otherwise that core would be gone). Restore the stock core from KNULLI (an update or another device) and remove them by hand."
      up_keep="$up_keep$up_b "
    fi
  done < "$up_l"
  rec_list "$up" L > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    if [ -L "$ROOT$up_a" ]; then touch_path "$up_a"; rm -f "$ROOT$up_a"; say "  removed link   $up_a"; fi
  done < "$up_l"
  # 2) files
  rec_list "$up" F > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    case "$up_keep" in *" $up_a "*) continue ;; esac
    if [ -e "$ROOT$up_a" ] || [ -L "$ROOT$up_a" ]; then touch_path "$up_a"; rm -f "$ROOT$up_a"; say "  removed        $up_a"; fi
  done < "$up_l"
  rec_list "$up" C > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    if [ -f "$ROOT$up_a" ]; then
      if [ "$(sha256_of "$ROOT$up_a")" = "$up_b" ]; then
        rm -f "$ROOT$up_a"; say "  removed        $up_a"
      else
        say "  kept           $up_a (you changed it)"
      fi
    fi
  done < "$up_l"
  # 3) patch and hand-over lines
  rec_list "$up" X > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    up_flag=$(patch_gnu_flag)
    if [ -f "$ROOT$up_a" ]; then
      up_tgt=$(awk '/^--- /{print $2; exit}' "$ROOT$up_a")
      up_tgt=${up_tgt#a/}
      if [ -f "$ROOT/$up_tgt" ] && [ "$(patch_state "$ROOT$up_a" "$ROOT/$up_tgt")" = applied ]; then
        # shellcheck disable=SC2086
        if patch $up_flag --dry-run -R -p1 -d "${ROOT:-/}" < "$ROOT$up_a" >/dev/null 2>&1; then
          touch_path "/$up_tgt"
          # shellcheck disable=SC2086
          patch $up_flag -R -p1 -d "${ROOT:-/}" < "$ROOT$up_a" >/dev/null
          say "  launcher patch taken out of /$up_tgt"
        else
          warn "the launcher patch no longer reverses cleanly (the file changed); /$up_tgt left as it is"
        fi
      else
        say "  launcher patch is not in /$up_tgt any more; nothing to take out"
      fi
      rm -f "$ROOT$up_a"
    fi
  done < "$up_l"
  rec_list "$up" D > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    if [ -f "$ROOT$up_a" ] && grep -qF "$FORK_BEGIN" "$ROOT$up_a"; then
      remove_fork_block "$ROOT$up_a"
      rm -f "$ROOT$HCL/backup/launch.sh.before_dsperate"
      say "  hand-over lines taken out of $up_a"
    fi
  done < "$up_l"
  # 4) put the originals back
  rec_list "$up" B > "$up_l"
  while IFS="$TAB" read -r up_k up_p up_a up_b; do
    [ -n "$up_p" ] || continue
    if [ -e "$ROOT$up_b" ] || [ -L "$ROOT$up_b" ]; then
      if [ -e "$ROOT$up_a" ] || [ -L "$ROOT$up_a" ]; then
        warn "$up_a exists again; the original stays in $up_b"
      else
        touch_path "$up_a"
        mkdir -p "$(dirname "$ROOT$up_a")"
        mv "$ROOT$up_b" "$ROOT$up_a"
        say "  restored       $up_a (from $up_b)"
      fi
    else
      warn "the saved original $up_b is missing; $up_a was not restored"
    fi
  done < "$up_l"
  rm -f "$up_l"
  rmdir "$ROOT$CLAUDE_DIR/fonts" 2>/dev/null || true
  rmdir "$ROOT$DSP_DIR" 2>/dev/null || true
  rec_drop "" "$up" ""
  DONE_PKGS="$DONE_PKGS $up"
}

tidy_after_uninstall() {
  tu_f=$(rec_file)
  if [ -f "$tu_f" ] && ! awk -F'\t' '$1 !~ /^#/ && NF {f=1} END{exit (f ? 0 : 1)}' "$tu_f"; then
    rm -f "$tu_f"
  fi
  if [ -d "$ROOT$HCL" ]; then
    find "$ROOT$HCL/backup" "$ROOT$HCL/patches" -depth -type d -exec rmdir {} \; 2>/dev/null || true
    rmdir "$ROOT$HCL" 2>/dev/null || true
  fi
}

# ---------------------------------------------------------------- list / menu
show_list() { # numbered=0|1
  sl_n=0
  printf '%s\n' "Packages (both devices need the same ones):"
  for sl_p in $ALL_PKGS; do
    pkg_meta "$sl_p"
    sl_n=$((sl_n + 1))
    if is_installed "$sl_p"; then sl_mark="[installed]"; else sl_mark="           "; fi
    if [ "$1" = 1 ]; then
      printf ' %2d) %-24s %s %-17s %s\n' "$sl_n" "$sl_p" "$sl_mark" "$M_SYS" "$M_DESC"
    else
      printf '  %-24s %s %-17s %s\n' "$sl_p" "$sl_mark" "$M_SYS" "$M_DESC"
    fi
  done
}

nth_pkg() { # n
  np_i=0
  for np_x in $ALL_PKGS; do
    np_i=$((np_i + 1))
    if [ "$np_i" = "$1" ]; then printf '%s' "$np_x"; return 0; fi
  done
  return 1
}

menu() {
  show_list 1
  say ""
  say "Type package numbers to install (for example: 4 5), 'u 4' to remove, 'a' for all, or 'q' to quit."
  printf '> '
  read -r m_ans || exit 0
  m_act=install
  m_sel=""
  set -- $m_ans
  if [ $# -eq 0 ]; then exit 0; fi
  case "$1" in
    q|Q) exit 0 ;;
    a|A) WANT_ALL=1; return 0 ;;
    u|U) m_act=uninstall; shift ;;
  esac
  for m_n in "$@"; do
    case "$m_n" in
      a|A) WANT_ALL=1; m_sel=""; break ;;
      *[!0-9]*|"") die "not a package number: $m_n" ;;
    esac
    m_p=$(nth_pkg "$m_n") || die "no package number $m_n"
    m_sel="$m_sel $m_p"
  done
  MODE=$m_act
  PKGS=$m_sel
}

# ---------------------------------------------------------------- main
while [ $# -gt 0 ]; do
  case "$1" in
    --all) WANT_ALL=1 ;;
    --list) MODE=list ;;
    --uninstall|--remove) MODE=uninstall ;;
    --dry-run|-n) DRY=1 ;;
    --force) FORCE=1 ;;
    --root) [ $# -ge 2 ] || die "--root needs a folder"; ROOT=$2; shift ;;
    --root=*) ROOT=${1#--root=} ;;
    --from) [ $# -ge 2 ] || die "--from needs a folder"; FROM=$2; shift ;;
    --from=*) FROM=${1#--from=} ;;
    --release) [ $# -ge 2 ] || die "--release needs a tag"; RELEASE=$2; shift ;;
    --release=*) RELEASE=${1#--release=} ;;
    -h|--help) usage; exit 0 ;;
    -*) usage >&2; die "unknown option: $1" ;;
    *)
      valid_pkg "$1" || { show_list 0 >&2; die "unknown package: $1"; }
      PKGS="$PKGS $1" ;;
  esac
  shift
done

ROOT=${ROOT%/}
case "$ROOT" in ""|/*) ;; *) die "--root must be an absolute path" ;; esac
if [ -n "$FROM" ] && [ ! -d "$FROM" ]; then die "--from: $FROM is not a folder"; fi

if [ "$MODE" = list ]; then
  show_list 0
  exit 0
fi

if [ -z "$PKGS" ] && [ "$WANT_ALL" = 0 ]; then
  if [ -t 0 ]; then
    menu
  else
    usage
    exit 0
  fi
fi
if [ "$WANT_ALL" = 1 ]; then PKGS=$ALL_PKGS; fi

# Order: everything else first, wrappers that depend on other packages last (install) / first (uninstall).
ORDERED=""
for o_p in $ALL_PKGS; do
  if in_list "$o_p" "$PKGS" && [ "$o_p" != arcade-mahjong-pad ]; then ORDERED="$ORDERED $o_p"; fi
done

if [ "$MODE" = install ]; then
  # arcade-mahjong-pad calls the real cores by their stock names in hanbang_cores/
  if in_list arcade-mahjong-pad "$PKGS"; then
    for o_d in "arcade-fbneo:fbneo_libretro.so" "arcade-mame2003-plus:mame2003_plus_libretro.so"; do
      o_pkg=${o_d%%:*}; o_file=${o_d#*:}
      if ! in_list "$o_pkg" "$PKGS" && [ ! -e "$ROOT$HCL/$o_file" ]; then
        say "arcade-mahjong-pad needs $o_file in $HCL/, so $o_pkg is added."
        ORDERED="$o_pkg$ORDERED"
        ORDERED=" $ORDERED"
      fi
    done
    ORDERED="$ORDERED arcade-mahjong-pad"
  fi
else
  if in_list arcade-mahjong-pad "$PKGS"; then ORDERED="arcade-mahjong-pad $ORDERED"; fi
fi

# --- checks before touching anything
if [ -z "$ROOT" ] && [ "$DRY" = 0 ]; then
  [ "$(id -u)" = 0 ] || die "run this as root (on KNULLI: ssh root@<device>)"
fi
if [ -z "$ROOT" ] && [ "$FORCE" = 0 ]; then
  case "$(uname -m)" in
    aarch64|arm64) ;;
    *) die "these builds are for Linux aarch64; this is $(uname -m). Use --force to try anyway." ;;
  esac
  if [ ! -d /userdata ]; then die "/userdata not found: this does not look like KNULLI. Use --force to try anyway."; fi
fi
if [ -z "$ROOT" ] && [ "$DRY" = 0 ]; then
  if ! command -v knulli-save-overlay >/dev/null 2>&1; then
    warn "knulli-save-overlay not found: links and .info files under /usr will be gone after a reboot"
  fi
  if command -v curl >/dev/null 2>&1; then
    rg=$(curl -s -m 2 http://127.0.0.1:1234/runningGame 2>/dev/null || true)
    case "$rg" in
      ""|*"NO GAME"*) ;;
      *) warn "EmulationStation reports a running game. Quit it first if you can; the files are swapped in one step, but a running game keeps using the old core." ;;
    esac
  fi
fi

# --- work area (on the SD card, not in RAM, because some packages are large)
if [ "$MODE" = install ]; then
  if [ "$DRY" = 1 ]; then
    TMP=$(mktemp -d "${TMPDIR:-/tmp}/hbinst.XXXXXX")
  else
    mkdir -p "$ROOT$HCL"
    TMP=$(mktemp -d "$ROOT$HCL/.install.XXXXXX")
  fi
  if [ "$DRY" = 0 ] || [ -n "$FROM" ]; then get_sums; fi
fi

if [ "$DRY" = 1 ]; then say "Dry run: nothing will be changed."; fi

if [ "$MODE" = install ]; then
  for i_p in $ORDERED; do install_pkg "$i_p"; done
else
  for u_p in $ORDERED; do
    if [ "$u_p" = arcade-fbneo ] || [ "$u_p" = arcade-mame2003-plus ]; then
      if is_installed arcade-mahjong-pad && ! in_list arcade-mahjong-pad "$ORDERED"; then
        say ""; say "== $u_p"
        say "  skipped: arcade-mahjong-pad still needs it. Remove that first, or remove both together."
        continue
      fi
    fi
    if [ "$DRY" = 1 ]; then
      say ""; say "== $u_p"
      if is_installed "$u_p"; then
        say "  would remove everything recorded for it in $REC and put the saved originals back"
      else
        say "  not installed (nothing recorded in $REC)"
      fi
    else
      uninstall_pkg "$u_p"
    fi
  done
  if [ "$DRY" = 0 ]; then tidy_after_uninstall; fi
fi

# --- wrap up
say ""
if [ "$DRY" = 1 ]; then
  say "Dry run finished; nothing was changed."
  exit 0
fi
if [ "$SYS_TOUCHED" = 1 ]; then
  if [ -n "$ROOT" ]; then
    say "(--root: skipped remount and knulli-save-overlay)"
  else
    save_overlay
  fi
fi
sync 2>/dev/null || true

if [ "$MODE" = install ]; then
  say "Done. Installed:$DONE_PKGS"
  say ""
  say "Next: this script never edits knulli.conf. Choose a core per game in EmulationStation (game > advanced settings > core)"
  say "or with a line such as  gba[\"My Game.gba\"].core=mgba_dual  in /userdata/system/knulli.conf. Details: cores/<package>/README.md."
  for n_p in $DONE_PKGS; do
    pkg_meta "$n_p"
    say "  $n_p: $M_HINT"
  done
  say ""
  say "Do the same on the second device: both need the same packages and the same game file."
else
  if [ -n "$DONE_PKGS" ]; then say "Done. Removed:$DONE_PKGS"; else say "Nothing was removed."; fi
fi
say "Record of what was installed: $REC"
