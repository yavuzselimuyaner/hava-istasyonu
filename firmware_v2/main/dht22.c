#include "dht22.h"
#include "dht22_comp.h"
#include "driver/gpio.h"
#include "esp_rom_sys.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

/* Tek telli okuma. DONANIMDA TEST EDILMEDI. Zamanlama: DHT22/AM2302 datasheet (baslangic >=800 us low). */
static int wait_level(gpio_num_t pin, int level, int timeout_us)
{
    int64_t t0 = esp_timer_get_time();
    while (gpio_get_level(pin) != level) {
        if (esp_timer_get_time() - t0 > timeout_us) return -1;
    }
    return (int)(esp_timer_get_time() - t0);
}

esp_err_t dht22_read(int gpio, float *temp_c, float *hum_pct)
{
    gpio_num_t pin = (gpio_num_t)gpio;
    uint8_t d[5] = { 0 };
    static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

    gpio_set_direction(pin, GPIO_MODE_INPUT_OUTPUT_OD);
    gpio_set_pull_mode(pin, GPIO_PULLUP_ONLY);
    gpio_set_level(pin, 1);
    vTaskDelay(pdMS_TO_TICKS(20));

    esp_err_t err = ESP_OK;
    portENTER_CRITICAL(&mux);
    gpio_set_level(pin, 0);
    esp_rom_delay_us(1500);                 /* >= 800 us */
    gpio_set_level(pin, 1);
    esp_rom_delay_us(30);
    if (wait_level(pin, 0, 100) < 0 || wait_level(pin, 1, 120) < 0 || wait_level(pin, 0, 120) < 0) {
        err = ESP_ERR_TIMEOUT;
    } else {
        for (int i = 0; i < 40 && err == ESP_OK; i++) {
            if (wait_level(pin, 1, 100) < 0) { err = ESP_ERR_TIMEOUT; break; }
            int high = wait_level(pin, 0, 120);
            if (high < 0) { err = ESP_ERR_TIMEOUT; break; }
            d[i / 8] <<= 1;
            if (high > 40) d[i / 8] |= 1;   /* ~27 us = 0, ~70 us = 1 */
        }
    }
    portEXIT_CRITICAL(&mux);
    if (err != ESP_OK) return err;
    return dht22_decode(d, temp_c, hum_pct) ? ESP_OK : ESP_ERR_INVALID_CRC;
}
