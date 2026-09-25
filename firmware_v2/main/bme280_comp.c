#include "bme280_comp.h"

void bme280_parse_calib(const uint8_t a[26], const uint8_t h[7], bme280_calib_t *c)
{
    c->T1 = a[0] | (a[1] << 8);
    c->T2 = (int16_t)(a[2] | (a[3] << 8));
    c->T3 = (int16_t)(a[4] | (a[5] << 8));
    c->P1 = a[6] | (a[7] << 8);
    c->P2 = (int16_t)(a[8] | (a[9] << 8));
    c->P3 = (int16_t)(a[10] | (a[11] << 8));
    c->P4 = (int16_t)(a[12] | (a[13] << 8));
    c->P5 = (int16_t)(a[14] | (a[15] << 8));
    c->P6 = (int16_t)(a[16] | (a[17] << 8));
    c->P7 = (int16_t)(a[18] | (a[19] << 8));
    c->P8 = (int16_t)(a[20] | (a[21] << 8));
    c->P9 = (int16_t)(a[22] | (a[23] << 8));
    c->H1 = a[25];
    c->H2 = (int16_t)(h[0] | (h[1] << 8));
    c->H3 = h[2];
    c->H4 = (int16_t)(((int8_t)h[3] << 4) | (h[4] & 0x0F));
    c->H5 = (int16_t)(((int8_t)h[5] << 4) | (h[4] >> 4));
    c->H6 = (int8_t)h[6];
}

void bme280_compensate(const bme280_calib_t *c, const uint8_t d[8], bme280_reading_t *out)
{
    int32_t adc_P = ((int32_t)d[0] << 12) | ((int32_t)d[1] << 4) | (d[2] >> 4);
    int32_t adc_T = ((int32_t)d[3] << 12) | ((int32_t)d[4] << 4) | (d[5] >> 4);
    int32_t adc_H = ((int32_t)d[6] << 8) | d[7];

    int32_t v1 = ((((adc_T >> 3) - ((int32_t)c->T1 << 1))) * (int32_t)c->T2) >> 11;
    int32_t v2 = (((((adc_T >> 4) - (int32_t)c->T1) * ((adc_T >> 4) - (int32_t)c->T1)) >> 12) * (int32_t)c->T3) >> 14;
    int32_t t_fine = v1 + v2;
    out->temperature_c = ((t_fine * 5 + 128) >> 8) / 100.0f;

    int64_t p1 = (int64_t)t_fine - 128000;
    int64_t p2 = p1 * p1 * (int64_t)c->P6;
    p2 += (p1 * (int64_t)c->P5) << 17;
    p2 += ((int64_t)c->P4) << 35;
    p1 = ((p1 * p1 * (int64_t)c->P3) >> 8) + ((p1 * (int64_t)c->P2) << 12);
    p1 = (((((int64_t)1) << 47) + p1)) * (int64_t)c->P1 >> 33;
    if (p1 == 0) {
        out->pressure_hpa = 0;
    } else {
        int64_t p = 1048576 - adc_P;
        p = (((p << 31) - p2) * 3125) / p1;
        p1 = (((int64_t)c->P9) * (p >> 13) * (p >> 13)) >> 25;
        p2 = (((int64_t)c->P8) * p) >> 19;
        p = ((p + p1 + p2) >> 8) + (((int64_t)c->P7) << 4);
        out->pressure_hpa = (float)p / 256.0f / 100.0f;
    }

    int32_t x = t_fine - 76800;
    x = (((((adc_H << 14) - (((int32_t)c->H4) << 20) - (((int32_t)c->H5) * x)) + 16384) >> 15) *
         (((((((x * (int32_t)c->H6) >> 10) * (((x * (int32_t)c->H3) >> 11) + 32768)) >> 10) + 2097152) *
           (int32_t)c->H2 + 8192) >> 14));
    x = x - (((((x >> 15) * (x >> 15)) >> 7) * (int32_t)c->H1) >> 4);
    if (x < 0) x = 0;
    if (x > 419430400) x = 419430400;
    out->humidity_pct = (float)(x >> 12) / 1024.0f;
}
