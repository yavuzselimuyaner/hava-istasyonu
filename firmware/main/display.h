#pragma once
#include <stdbool.h>
#ifdef HOST_TEST
typedef int esp_err_t;
#else
#include "esp_err.h"
#endif

typedef struct {
    bool have_out;
    float out_temp, out_hum, out_wind;
    bool have_in;
    float in_temp, in_hum, in_pressure;
} display_view_t;

esp_err_t display_init(void);
void display_update(const display_view_t *v);
