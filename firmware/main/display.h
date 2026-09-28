/* display.h: T-Display-S3'un dahili ekranina (ST7789) olcumu yazar.
 * CONFIG_DISPLAY_ST7789 kapaliyken fonksiyonlar bos govdeyle derlenir (cagirmak zararsiz). */
#pragma once
#include <stdbool.h>

void display_init(void);
void display_show(float t, float h, float p, bool has_p);
