/* Ekran cizim kodunu donanimsiz calistirir: gcc -DHOST_TEST ... && render out.ppm */
#include <stdio.h>
#include <stdint.h>
#define HOST_TEST 1
#include "../../main/display.c"

static uint16_t fb[LCD_W * LCD_H];

int esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t p, int x0, int y0, int x1, int y1, const void *d)
{
    (void)p;
    const uint16_t *src = d;
    for (int y = y0; y < y1; y++)
        for (int x = x0; x < x1; x++) {
            if (x < 0 || y < 0 || x >= LCD_W || y >= LCD_H) { fprintf(stderr, "TASMA %d,%d\n", x, y); continue; }
            fb[y * LCD_W + x] = src[(y - y0) * (x1 - x0) + (x - x0)];
        }
    return 0;
}

static void dump(const char *path)
{
    FILE *f = fopen(path, "wb");
    fprintf(f, "P6\n%d %d\n255\n", LCD_W, LCD_H);
    for (int i = 0; i < LCD_W * LCD_H; i++) {
        uint16_t c = (fb[i] >> 8) | (fb[i] << 8);
        uint8_t px[3] = { (c >> 11) << 3, ((c >> 5) & 0x3F) << 2, (c & 0x1F) << 3 };
        fwrite(px, 1, 3, f);
    }
    fclose(f);
}

int main(void)
{
    /* display_init()'in cizim kismini taklit et */
    fill_rect(0, 0, LCD_W, LCD_H, COL_BG);
    fill_rect(0, 126, LCD_W, 1, COL_LINE);
    draw_text(8, 8, 3, COL_OUT, COL_BG, "DISARI");
    draw_text(8, 134, 3, COL_IN, COL_BG, "ODA");

    display_view_t v = { .have_out = true, .out_temp = 18.5f, .out_hum = 65, .out_wind = 12,
                         .have_in = true, .in_temp = 24.3f, .in_hum = 45, .in_pressure = 1013.2f };
    display_update(&v);
    dump("view_full.ppm");

    display_view_t e = { 0 };
    display_update(&e);
    dump("view_empty.ppm");

    v.out_temp = -12.5f; v.in_temp = 100.0f; v.out_wind = 105; v.in_pressure = 998.0f;
    display_update(&v);
    dump("view_extreme.ppm");
    return 0;
}
