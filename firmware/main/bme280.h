#pragma once
#include <stdint.h>
#include "esp_err.h"
#include "driver/i2c_master.h"
#include "bme280_comp.h"

esp_err_t bme280_init(i2c_master_bus_handle_t bus, uint8_t addr);
esp_err_t bme280_read(bme280_reading_t *out);
