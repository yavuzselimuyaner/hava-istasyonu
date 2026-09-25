/* PC demosu: firmware'in GERCEK display.c ve bme280_comp.c kodunu ESP32 olmadan calistirir.
 * Kullanim: host_demo out_t out_h out_wind have_out raw_P raw_T raw_H have_in screen.ppm */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#define HOST_TEST 1
#include "../main/display.c"
#include "../main/bme280_comp.c"

static uint16_t fb[LCD_W * LCD_H];

int esp_lcd_panel_draw_bitmap(esp_lcd_panel_handle_t p, int x0, int y0, int x1, int y1, const void *d)
{
    (void)p;
    const uint16_t *src = d;
    for (int y = y0; y < y1; y++)
        for (int x = x0; x < x1; x++)
            if (x >= 0 && y >= 0 && x < LCD_W && y < LCD_H) fb[y * LCD_W + x] = src[(y - y0) * (x1 - x0) + (x - x0)];
    return 0;
}

/* Bosch datasheet ornek kalibrasyon seti (gercek bir BME280'in yerine) */
static const bme280_calib_t CAL = {
    .T1 = 27504, .T2 = 26435, .T3 = -1000,
    .P1 = 36477, .P2 = -10685, .P3 = 3024, .P4 = 2855, .P5 = 140, .P6 = -7, .P7 = 15500, .P8 = -14600, .P9 = 6000,
    .H1 = 75, .H2 = 362, .H3 = 0, .H4 = 316, .H5 = 50, .H6 = 30,
};

int main(int argc, char **argv)
{
    if (argc < 10) { fprintf(stderr, "kullanim: out_t out_h out_wind have_out raw_P raw_T raw_H have_in screen.ppm\n"); return 2; }
    display_view_t v = { 0 };
    v.have_out = atoi(argv[4]); v.out_temp = atof(argv[1]); v.out_hum = atof(argv[2]); v.out_wind = atof(argv[3]);
    int32_t P = atoi(argv[5]), T = atoi(argv[6]), H = atoi(argv[7]);
    if (atoi(argv[8])) {
        uint8_t d[8] = { P >> 12, P >> 4, (P & 0xF) << 4, T >> 12, T >> 4, (T & 0xF) << 4, H >> 8, H };
        bme280_reading_t r; bme280_compensate(&CAL, d, &r);
        v.have_in = 1; v.in_temp = r.temperature_c; v.in_hum = r.humidity_pct; v.in_pressure = r.pressure_hpa;
    }
    /* display_init()'in cizim kismi */
    fill_rect(0, 0, LCD_W, LCD_H, COL_BG);
    fill_rect(0, 126, LCD_W, 1, COL_LINE);
    draw_text(8, 8, 3, COL_OUT, COL_BG, "DISARI");
    draw_text(8, 134, 3, COL_IN, COL_BG, "ODA");
    display_update(&v);
    FILE *f = fopen(argv[9], "wb");
    fprintf(f, "P6\n%d %d\n255\n", LCD_W, LCD_H);
    for (int i = 0; i < LCD_W * LCD_H; i++) {
        uint16_t c = (fb[i] >> 8) | (fb[i] << 8);
        uint8_t px[3] = { (c >> 11) << 3, ((c >> 5) & 0x3F) << 2, (c & 0x1F) << 3 };
        fwrite(px, 1, 3, f);
    }
    fclose(f);
    if (v.have_in) printf("ODA (sensor hesabi): %.2f C  %%%.1f nem  %.2f hPa\n", v.in_temp, v.in_hum, v.in_pressure);
    return 0;
}
