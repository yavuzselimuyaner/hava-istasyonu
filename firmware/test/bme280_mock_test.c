/* BME280 surucusunu SANAL SENSORE karsi calistirir (donanimsiz). Sanal sensor Bosch datasheet register haritasina gore davranir:
 * chip id 0xD0, kalibrasyon 0x88.., 0xE1.., ctrl_hum 0xF2 (ctrl_meas yazilana kadar gecerli olmaz), ctrl_meas 0xF4 (forced mod), status 0xF3, veri 0xF7..0xFE. */
#include <stdio.h>
#include <string.h>
#include <math.h>
#include "../main/bme280.c"
#include "../main/bme280_comp.c"

static uint8_t reg[256];
static int log_n; static uint8_t log_reg[64], log_val[64];
static int measuring_polls;
static int chip_id = 0x60;
static int addr_seen;

void vTaskDelay(int t) { (void)t; }
esp_err_t i2c_master_bus_add_device(i2c_master_bus_handle_t b, const i2c_device_config_t *c, i2c_master_dev_handle_t *d) { (void)b; addr_seen = c->device_address; *d = (void *)1; return ESP_OK; }
esp_err_t i2c_master_transmit(i2c_master_dev_handle_t d, const uint8_t *buf, size_t n, int t)
{
    (void)d; (void)t;
    if (n != 2) return ESP_FAIL;
    log_reg[log_n] = buf[0]; log_val[log_n++] = buf[1];
    reg[buf[0]] = buf[1];
    if (buf[0] == 0xE0 && buf[1] == 0xB6) { /* soft reset */ }
    if (buf[0] == 0xF4 && (buf[1] & 3) == 1) measuring_polls = 2;      /* forced mod: 2 sorguluk olcum suresi */
    return ESP_OK;
}
esp_err_t i2c_master_transmit_receive(i2c_master_dev_handle_t d, const uint8_t *w, size_t wn, uint8_t *r, size_t rn, int t)
{
    (void)d; (void)t; if (wn != 1) return ESP_FAIL;
    uint8_t a = w[0];
    if (a == 0xD0) { r[0] = (uint8_t)chip_id; return ESP_OK; }
    if (a == 0xF3) { r[0] = measuring_polls > 0 ? 0x08 : 0x00; if (measuring_polls > 0) measuring_polls--; return ESP_OK; }
    for (size_t i = 0; i < rn; i++) r[i] = reg[a + i];
    return ESP_OK;
}

int main(void)
{
    int fail = 0;
    /* Bosch datasheet ornek kalibrasyon seti (bme_test.c ile ayni) ve ornek ham veri */
    static const int16_t T[3] = { 0, 26435, -1000 }; (void)T;
    uint8_t a[26] = { 0 }, h[7] = { 0 };
    a[0] = 27504 & 255; a[1] = 27504 >> 8; a[2] = 26435 & 255; a[3] = 26435 >> 8; a[4] = (uint16_t)-1000 & 255; a[5] = (uint16_t)-1000 >> 8;
    a[6] = 36477 & 255; a[7] = 36477 >> 8;
    int16_t p[8] = { -10685, 3024, 2855, 140, -7, 15500, -14600, 6000 };
    for (int i = 0; i < 8; i++) { a[8 + 2 * i] = (uint16_t)p[i] & 255; a[9 + 2 * i] = (uint16_t)p[i] >> 8; }
    a[25] = 75; h[0] = 362 & 255; h[1] = 362 >> 8; h[2] = 0; h[3] = 316 >> 4; h[4] = (316 & 15) | ((50 & 15) << 4); h[5] = 50 >> 4; h[6] = 30;
    memcpy(&reg[0x88], a, 26); memcpy(&reg[0xE1], h, 7);
    int32_t P = 415148, Tm = 519888, H = 30000;
    uint8_t d[8] = { P >> 12, P >> 4, (P & 0xF) << 4, Tm >> 12, Tm >> 4, (Tm & 0xF) << 4, H >> 8, H };
    memcpy(&reg[0xF7], d, 8);

    if (bme280_init((i2c_master_bus_handle_t)1, 0x76) != ESP_OK) { printf("HATA: init basarisiz\n"); fail = 1; }
    if (addr_seen != 0x76) { printf("HATA: adres 0x%02X\n", addr_seen); fail = 1; }
    log_n = 0;
    bme280_reading_t m;
    if (bme280_read(&m) != ESP_OK) { printf("HATA: read basarisiz\n"); fail = 1; }
    printf("okuma: %.2f C  %%%.1f  %.2f hPa\n", m.temperature_c, m.humidity_pct, m.pressure_hpa);
    if (fabs(m.temperature_c - 25.08) > 0.01 || fabs(m.pressure_hpa - 1006.53) > 0.02) { printf("HATA: deger beklenenle uyusmuyor\n"); fail = 1; }
    /* yazma sirasi: ctrl_hum (0xF2) ctrl_meas'ten (0xF4) ONCE olmali (datasheet: nem ayari ctrl_meas yazilinca gecerli olur) */
    int i_hum = -1, i_meas = -1;
    for (int i = 0; i < log_n; i++) { if (log_reg[i] == 0xF2 && i_hum < 0) i_hum = i; if (log_reg[i] == 0xF4 && i_meas < 0) i_meas = i; }
    if (i_hum < 0 || i_meas < 0 || i_hum > i_meas) { printf("HATA: yazma sirasi yanlis (ctrl_hum, ctrl_meas'ten once olmali)\n"); fail = 1; } else printf("yazma sirasi OK: 0xF2 (nem) sonra 0xF4 (forced mod)\n");
    if (reg[0xF4] != 0x25) { printf("HATA: ctrl_meas=0x%02X, beklenen 0x25\n", reg[0xF4]); fail = 1; }
    /* BMP280 (chip id 0x58, nem yok) reddedilmeli */
    chip_id = 0x58;
    if (bme280_init((i2c_master_bus_handle_t)1, 0x76) == ESP_OK) { printf("HATA: BMP280 kabul edildi\n"); fail = 1; } else printf("chip id 0x58 (BMP280) reddedildi OK\n");
    printf(fail ? "SONUC: BASARISIZ\n" : "SONUC: GECTI\n"); return fail;
}
