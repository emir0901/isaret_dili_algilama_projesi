// ==============================================================================
//                 İŞARET DİLİ ANALİZ SİSTEMİ PROJESİ (BAP)
// ==============================================================================
// Geliştirici / Yazar : Recep Emirhan Öztürk
// E-posta            : emrhanozt06@gmail.com
// GitHub             : https://github.com/emir0901
//
// © 2026 Recep Emirhan Öztürk. Tüm hakları saklıdır.
// ==============================================================================

#include <MPU6050.h>
#include <Wire.h>

MPU6050 mpu;

// Flex pinleri
#define F1 34
#define F2 35
#define F3 32
#define F4 33
#define F5 36

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);
  Wire.begin();
  mpu.initialize();

  if (!mpu.testConnection()) {
    Serial.println("# MPU6050 baglanti hatasi!");
  } else {
    Serial.println("# MPU6050 hazir - Veri gonderiliyor...");
  }
  delay(1000);
}

void loop() {
  int f1 = analogRead(F1);
  int f2 = analogRead(F2);
  int f3 = analogRead(F3);
  int f4 = analogRead(F4);
  int f5 = analogRead(F5);

  int16_t ax, ay, az;
  mpu.getAcceleration(&ax, &ay, &az);

  // Sadece ham sensör verisi — label ve posture Python tarafında eklenir
  Serial.print(f1);
  Serial.print(",");
  Serial.print(f2);
  Serial.print(",");
  Serial.print(f3);
  Serial.print(",");
  Serial.print(f4);
  Serial.print(",");
  Serial.print(f5);
  Serial.print(",");
  Serial.print(ax);
  Serial.print(",");
  Serial.print(ay);
  Serial.print(",");
  Serial.println(az);

  delay(40); // ~25Hz
}