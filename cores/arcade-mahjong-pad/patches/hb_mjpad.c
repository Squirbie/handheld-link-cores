/* hb_mjpad.c - Mahjong Pad: answers keyboard-only arcade mahjong keys from the gamepad (libretro wrapper core).
 * License: offered under the same terms as the core it wraps - the FinalBurn Neo license when built as fbneo_mj,
 * the MAME license when built as mame2003_plus_mj (both non-commercial). Part of handheld-link-cores. */
/* hb_mjpad — 마작 판 단추를 기기 패드로 (10/27)
 * 진짜 코어(FBNeo · MAME 2003-Plus)는 마작 키(A~N · 깡 · 퐁 · 치 · 리치 · 론)를 키보드로만 읽어서
 * 키보드가 없는 기기에서는 마작을 칠 수 없다. 이 감싸개는 진짜 코어를 dlopen 해 retro_* 를 모두 넘기고,
 * 진짜 코어가 키보드를 물으면 1P 패드로 만든 마작 키를 답한다. 고른 칸은 화면 아래 줄에 그린다.
 *   ←/→ 칸 옮기기(누르고 있으면 되풀이) · ↓ 맨 왼쪽(A) · ↑ 맨 오른쪽(N, 쯔모한 패)
 *   A 고른 칸 누르기(버리기 · 메뉴 고르기) · B 론(쯔모) · X 리치 · Y 퐁 · L 치 · R 깡 · R2 N 바로 · L2 줄 보이기/숨기기
 *   SELECT 동전 · START 시작 — 진짜 코어 그대로
 * 진짜 코어 자리: HB_MJ_REAL(컴파일 때) — 환경 값 HB_MJ_REAL 이 있으면 그것(시험용).
 * 조이스틱 마작(슈퍼 카네코 노바 · G-테이스트 · 작국지 등)처럼 키보드를 안 쓰는 게임이면 아무것도 안 하고 넘긴다. */
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "libretro.h"

#ifndef HB_MJ_REAL
#define HB_MJ_REAL "/userdata/system/hanbang_cores/fbneo_libretro.so"
#endif

static void *h;
#define R(name) static __typeof__(&name) p_##name;
R(retro_set_environment) R(retro_set_video_refresh) R(retro_set_audio_sample)
R(retro_set_audio_sample_batch) R(retro_set_input_poll) R(retro_set_input_state)
R(retro_init) R(retro_deinit) R(retro_api_version) R(retro_get_system_info)
R(retro_get_system_av_info) R(retro_set_controller_port_device) R(retro_reset) R(retro_run)
R(retro_serialize_size) R(retro_serialize) R(retro_unserialize) R(retro_cheat_reset)
R(retro_cheat_set) R(retro_load_game) R(retro_load_game_special) R(retro_unload_game)
R(retro_get_region) R(retro_get_memory_data) R(retro_get_memory_size)

static void load_real(void)
{
   const char *p;
   if (h)
      return;
   p = getenv("HB_MJ_REAL");
   h = dlopen(p && *p ? p : HB_MJ_REAL, RTLD_NOW | RTLD_LOCAL);
   if (!h) {
      fprintf(stderr, "[hb_mjpad] 진짜 코어를 못 엶: %s\n", dlerror());
      abort();
   }
#define S(name) p_##name = (__typeof__(p_##name))dlsym(h, #name);
   S(retro_set_environment) S(retro_set_video_refresh) S(retro_set_audio_sample)
   S(retro_set_audio_sample_batch) S(retro_set_input_poll) S(retro_set_input_state)
   S(retro_init) S(retro_deinit) S(retro_api_version) S(retro_get_system_info)
   S(retro_get_system_av_info) S(retro_set_controller_port_device) S(retro_reset) S(retro_run)
   S(retro_serialize_size) S(retro_serialize) S(retro_unserialize) S(retro_cheat_reset)
   S(retro_cheat_set) S(retro_load_game) S(retro_load_game_special) S(retro_unload_game)
   S(retro_get_region) S(retro_get_memory_data) S(retro_get_memory_size)
}

