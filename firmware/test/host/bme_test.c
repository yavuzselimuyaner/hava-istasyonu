/* BME280 kompanzasyon testi: tamsayi (firmware) vs Bosch cift-hassasiyet referansi + datasheet ornegi. */
#include <stdio.h>
#include <math.h>
#include <string.h>
#include "../../main/bme280_comp.c"

static const bme280_calib_t C = {
    .T1 = 27504, .T2 = 26435, .T3 = -1000,
    .P1 = 36477, .P2 = -10685, .P3 = 3024, .P4 = 2855, .P5 = 140, .P6 = -7, .P7 = 15500, .P8 = -14600, .P9 = 6000,
    .H1 = 75, .H2 = 362, .H3 = 0, .H4 = 316, .H5 = 50, .H6 = 30,
};

static void pack_calib(uint8_t a[26], uint8_t h[7])
{
    memset(a, 0, 26);
    a[0] = C.T1; a[1] = C.T1 >> 8; a[2] = C.T2; a[3] = C.T2 >> 8; a[4] = C.T3; a[5] = C.T3 >> 8;
    a[6] = C.P1; a[7] = C.P1 >> 8;
    int16_t p[8] = { C.P2, C.P3, C.P4, C.P5, C.P6, C.P7, C.P8, C.P9 };
    for (int i = 0; i < 8; i++) { a[8 + 2 * i] = p[i]; a[9 + 2 * i] = p[i] >> 8; }
    a[25] = C.H1;
    h[0] = C.H2; h[1] = C.H2 >> 8; h[2] = C.H3;
    h[3] = C.H4 >> 4; h[4] = (C.H4 & 0x0F) | ((C.H5 & 0x0F) << 4); h[5] = C.H5 >> 4; h[6] = C.H6;
}

static void pack_raw(uint8_t d[8], int32_t P, int32_t T, int32_t H)
{
    d[0] = P >> 12; d[1] = P >> 4; d[2] = (P & 0xF) << 4;
    d[3] = T >> 12; d[4] = T >> 4; d[5] = (T & 0xF) << 4;
    d[6] = H >> 8; d[7] = H;
}

/* Bosch datasheet, cift hassasiyetli referans formuller */
static void ref(int32_t aT, int32_t aP, int32_t aH, double *T, double *P, double *H)
{
    double v1 = (aT / 16384.0 - C.T1 / 1024.0) * C.T2;
    double v2 = (aT / 131072.0 - C.T1 / 8192.0) * (aT / 131072.0 - C.T1 / 8192.0) * C.T3;
    double tf = v1 + v2;
    *T = tf / 5120.0;
    double p1 = tf / 2.0 - 64000.0;
    double p2 = p1 * p1 * C.P6 / 32768.0;
    p2 = p2 + p1 * C.P5 * 2.0;
    p2 = p2 / 4.0 + C.P4 * 65536.0;
    p1 = (C.P3 * p1 * p1 / 524288.0 + C.P2 * p1) / 524288.0;
    p1 = (1.0 + p1 / 32768.0) * C.P1;
    double p = 1048576.0 - aP;
    p = (p - p2 / 4096.0) * 6250.0 / p1;
    p1 = C.P9 * p * p / 2147483648.0;
    p2 = p * C.P8 / 32768.0;
    *P = (p + (p1 + p2 + C.P7) / 16.0) / 100.0;
    double h = tf - 76800.0;
    h = (aH - (C.H4 * 64.0 + C.H5 / 16384.0 * h)) *
        (C.H2 / 65536.0 * (1.0 + C.H6 / 67108864.0 * h * (1.0 + C.H3 / 67108864.0 * h)));
    h = h * (1.0 - C.H1 * h / 524288.0);
    *H = h < 0 ? 0 : h > 100 ? 100 : h;
}

int main(void)
{
    uint8_t a[26], h[7], d[8];
    pack_calib(a, h);
    bme280_calib_t P; bme280_parse_calib(a, h, &P);
    int fail = 0;
    if (memcmp(&P, &C, sizeof P)) { printf("HATA: kalibrasyon ayristirma farkli\n"); fail = 1; }

    /* Bosch BMP280/BME280 datasheet ornegi: T=25.08 C, P=100653 Pa (1006.53 hPa) */
    bme280_reading_t r;
    pack_raw(d, 415148, 519888, 30000);
    bme280_compensate(&P, d, &r);
    printf("Datasheet ornegi: T=%.2f C (beklenen 25.08)  P=%.2f hPa (beklenen 1006.53)  H=%.1f %%\n",
           r.temperature_c, r.pressure_hpa, r.humidity_pct);
    if (fabs(r.temperature_c - 25.08) > 0.01 || fabs(r.pressure_hpa - 1006.53) > 0.02) { printf("HATA: ornek uyusmuyor\n"); fail = 1; }

    double mT = 0, mP = 0, mH = 0; int n = 0;
    for (int aT = 450000; aT <= 580000; aT += 2000)
        for (int aP = 380000; aP <= 450000; aP += 3000)
            for (int aH = 20000; aH <= 45000; aH += 2500) {
                pack_raw(d, aP, aT, aH);
                bme280_compensate(&P, d, &r);
                double T, Pp, H; ref(aT, aP, aH, &T, &Pp, &H);
                if (fabs(r.temperature_c - T) > mT) mT = fabs(r.temperature_c - T);
                if (fabs(r.pressure_hpa - Pp) > mP) mP = fabs(r.pressure_hpa - Pp);
                if (fabs(r.humidity_pct - H) > mH) mH = fabs(r.humidity_pct - H);
                n++;
            }
    printf("%d nokta, tamsayi vs cift-hassasiyet max fark: T=%.4f C  P=%.4f hPa  H=%.4f %%\n", n, mT, mP, mH);
    if (mT > 0.01 || mP > 0.02 || mH > 0.2) { printf("HATA: fark tolerans disi\n"); fail = 1; }
    printf(fail ? "SONUC: BASARISIZ\n" : "SONUC: GECTI\n");
    return fail;
}
