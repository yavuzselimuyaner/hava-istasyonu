#pragma once
#include "esp_err.h"
esp_err_t dht22_read(int gpio, float *temp_c, float *hum_pct);
