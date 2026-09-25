#pragma once
#include <stdint.h>
#include <stdbool.h>
/* d = 5 bayt: nem H, nem L, sicaklik H, sicaklik L, toplam. Toplam dogruysa true. */
bool dht22_decode(const uint8_t d[5], float *temp_c, float *hum_pct);