/* ---- 프런트엔드 콜백 ---- */
static retro_environment_t fe_env;
static retro_video_refresh_t fe_video;
static retro_input_poll_t fe_poll;
static retro_input_state_t fe_state;
static enum retro_pixel_format pixfmt = RETRO_PIXEL_FORMAT_0RGB1555;
/* 마작 키를 키보드로 읽는 게임일 때만 켬 — 진짜 코어가 처음 키보드를 물을 때 켜짐(FBNeo 는 마작 키 게임에서만 키보드를 물음).
 * MAME 2003-Plus 는 입력 방식 simultaneous 에서 늘 키보드를 물어 HB_MJ_ALWAYS 로 처음부터 켬(마작 게임에만 이 코어를 씀). */
#ifdef HB_MJ_ALWAYS
static int mj_on = 1;
#else
static int mj_on = 0;
#endif

/* ---- 마작 패드 상태 ---- */
#define NCELL 14
static int cursor = NCELL - 1;        /* 처음엔 N(쯔모한 패) */
static int show_bar = 1;
static unsigned bar_timer;            /* 칸을 옮긴 뒤 줄을 또렷이 보이는 시간(장) */
static uint16_t pad, pad_prev;
static unsigned hold_l, hold_r;
static int key_cell = -1;             /* A 를 누르는 동안 누르는 칸 */

static int16_t pad_btn(unsigned id)
{
   return fe_state ? fe_state(0, RETRO_DEVICE_JOYPAD, 0, id) : 0;
}

static void mj_poll(void)
{
   unsigned i;
   uint16_t now = 0;
   if (fe_poll)
      fe_poll();
   if (!mj_on)
      return;
   for (i = 0; i < 16; i++)
      if (pad_btn(i))
         now |= 1u << i;
   pad_prev = pad;
   pad = now;
#define DOWN(b)  (pad & (1u << (b)))
#define EDGE(b)  ((pad & (1u << (b))) && !(pad_prev & (1u << (b))))
   /* ←/→ : 누른 때 한 칸, 18장 뒤부터 6장마다 되풀이 */
   if (DOWN(RETRO_DEVICE_ID_JOYPAD_LEFT)) {
      hold_l++;
      if (hold_l == 1 || (hold_l > 18 && (hold_l - 18) % 6 == 0)) {
         if (cursor > 0) cursor--;
         bar_timer = 120;
      }
   } else
      hold_l = 0;
   if (DOWN(RETRO_DEVICE_ID_JOYPAD_RIGHT)) {
      hold_r++;
      if (hold_r == 1 || (hold_r > 18 && (hold_r - 18) % 6 == 0)) {
         if (cursor < NCELL - 1) cursor++;
         bar_timer = 120;
      }
   } else
      hold_r = 0;
   if (EDGE(RETRO_DEVICE_ID_JOYPAD_DOWN)) { cursor = 0; bar_timer = 120; }
   if (EDGE(RETRO_DEVICE_ID_JOYPAD_UP))   { cursor = NCELL - 1; bar_timer = 120; }
   if (EDGE(RETRO_DEVICE_ID_JOYPAD_L2))   show_bar = !show_bar;
   /* A: 누르는 동안 고른 칸의 키(누르기 시작한 칸을 붙잡음) */
   if (DOWN(RETRO_DEVICE_ID_JOYPAD_A)) {
      if (key_cell < 0)
         key_cell = cursor;
   } else
      key_cell = -1;
   if (bar_timer)
      bar_timer--;
}

static int16_t mj_key(unsigned id)
{
   if (id >= RETROK_a && id <= RETROK_n)
      return (key_cell == (int)(id - RETROK_a)) ||
             (id == RETROK_n && DOWN(RETRO_DEVICE_ID_JOYPAD_R2));
   switch (id) {
   case RETROK_z:      return DOWN(RETRO_DEVICE_ID_JOYPAD_B) ? 1 : 0;   /* 론 */
   case RETROK_LSHIFT: return DOWN(RETRO_DEVICE_ID_JOYPAD_X) ? 1 : 0;   /* 리치 */
   case RETROK_LALT:   return DOWN(RETRO_DEVICE_ID_JOYPAD_Y) ? 1 : 0;   /* 퐁 */
   case RETROK_SPACE:  return DOWN(RETRO_DEVICE_ID_JOYPAD_L) ? 1 : 0;   /* 치 */
   case RETROK_LCTRL:  return DOWN(RETRO_DEVICE_ID_JOYPAD_R) ? 1 : 0;   /* 깡 */
   default:            return 0;
   }
}

