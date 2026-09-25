#include "bme280.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define REG_ID        0xD0
#define REG_RESET     0xE0
#define REG_CTRL_HUM  0xF2
#define REG_STATUS    0xF3
#define REG_CTRL_MEAS 0xF4
#define REG_CONFIG    0xF5
#define REG_DATA      0xF7

static i2c_master_dev_handle_t dev;
static bme280_calib_t cal;

static esp_err_t rd(uint8_t reg, uint8_t *buf, size_t n)
{
    return i2c_master_transmit_receive(dev, &reg, 1, buf, n, 100);
}

static esp_err_t wr(uint8_t reg, uint8_t val)
{
    uint8_t b[2] = { reg, val };
    return i2c_master_transmit(dev, b, 2, 100);
}

esp_err_t bme280_init(i2c_master_bus_handle_t bus, uint8_t addr)
{
    i2c_device_config_t cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = addr,
        .scl_speed_hz = 100000,
    };
    esp_err_t e = i2c_master_bus_add_device(bus, &cfg, &dev);
    if (e != ESP_OK) return e;

    uint8_t id;
    e = rd(REG_ID, &id, 1);
    if (e != ESP_OK) return e;
    if (id != 0x60) return ESP_ERR_NOT_SUPPORTED;   /* 0x58 = BMP280 (nem yok) */

    wr(REG_RESET, 0xB6);
    vTaskDelay(pdMS_TO_TICKS(5));

    uint8_t a[26], h[7];
    if ((e = rd(0x88, a, 26)) != ESP_OK) return e;
    if ((e = rd(0xE1, h, 7)) != ESP_OK) return e;
    bme280_parse_calib(a, h, &cal);
    return wr(REG_CONFIG, 0x00);
}

esp_err_t bme280_read(bme280_reading_t *out)
{
    esp_err_t e;
    if ((e = wr(REG_CTRL_HUM, 0x01)) != ESP_OK) return e;    /* nem x1 */
    if ((e = wr(REG_CTRL_MEAS, 0x25)) != ESP_OK) return e;   /* sicaklik x1, basinc x1, forced */

    uint8_t st = 0x08;
    for (int i = 0; i < 20 && (st & 0x08); i++) {
        vTaskDelay(pdMS_TO_TICKS(5));
        if ((e = rd(REG_STATUS, &st, 1)) != ESP_OK) return e;
    }

    uint8_t d[8];
    if ((e = rd(REG_DATA, d, 8)) != ESP_OK) return e;
    bme280_compensate(&cal, d, out);
    return ESP_OK;
}
