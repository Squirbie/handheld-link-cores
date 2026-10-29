<p align="center"><a href="README.md"><img src="../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# card-update — update the cores on a KNULLI card from Windows or macOS

For cards that already have these cores in `system/hanbang_cores/` (a card set up with [`install.sh`](../install.sh), or a ready-made card image built with these cores). Put the card in your PC and run one file:

- It replaces **only** files whose md5 is a known older build, listed in `card-updates.txt` of the [latest release](https://github.com/Squirbie/handheld-link-cores/releases/latest). A file it does not recognise is left alone.
- The new file is checked first (the release's `SHA256SUMS.txt` and the md5 in the list), written next to the old one, checked again, and only then swapped in.
- The old file is kept in `system/hanbang_cores/backup/`.
- **Offline package:** when `card-updates.txt`, `SHA256SUMS.txt` and the package zips sit next to the script, it uses those files and needs no internet (the `.bat`, the `.command` and `bash update-card.sh` all look there first; the one-line commands always download).

Right now it updates **MAME 2003-Plus bf8 → bf9** (`mame2003_plus_libretro.so`).

## Windows

1. Put the card that has `system\hanbang_cores` in the PC (for KNULLI with two cards, that is the games card).
2. Download [`card-update.zip`](https://github.com/Squirbie/handheld-link-cores/releases/latest/download/card-update.zip), **extract it**, and double-click `update-card-windows.bat`.
   If Windows says "Windows protected your PC", click **More info → Run anyway**.
   Or paste this into PowerShell instead:
   ```powershell
   irm https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/card-update/update-card-windows.ps1 | iex
   ```
3. Press Enter to update. Eject the card (Safely Remove Hardware) and put it back in the handheld.

## macOS

1. Put the card in the Mac.
2. Open **Terminal** and paste:
   ```sh
   curl -fsSL https://raw.githubusercontent.com/Squirbie/handheld-link-cores/main/card-update/update-card.sh | bash
   ```
   `update-card-mac.command` from the zip does the same, but macOS blocks downloaded scripts from unknown developers until you allow them in System Settings → Privacy & Security, so Terminal is quicker.
3. Press Enter to update. Eject the card and put it back in the handheld.

The same `update-card.sh` works on Linux (it looks under `/media`, `/run/media` and `/mnt`).

## Notes

- **Netplay needs the same build on both devices:** update both cards.
- New builds cannot load save states from older ones (the state layout changed); in-game saves and high scores are not touched.
- To go back, put the file from `system/hanbang_cores/backup/` back in place.
- Tested on 2026-10-29: macOS (exFAT card image; Enter, `n`, no terminal, already new, unknown build, `curl | bash`, the `.command` file) and Windows Server 2025 with Windows PowerShell 5.1 (the `.bat` with Enter and with `n`, already new, unknown build, no card). No `._` files are left on the card on macOS. Also tested: an offline package in a folder with a Korean name and a space, with GitHub blocked, on both systems, and the `.bat` started from PowerShell 7.
