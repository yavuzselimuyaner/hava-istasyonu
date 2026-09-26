/* Hava sensor dugumu: olc -> MQTT (WebSocket/TLS) ile yayinla. Bir tarayici sayfasi (web/index.html) ayni konuyu dinler.
 * Sensor: BME280 (sensor karti) veya DHT22 (prototip). Kart: ESP32-C3 (ana kart) veya T-Display-S3 (prototip). */
#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "mqtt_client.h"
#include "esp_crt_bundle.h"
#include "sdkconfig.h"
#if CONFIG_SENSOR_BME280
#include "driver/i2c_master.h"
#include "bme280.h"
#else
#include "dht22.h"
#endif

static const char *TAG = "hava";
static EventGroupHandle_t s_events;
#define WIFI_UP BIT0
static volatile bool s_mqtt_up;

static void wifi_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (base == WIFI_EVENT && id == WIFI_EVENT_STA_START) esp_wifi_connect();
    else if (base == WIFI_EVENT && id == WIFI_EVENT_STA_DISCONNECTED) { xEventGroupClearBits(s_events, WIFI_UP); esp_wifi_connect(); }
    else if (base == IP_EVENT && id == IP_EVENT_STA_GOT_IP) xEventGroupSetBits(s_events, WIFI_UP);
}

static void wifi_start(void)
{
    s_events = xEventGroupCreate();
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
    xEventGroupWaitBits(s_events, WIFI_UP, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI(TAG, "Wi-Fi baglandi");
}

static void mqtt_handler(void *arg, esp_event_base_t base, int32_t id, void *data)
{
    if (id == MQTT_EVENT_CONNECTED) { s_mqtt_up = true; ESP_LOGI(TAG, "MQTT baglandi"); }
    else if (id == MQTT_EVENT_DISCONNECTED) { s_mqtt_up = false; ESP_LOGW(TAG, "MQTT koptu"); }
}

typedef struct { float t, h, p; bool has_p; } meas_t;

#if CONFIG_SENSOR_BME280
static bool sensor_init(void)
{
    i2c_master_bus_config_t bc = { .i2c_port = I2C_NUM_0, .sda_io_num = CONFIG_I2C_SDA, .scl_io_num = CONFIG_I2C_SCL,
                                   .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7 };
    i2c_master_bus_handle_t bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bc, &bus));
    bool ok = (bme280_init(bus, 0x76) == ESP_OK);
    if (!ok) ESP_LOGE(TAG, "BME280 bulunamadi (0x76): kablo ve pull-up'lari kontrol et");
    return ok;
}
static bool sensor_read(meas_t *m)
{
    bme280_reading_t r;
    if (bme280_read(&r) != ESP_OK) return false;
    m->t = r.temperature_c; m->h = r.humidity_pct; m->p = r.pressure_hpa; m->has_p = true;
    return true;
}
#else
static bool sensor_init(void) { vTaskDelay(pdMS_TO_TICKS(1500)); return true; }   /* DHT22: guc verdikten sonra 1 sn bekle */
static bool sensor_read(meas_t *m)
{
    m->has_p = false; m->p = 0;
    esp_err_t e = dht22_read(CONFIG_SENSOR_PIN, &m->t, &m->h);
    if (e != ESP_OK) ESP_LOGW(TAG, "DHT22 okunamadi: %s", esp_err_to_name(e));
    return e == ESP_OK;
}
#endif

void app_main(void)
{
    esp_err_t r = nvs_flash_init();
    if (r == ESP_ERR_NVS_NO_FREE_PAGES || r == ESP_ERR_NVS_NEW_VERSION_FOUND) { ESP_ERROR_CHECK(nvs_flash_erase()); r = nvs_flash_init(); }
    ESP_ERROR_CHECK(r);
    wifi_start();

    esp_mqtt_client_config_t mc = {
        .broker.address.uri = CONFIG_MQTT_URI,
        .broker.verification.crt_bundle_attach = esp_crt_bundle_attach,
        .credentials.username = CONFIG_MQTT_USER,
        .credentials.authentication.password = CONFIG_MQTT_PASS,
    };
    esp_mqtt_client_handle_t client = esp_mqtt_client_init(&mc);
    esp_mqtt_client_register_event(client, ESP_EVENT_ANY_ID, mqtt_handler, NULL);
    esp_mqtt_client_start(client);

    bool ok = sensor_init();
    for (;;) {
        meas_t m;
        if (ok && sensor_read(&m)) {
            char js[128];
            if (m.has_p) snprintf(js, sizeof(js), "{\"t\":%.2f,\"h\":%.1f,\"p\":%.1f}", m.t, m.h, m.p);
            else         snprintf(js, sizeof(js), "{\"t\":%.2f,\"h\":%.1f}", m.t, m.h);
            ESP_LOGI(TAG, "olcum: %s", js);
            if (s_mqtt_up) esp_mqtt_client_publish(client, CONFIG_MQTT_TOPIC, js, 0, 1, 1);   /* QoS1, retain: sayfa acilinca son degeri gorur */
            else ESP_LOGW(TAG, "MQTT bagli degil, yayin atlandi");
        }
        vTaskDelay(pdMS_TO_TICKS(CONFIG_PUBLISH_SECONDS * 1000));
    }
}
