#include "dht22_comp.h"

bool dht22_decode(const uint8_t d[5], float *temp_c, float *hum_pct)
{
    uint8_t sum = (uint8_t)(d[0] + d[1] + d[2] + d[3]);
    if (sum != d[4]) return false;
    *hum_pct = (float)(((uint16_t)d[0] << 8) | d[1]) / 10.0f;
    int raw = ((d[2] & 0x7F) << 8) | d[3];
    *temp_c = (float)raw / 10.0f;
    if (d[2] & 0x80) *temp_c = -*temp_c;
    return true;
}
