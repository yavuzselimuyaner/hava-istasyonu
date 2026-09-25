#include "display.h"
#include <stdio.h>
#include <string.h>
#ifdef HOST_TEST
typedef void *esp_lcd_panel_handle_t;
#define ESP_OK 0
int esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t p, int x0, int y0, int x1, int y1, const void *d);
#else
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_vendor.h"
#include "esp_lcd_panel_st7789.h"
#endif
#include "font5x7.h"
#include "pins.h"

#define LCD_W 240
#define LCD_H 240
#define LCD_SPI_HOST SPI2_HOST
#define LCD_INVERT   true    /* IPS ST7789 modulleri genelde ters renk ister; modulde renkler tersse false yap */
#define LCD_X_GAP    0
#define LCD_Y_GAP    0       /* 240x240 modulde ekran kayiksa 80 dene */
#define MAX_SCALE    6

static esp_lcd_panel_handle_t panel;
static uint16_t glyph_buf[(6 * MAX_SCALE) * (7 * MAX_SCALE)];
static uint16_t line_buf[LCD_W];

static uint16_t rgb(uint8_t r, uint8_t g, uint8_t b)
{
    uint16_t c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3);
    return (c >> 8) | (c << 8);      /* SPI: yuksek bayt once */
}

#define COL_BG    rgb(0, 0, 0)
#define COL_OUT   rgb(80, 200, 255)
#define COL_IN    rgb(255, 190, 60)
#define COL_TEXT  rgb(230, 230, 230)
#define COL_LINE  rgb(80, 80, 80)

static void fill_rect(int x, int y, int w, int h, uint16_t col)
{
    for (int i = 0; i < w; i++) line_buf[i] = col;
    for (int r = 0; r < h; r++)
        esp_lcd_panel_draw_bitmap(panel, x, y + r, x + w, y + r + 1, line_buf);
}

static void draw_char(int x, int y, int scale, uint16_t fg, uint16_t bg, char ch)
{
    const uint8_t *cols = NULL;
    if (ch >= 'a' && ch <= 'z') ch -= 32;
    if (ch >= FONT_FIRST && ch <= FONT_LAST) cols = font5x7[ch - FONT_FIRST];
    int w = 6 * scale, h = 7 * scale;
    for (int py = 0; py < h; py++) {
        for (int px = 0; px < w; px++) {
            int cx = px / scale, cy = py / scale;
            bool on = cols && cx < 5 && (cols[cx] & (1 << cy));
            glyph_buf[py * w + px] = on ? fg : bg;
        }
    }
    esp_lcd_panel_draw_bitmap(panel, x, y, x + w, y + h, glyph_buf);
}

static void draw_text(int x, int y, int scale, uint16_t fg, uint16_t bg, const char *s)
{
    for (; *s; s++, x += 6 * scale) {
        if (x + 6 * scale > LCD_W) break;
        draw_char(x, y, scale, fg, bg, *s);
    }
}

#ifndef HOST_TEST
esp_err_t display_init(void)
{
    gpio_config_t bl = { .pin_bit_mask = 1ULL << PIN_LCD_BL, .mode = GPIO_MODE_OUTPUT };
    ESP_ERROR_CHECK(gpio_config(&bl));
    gpio_set_level(PIN_LCD_BL, 0);

    spi_bus_config_t bus = {
        .mosi_io_num = PIN_LCD_MOSI,
        .miso_io_num = -1,
        .sclk_io_num = PIN_LCD_SCK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 6 * MAX_SCALE * 7 * MAX_SCALE * 2 + 8,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(LCD_SPI_HOST, &bus, SPI_DMA_CH_AUTO));

    esp_lcd_panel_io_handle_t io;
    esp_lcd_panel_io_spi_config_t io_cfg = {
        .dc_gpio_num = PIN_LCD_DC,
        .cs_gpio_num = PIN_LCD_CS,
        .pclk_hz = 20 * 1000 * 1000,
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
        .spi_mode = 0,
        .trans_queue_depth = 10,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)LCD_SPI_HOST, &io_cfg, &io));

    esp_lcd_panel_dev_config_t pcfg = {
        .reset_gpio_num = PIN_LCD_RST,
        .rgb_ele_order = LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel = 16,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(io, &pcfg, &panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_invert_color(panel, LCD_INVERT));
    ESP_ERROR_CHECK(esp_lcd_panel_set_gap(panel, LCD_X_GAP, LCD_Y_GAP));
    ESP_ERROR_CHECK(esp_lcd_panel_disp_on_off(panel, true));

    fill_rect(0, 0, LCD_W, LCD_H, COL_BG);
    fill_rect(0, 126, LCD_W, 1, COL_LINE);
    draw_text(8, 8, 3, COL_OUT, COL_BG, "DISARI");
    draw_text(8, 134, 3, COL_IN, COL_BG, "ODA");
    gpio_set_level(PIN_LCD_BL, 1);
    return ESP_OK;
}

#endif

static void value_line(int y, int scale, uint16_t fg, bool ok, float v, const char *unit)
{
    char buf[16];
    if (ok) snprintf(buf, sizeof(buf), "%.1f^%s", v, unit);
    else    snprintf(buf, sizeof(buf), "--");
    fill_rect(0, y, LCD_W, 7 * scale, COL_BG);
    draw_text(8, y, scale, fg, COL_BG, buf);
}

static void info_line(int y, const char *text)
{
    fill_rect(0, y, LCD_W, 14, COL_BG);
    draw_text(8, y, 2, COL_TEXT, COL_BG, text);
}

void display_update(const display_view_t *v)
{
    char b[32];
    value_line(36, 5, COL_OUT, v->have_out, v->out_temp, "C");
    if (v->have_out) {
        snprintf(b, sizeof(b), "NEM %.0f%%", v->out_hum);
        info_line(84, b);
        snprintf(b, sizeof(b), "RUZGAR %.0f KM/H", v->out_wind);
        info_line(104, b);
    } else {
        info_line(84, "NEM --");
        info_line(104, "RUZGAR --");
    }
    value_line(160, 5, COL_IN, v->have_in, v->in_temp, "C");
    if (v->have_in) {
        snprintf(b, sizeof(b), "NEM %.0f%% %.0f HPA", v->in_hum, v->in_pressure);
        info_line(210, b);
    } else {
        info_line(210, "SENSOR YOK");
    }
}