static int16_t my_state(unsigned port, unsigned device, unsigned index, unsigned id)
{
   if ((device & RETRO_DEVICE_MASK) == RETRO_DEVICE_KEYBOARD) {
      mj_on = 1;   /* 진짜 코어가 키보드를 물으면 마작 키 게임 — 이때부터 켬 */
      return mj_key(id);
   }
   return fe_state ? fe_state(port, device, index, id) : 0;
}

/* ---- 화면 아래 줄(14칸 A~N · 고른 칸 노랑) ---- */
static uint8_t *fbuf;
static size_t fbuf_size;
/* 3x5 글꼴 A~N */
static const uint8_t font[NCELL][5] = {
   {2,5,7,5,5},{6,5,6,5,6},{3,4,4,4,3},{6,5,5,5,6},{7,4,6,4,7},{7,4,6,4,4},{3,4,5,5,3},
   {5,5,7,5,5},{7,2,2,2,7},{1,1,1,5,2},{5,5,6,5,5},{4,4,4,4,7},{5,7,7,5,5},{5,7,7,7,5} };

static void put(uint8_t *row, unsigned x, uint32_t rgb)
{
   if (pixfmt == RETRO_PIXEL_FORMAT_XRGB8888)
      ((uint32_t *)row)[x] = rgb;
   else if (pixfmt == RETRO_PIXEL_FORMAT_RGB565)
      ((uint16_t *)row)[x] = (uint16_t)(((rgb >> 8) & 0xf800) | ((rgb >> 5) & 0x07e0) | ((rgb >> 3) & 0x1f));
   else
      ((uint16_t *)row)[x] = (uint16_t)(((rgb >> 9) & 0x7c00) | ((rgb >> 6) & 0x03e0) | ((rgb >> 3) & 0x1f));
}

/* 게임 화면을 3/8 밝기로(고르지 않은 칸 — 패가 비쳐 보이게) */
static void dim(uint8_t *row, unsigned x)
{
   if (pixfmt == RETRO_PIXEL_FORMAT_XRGB8888) {
      uint32_t c = ((uint32_t *)row)[x];
      ((uint32_t *)row)[x] = ((c >> 2) & 0x3f3f3f) + ((c >> 3) & 0x1f1f1f);
   } else if (pixfmt == RETRO_PIXEL_FORMAT_RGB565) {
      uint16_t c = ((uint16_t *)row)[x];
      ((uint16_t *)row)[x] = (uint16_t)(((c >> 2) & 0x39e7) + ((c >> 3) & 0x18e3));
   } else {
      uint16_t c = ((uint16_t *)row)[x];
      ((uint16_t *)row)[x] = (uint16_t)(((c >> 2) & 0x1ce7) + ((c >> 3) & 0x0c63));
   }
}

static void my_video(const void *data, unsigned w, unsigned hgt, size_t pitch)
{
   unsigned y, x, c, bh = 7;
   if (!fe_video)
      return;
   if (!mj_on || !data || data == RETRO_HW_FRAME_BUFFER_VALID || !show_bar || hgt < 40 || w < NCELL * 5) {
      fe_video(data, w, hgt, pitch);
      return;
   }
   if (fbuf_size < pitch * hgt) {
      free(fbuf);
      fbuf_size = pitch * hgt;
      fbuf = (uint8_t *)malloc(fbuf_size);
      if (!fbuf) { fbuf_size = 0; fe_video(data, w, hgt, pitch); return; }
   }
   memcpy(fbuf, data, pitch * hgt);
   for (c = 0; c < NCELL; c++) {
      unsigned x0 = c * w / NCELL, x1 = (c + 1) * w / NCELL;
      int sel = (int)c == cursor;
      uint32_t bg = sel ? 0xfeb713 : 0x0e0404, fg = sel ? 0x0e0404 : (bar_timer ? 0xfef4e6 : 0x9a8f80);
      for (y = hgt - bh; y < hgt; y++) {
         uint8_t *row = fbuf + pitch * y;
         for (x = x0; x < x1; x++) {
            if (x == x0)
               put(row, x, 0x0e0404);
            else if (sel)
               put(row, x, bg);
            else
               dim(row, x);
         }
      }
      {  /* 글자: 칸 가운데 3x5 */
         unsigned gx = x0 + (x1 - x0) / 2 - 1, gy = hgt - bh + 1, r, b;
         for (r = 0; r < 5; r++)
            for (b = 0; b < 3; b++)
               if (font[c][r] & (4 >> b))
                  put(fbuf + pitch * (gy + r), gx + b, fg);
      }
   }
   fe_video(fbuf, w, hgt, pitch);
}

