/* DHT22 kod cozme testi (datasheet ornekleri). gcc -o dht22_test dht22_test.c && ./dht22_test */
#include <stdio.h>
#include <math.h>
#include "../main/dht22_comp.c"
int main(void)
{
    int fail = 0; float t, h;
    uint8_t ex1[5] = { 0x02, 0x92, 0x01, 0x0D, 0xA2 };       /* datasheet: 65.2 %RH... hesap: 0x0292=658 -> 65.8 %, 0x010D=269 -> 26.9 C */
    if (!dht22_decode(ex1, &t, &h) || fabsf(h - 65.8f) > 0.01f || fabsf(t - 26.9f) > 0.01f) { printf("HATA ornek1: %.1f C %.1f %%\n", t, h); fail = 1; }
    else printf("ornek1 OK: %.1f C  %.1f %%\n", t, h);
    uint8_t ex2[5] = { 0x02, 0x92, 0x80, 0x65, 0x79 };       /* sicaklik bit15=1: -10.1 C */
    if (!dht22_decode(ex2, &t, &h) || fabsf(t + 10.1f) > 0.01f) { printf("HATA ornek2: %.1f\n", t); fail = 1; }
    else printf("ornek2 OK (negatif): %.1f C\n", t);
    uint8_t bad[5] = { 0x02, 0x92, 0x01, 0x0D, 0x00 };       /* yanlis toplam reddedilmeli */
    if (dht22_decode(bad, &t, &h)) { printf("HATA: yanlis toplam kabul edildi\n"); fail = 1; } else printf("yanlis toplam reddedildi OK\n");
    printf(fail ? "SONUC: BASARISIZ\n" : "SONUC: GECTI\n"); return fail;
}
