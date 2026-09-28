/* display.c: T-Display-S3'un dahili ekrani (ST7789, 170x320, paralel 8 bit i80 arayuzu).
 * Yalnizca CONFIG_DISPLAY_ST7789 acikken derlenir (bu ekran ana kartta yok, yalnizca T-Display-S3
 * gelistirme kartinda var). Pin numaralari ve gap/swap/mirror ayarlari LilyGO'nun resmi
 * T-Display-S3 ornek projesinden (examples/factory) alindi: https://github.com/Xinyuan-LilyGO/T-Display-S3
 *
 * Font kutuphanesi kullanilmiyor: rakamlar ve C/H/P harfleri 7 parcali gosterge (7-segment) gibi
 * dikdortgenlerle ciziliyor. Bu satirlik olcum degerleri (orn. "22.4C") icin yeterli. */
#include "display.h"
#include "sdkconfig.h"

#if CONFIG_DISPLAY_ST7789
#include <stdio.h>
#include <stdlib.h>
#include "driver/gpio.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_ops.h"
#include "esp_log.h"

/* LilyGO T-Display-S3 pin haritasi (paralel LCD arayuzu) */
#define PIN_D0  39
#define PIN_D1  40
#define PIN_D2  41
#define PIN_D3  42
#define PIN_D4  45
#define PIN_D5  46
#define PIN_D6  47
#define PIN_D7  48
#define PIN_WR  8
#define PIN_RD  9
#define PIN_DC  7
#define PIN_CS  6
#define PIN_RST 5
#define PIN_BL  38
#define PIN_PWR 15     /* cevre birimleri (ekran dahil) bu pin HIGH olmadan calismiyor */

#define LCD_W 320      /* swap_xy+mirror sonrasi yatay (landscape) gorunum */
#define LCD_H 170
#define COLOR_BG 0x0000
#define COLOR_FG 0x07E0   /* RGB565 yesil */

static const char *TAG = "display";
static esp_lcd_panel_handle_t s_panel;
static uint16_t *s_buf;       /* yeniden kullanilan cizim tamponu, en buyuk ihtiyaca gore ayrilir */

/* 7 parcali gosterge duzeni:
 *    _a_
 *   f   b
 *    _g_
 *   e   c
 *    _d_
 */
#define SEG_A (1 << 0)
#define SEG_B (1 << 1)
#define SEG_C (1 << 2)
#define SEG_D (1 << 3)
#define SEG_E (1 << 4)
#define SEG_F (1 << 5)
#define SEG_G (1 << 6)

static uint8_t seg_pattern(char c)
{
    switch (c) {
        case '0': return SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F;
        case '1': return SEG_B | SEG_C;
        case '2': return SEG_A | SEG_B | SEG_G | SEG_E | SEG_D;
        case '3': return SEG_A | SEG_B | SEG_G | SEG_C | SEG_D;
        case '4': return SEG_F | SEG_G | SEG_B | SEG_C;
        case '5': return SEG_A | SEG_F | SEG_G | SEG_C | SEG_D;
        case '6': return SEG_A | SEG_F | SEG_G | SEG_E | SEG_C | SEG_D;
        case '7': return SEG_A | SEG_B | SEG_C;
        case '8': return SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G;
        case '9': return SEG_A | SEG_B | SEG_C | SEG_D | SEG_F | SEG_G;
        case 'C': return SEG_A | SEG_F | SEG_E | SEG_D;
        case 'H': return SEG_F | SEG_E | SEG_G | SEG_B | SEG_C;
        case 'P': return SEG_A | SEG_F | SEG_G | SEG_B | SEG_E;
        case '-': return SEG_G;
        default:  return 0;   /* bosluk: hicbir parca yanmaz */
    }
}

#define CW 34   /* karakter kutusu genisligi */
#define CH 46   /* karakter kutusu yuksekligi (satir yuksekligi 170/3=56, ortalamak icin CH<56) */
#define ST 6    /* parca kalinligi */
#define ROW_H (LCD_H / 3)

static void fill_rect(int x, int y, int w, int h, uint16_t color)
{
    if (w <= 0 || h <= 0) return;
    for (int i = 0; i < w * h; i++) s_buf[i] = color;   /* s_buf her zaman en az LCD_W*ROW_H buyuklugunde */
    esp_lcd_panel_draw_bitmap(s_panel, x, y, x + w, y + h, s_buf);
}