static bool my_env(unsigned cmd, void *data)
{
   bool ok = fe_env ? fe_env(cmd, data) : false;
   if (cmd == RETRO_ENVIRONMENT_SET_PIXEL_FORMAT && ok && data)
      pixfmt = *(const enum retro_pixel_format *)data;
   return ok;
}

/* ---- libretro 겉 ---- */
RETRO_API void retro_set_environment(retro_environment_t cb) { load_real(); fe_env = cb; p_retro_set_environment(my_env); }
RETRO_API void retro_set_video_refresh(retro_video_refresh_t cb) { load_real(); fe_video = cb; p_retro_set_video_refresh(my_video); }
RETRO_API void retro_set_audio_sample(retro_audio_sample_t cb) { load_real(); p_retro_set_audio_sample(cb); }
RETRO_API void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { load_real(); p_retro_set_audio_sample_batch(cb); }
RETRO_API void retro_set_input_poll(retro_input_poll_t cb) { load_real(); fe_poll = cb; p_retro_set_input_poll(mj_poll); }
RETRO_API void retro_set_input_state(retro_input_state_t cb) { load_real(); fe_state = cb; p_retro_set_input_state(my_state); }
RETRO_API void retro_init(void) { load_real(); p_retro_init(); }
RETRO_API void retro_deinit(void) { p_retro_deinit(); free(fbuf); fbuf = NULL; fbuf_size = 0; }
RETRO_API unsigned retro_api_version(void) { load_real(); return p_retro_api_version(); }
RETRO_API void retro_get_system_info(struct retro_system_info *info) { load_real(); p_retro_get_system_info(info); }
RETRO_API void retro_get_system_av_info(struct retro_system_av_info *info) { p_retro_get_system_av_info(info); }
RETRO_API void retro_set_controller_port_device(unsigned port, unsigned device) { p_retro_set_controller_port_device(port, device); }
RETRO_API void retro_reset(void) { p_retro_reset(); }
RETRO_API void retro_run(void) { p_retro_run(); }
RETRO_API size_t retro_serialize_size(void) { return p_retro_serialize_size(); }
RETRO_API bool retro_serialize(void *data, size_t size) { return p_retro_serialize(data, size); }
RETRO_API bool retro_unserialize(const void *data, size_t size) { return p_retro_unserialize(data, size); }
RETRO_API void retro_cheat_reset(void) { p_retro_cheat_reset(); }
RETRO_API void retro_cheat_set(unsigned index, bool enabled, const char *code) { p_retro_cheat_set(index, enabled, code); }
RETRO_API bool retro_load_game(const struct retro_game_info *game) { return p_retro_load_game(game); }
RETRO_API bool retro_load_game_special(unsigned type, const struct retro_game_info *info, size_t num) { return p_retro_load_game_special(type, info, num); }
RETRO_API void retro_unload_game(void) { p_retro_unload_game(); }
RETRO_API unsigned retro_get_region(void) { return p_retro_get_region(); }
RETRO_API void *retro_get_memory_data(unsigned id) { return p_retro_get_memory_data(id); }
RETRO_API size_t retro_get_memory_size(unsigned id) { return p_retro_get_memory_size(id); }
