#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_http_client.h"
#include "esp_crt_bundle.h"
#include "cJSON.h"
#include "driver/i2c_master.h"
#include "bme280.h"
#include "pins.h"
#include "display.h"

static const char *TAG = "hava";
static EventGroupHandle_t wifi_events;
#define WIFI_CONNECTED_BIT BIT0

typedef struct {
    float temperature;
    float humidity;
    float wind;
    int code;
} weather_t;

static void wifi_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) {
        xEventGroupClearBits(wifi_events, WIFI_CONNECTED_BIT);
        esp_wifi_connect();
    } else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) {
        xEventGroupSetBits(wifi_events, WIFI_CONNECTED_BIT);
    }
}

static void wifi_start(void)
{
    wifi_events = xEventGroupCreate();
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_handler, NULL));
    ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_handler, NULL));
    wifi_config_t wc = { 0 };
    strncpy((char *)wc.sta.ssid, CONFIG_WIFI_SSID, sizeof(wc.sta.ssid) - 1);
    strncpy((char *)wc.sta.password, CONFIG_WIFI_PASSWORD, sizeof(wc.sta.password) - 1);
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wc));
    ESP_ERROR_CHECK(esp_wifi_start());
    xEventGroupWaitBits(wifi_events, WIFI_CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI(TAG, "Wi-Fi baglandi");
}

static esp_err_t fetch_weather(weather_t *out)
{
    char url[256];
    snprintf(url, sizeof(url),
        "https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        CONFIG_LATITUDE, CONFIG_LONGITUDE);

    esp_http_client_config_t cfg = {
        .url = url,
        .crt_bundle_attach = esp_crt_bundle_attach,
        .timeout_ms = 10000,
    };
    esp_http_client_handle_t c = esp_http_client_init(&cfg);
    esp_err_t err = esp_http_client_open(c, 0);
    if (err != ESP_OK) { esp_http_client_cleanup(c); return err; }

    esp_http_client_fetch_headers(c);
    char buf[1024];
    int n = esp_http_client_read_response(c, buf, sizeof(buf) - 1);
    esp_http_client_close(c);
    esp_http_client_cleanup(c);
    if (n <= 0) return ESP_FAIL;
    buf[n] = 0;

    cJSON *root = cJSON_Parse(buf);
    if (!root) return ESP_FAIL;
    cJSON *cur = cJSON_GetObjectItem(root, "current");
    if (!cur) { cJSON_Delete(root); return ESP_FAIL; }
    out->temperature = (float)cJSON_GetObjectItem(cur, "temperature_2m")->valuedouble;
    out->humidity    = (float)cJSON_GetObjectItem(cur, "relative_humidity_2m")->valuedouble;
    out->wind        = (float)cJSON_GetObjectItem(cur, "wind_speed_10m")->valuedouble;
    out->code        = cJSON_GetObjectItem(cur, "weather_code")->valueint;
    cJSON_Delete(root);
    return ESP_OK;
}

void app_main(void)
{
    esp_err_t r = nvs_flash_init();
    if (r == ESP_ERR_NVS_NO_FREE_PAGES || r == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        r = nvs_flash_init();
    }
    ESP_ERROR_CHECK(r);
    display_init();
    display_view_t view = { 0 };
    display_update(&view);
    wifi_start();

    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = PIN_I2C_SDA,
        .scl_io_num = PIN_I2C_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = false,
    };
    i2c_master_bus_handle_t bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));
    bool have_sensor = (bme280_init(bus, 0x76) == ESP_OK);
    if (!have_sensor) ESP_LOGW(TAG, "BME280 bulunamadi (0x76)");

    const int sensor_period_s = 10;
    int since_weather = CONFIG_REFRESH_SECONDS;
    for (;;) {
        if (have_sensor) {
            bme280_reading_t m;
            if (bme280_read(&m) == ESP_OK) {
                ESP_LOGI(TAG, "Oda: %.1f C | Nem %%%.0f | Basinc %.1f hPa",
                         m.temperature_c, m.humidity_pct, m.pressure_hpa);
                view.have_in = true;
                view.in_temp = m.temperature_c;
                view.in_hum = m.humidity_pct;
                view.in_pressure = m.pressure_hpa;
            }
        }
        if (since_weather >= CONFIG_REFRESH_SECONDS) {
            weather_t w;
            if (fetch_weather(&w) == ESP_OK) {
                ESP_LOGI(TAG, "Disari: %.1f C | Nem %%%.0f | Ruzgar %.1f km/h | Kod %d",
                         w.temperature, w.humidity, w.wind, w.code);
                view.have_out = true;
                view.out_temp = w.temperature;
                view.out_hum = w.humidity;
                view.out_wind = w.wind;
            } else {
                ESP_LOGW(TAG, "Hava verisi alinamadi");
            }
            since_weather = 0;
        }
        display_update(&view);
        vTaskDelay(pdMS_TO_TICKS(sensor_period_s * 1000));
        since_weather += sensor_period_s;
    }
}