static void draw_char(int x0, int y0, char c, uint16_t color)
{
    if (c == '.') { fill_rect(x0 + 4, y0 + CH - ST, ST, ST, color); return; }
    uint8_t seg = seg_pattern(c);
    int hw = CW - 2 * ST;                 /* yatay parca uzunlugu */
    int vh = (CH - 3 * ST) / 2;           /* dikey parca uzunlugu (ust/alt yari) */
    if (seg & SEG_A) fill_rect(x0 + ST, y0, hw, ST, color);
    if (seg & SEG_G) fill_rect(x0 + ST, y0 + ST + vh, hw, ST, color);
    if (seg & SEG_D) fill_rect(x0 + ST, y0 + 2 * ST + 2 * vh, hw, ST, color);
    if (seg & SEG_F) fill_rect(x0, y0 + ST, ST, vh, color);
    if (seg & SEG_E) fill_rect(x0, y0 + 2 * ST + vh, ST, vh, color);
    if (seg & SEG_B) fill_rect(x0 + CW - ST, y0 + ST, ST, vh, color);
    if (seg & SEG_C) fill_rect(x0 + CW - ST, y0 + 2 * ST + vh, ST, vh, color);
}

static void draw_line(int row, const char *text, uint16_t color)
{
    int y = row * ROW_H;
    fill_rect(0, y, LCD_W, ROW_H, COLOR_BG);    /* onceki degeri temizle */
    int x = 4, y0 = y + (ROW_H - CH) / 2;
    for (const char *p = text; *p; p++) {
        draw_char(x, y0, *p, color);
        x += (*p == '.') ? (CW / 2) : CW;
    }
}

void display_init(void)
{
    gpio_config_t pwr_cfg = { .pin_bit_mask = 1ULL << PIN_PWR, .mode = GPIO_MODE_OUTPUT };
    gpio_config(&pwr_cfg);
    gpio_set_level(PIN_PWR, 1);

    gpio_config_t rd_cfg = { .pin_bit_mask = 1ULL << PIN_RD, .mode = GPIO_MODE_OUTPUT };
    gpio_config(&rd_cfg);
    gpio_set_level(PIN_RD, 1);      /* yazma-yalnizca kullanim: RD hep yuksek tutulur */

    gpio_config_t bl_cfg = { .pin_bit_mask = 1ULL << PIN_BL, .mode = GPIO_MODE_OUTPUT };
    gpio_config(&bl_cfg);
    gpio_set_level(PIN_BL, 1);

    esp_lcd_i80_bus_handle_t bus;
    esp_lcd_i80_bus_config_t bus_cfg = {
        .dc_gpio_num = PIN_DC, .wr_gpio_num = PIN_WR, .clk_src = LCD_CLK_SRC_DEFAULT,
        .data_gpio_nums = { PIN_D0, PIN_D1, PIN_D2, PIN_D3, PIN_D4, PIN_D5, PIN_D6, PIN_D7 },
        .bus_width = 8, .max_transfer_bytes = LCD_W * ROW_H * sizeof(uint16_t),
    };
    ESP_ERROR_CHECK(esp_lcd_new_i80_bus(&bus_cfg, &bus));

    esp_lcd_panel_io_handle_t io;
    esp_lcd_panel_io_i80_config_t io_cfg = {
        .cs_gpio_num = PIN_CS, .pclk_hz = 10 * 1000 * 1000, .trans_queue_depth = 10,
        .dc_levels = { .dc_idle_level = 0, .dc_cmd_level = 0, .dc_dummy_level = 0, .dc_data_level = 1 },
        .lcd_cmd_bits = 8, .lcd_param_bits = 8,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_i80(bus, &io_cfg, &io));

    esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = PIN_RST,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,  /* IDF < 5.1 ise bu alan yerine .color_space kullanilir */
        .bits_per_pixel = 16,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(io, &panel_cfg, &s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(s_panel, true));
    ESP_ERROR_CHECK(esp_lcd_panel_swap_xy(s_panel, true));
    ESP_ERROR_CHECK(esp_lcd_panel_mirror(s_panel, false, true));
    ESP_ERROR_CHECK(esp_lcd_panel_set_gap(s_panel, 0, 35));   /* LilyGO'nun resmi ornegindeki deger */
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(s_panel, true));

    s_buf = malloc(LCD_W * ROW_H * sizeof(uint16_t));
    if (!s_buf) { ESP_LOGE(TAG, "cizim tamponu ayrilamadi"); return; }
    fill_rect(0, 0, LCD_W, LCD_H, COLOR_BG);
    ESP_LOGI(TAG, "ekran hazir (%dx%d)", LCD_W, LCD_H);
}

void display_show(float t, float h, float p, bool has_p)
{
    if (!s_buf) return;
    char line[16];
    snprintf(line, sizeof(line), "%.1fC", t); draw_line(0, line, COLOR_FG);
    snprintf(line, sizeof(line), "%.0fH", h); draw_line(1, line, COLOR_FG);
    if (has_p) { snprintf(line, sizeof(line), "%.0fP", p); draw_line(2, line, COLOR_FG); }
}

#else  /* CONFIG_DISPLAY_ST7789 kapali: cagrilar zararsiz sekilde hicbir sey yapmaz */
void display_init(void) {}
void display_show(float t, float h, float p, bool has_p) { (void)t; (void)h; (void)p; (void)has_p; }
#endif
