#pragma once
#include <stdint.h>

typedef struct {
    float temperature_c;
    float pressure_hpa;
    float humidity_pct;
} bme280_reading_t;

typedef struct {
    uint16_t T1; int16_t T2, T3;
    uint16_t P1; int16_t P2, P3, P4, P5, P6, P7, P8, P9;
    uint8_t H1, H3; int16_t H2, H4, H5; int8_t H6;
} bme280_calib_t;

/* a = 0x88..0xA1 (26 bayt), h = 0xE1..0xE7 (7 bayt) */
void bme280_parse_calib(const uint8_t a[26], const uint8_t h[7], bme280_calib_t *c);
/* d = 0xF7..0xFE (8 bayt: basinc, sicaklik, nem) */
void bme280_compensate(const bme280_calib_t *c, const uint8_t d[8], bme280_reading_t *out);
