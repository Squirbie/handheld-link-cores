<p align="center"><a href="README.md"><img src="../docs/images/lang-en-on.svg" height="44" alt="English (selected)"></a><a href="README.ko.md"><img src="../docs/images/lang-ko-off.svg" height="44" alt="한국어"></a></p>

# Licenses

Each core keeps its upstream license, and its patches in this repository are under the same terms. The full texts are in this folder.

| Upstream | File | License |
|---|---|---|
| melonDS DS | `melonds-ds_LICENSE` | GPL-3.0 |
| DSperate | `DSperate_LICENSE` | GPL-3.0 |
| gambatte-libretro | `gambatte-libretro_COPYING` | GPL-2.0 |
| mGBA | `mgba_LICENSE` | MPL-2.0 |
| gpSP | `gpsp_COPYING` | GPL-2.0 |
| Beetle WonderSwan | `beetle-wswan-libretro_COPYING` | GPL-2.0 |
| Beetle NeoPop | `beetle-ngp-libretro_COPYING` | GPL-2.0 |
| Genesis Plus GX | `Genesis-Plus-GX_LICENSE.txt` | **Non-commercial**; modified versions must ship their full source |
| blueMSX | `blueMSX-libretro_license.txt` | Per file (BSD-style, GPL, zlib …) |
| FCEUmm | `libretro-fceumm_Copying` | GPL-2.0 |
| DOSBox Pure | `dosbox-pure_LICENSE` | GPL-2.0 |
| MAME 2003-Plus | `mame2003-plus-libretro_LICENSE.md` | **Non-commercial** (the classic MAME license) |
| FinalBurn Neo | `FBNeo_src_license.txt` (+ `FBNeo_LICENSE.md`) | **Non-commercial**; source changes must be published; ship the text unchanged |

Cores marked **non-commercial** may not be sold or shipped on devices that are sold.

## Our own files

| What | License |
|---|---|
| `knulli-scripts/` (scripts, services, launcher patch), the docs and the build tooling | GPL-3.0-or-later — [`../LICENSE`](../LICENSE) |
| `cores/arcade-mahjong-pad/patches/hb_mjpad.c` | The same terms as the core it wraps: the FinalBurn Neo license when built as `fbneo_mj`, the MAME license when built as `mame2003_plus_mj` (both non-commercial) |
| Galmuri pixel fonts in the `knulli-scripts` release zip | SIL Open Font License 1.1 (`fonts/Galmuri-OFL.txt`) |
