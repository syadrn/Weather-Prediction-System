// Tampilkan Blynk template id, name dan auth token
#define BLYNK_TEMPLATE_ID "TMPL633vt5hV9"
#define BLYNK_TEMPLATE_NAME "Monitoring Cuaca"
#define BLYNK_AUTH_TOKEN "s_XXfCra-J2EWEfBSS-d6w-WG9zLNPM4"

// import hal hal yang digunakan
#include "WiFi.h"
#include <HTTPClient.h>
#include "DHT.h"
#include <BlynkSimpleEsp32.h>

#define On_Board_LED_PIN  2
#define DHTPIN  4
#define DHTTYPE DHT11
#define LDR 32        // Pin for LDR sensor
#define Rain 35      // Pin for Rain sensor

// WiFi credentials
const char* ssid = "KOST MUSLIM";
const char* password = "i0d1r1u9s71";

// Google script Web_App_URL.
String Web_App_URL = "https://script.google.com/macros/s/AKfycbzc6cAA93fcSHQhgETQHJcngXFqcDzCfuojjXell1FgNX4gRLc0WPH70Pe4kBfidEVIxw/exec";

String Status_Read_Sensor = "";
float Temp;
int Humd;
int LDRvalue;
int RainValue;

// Initialize DHT as dht11.
DHT dht11(DHTPIN, DHTTYPE);
BlynkTimer timer;

//________________________________________________________________________________Getting_DHT11_Sensor_Data()
// Subroutine for getting temperature and humidity data from the DHT11 sensor.
void Getting_DHT11_Sensor_Data() {
  Humd = dht11.readHumidity();
  Temp = dht11.readTemperature();

  if (isnan(Humd) || isnan(Temp)) {
    Serial.println(F("Failed to read from DHT sensor!"));
    Status_Read_Sensor = "Failed";
    Temp = 0.00;
    Humd = 0;
  } else {
    Status_Read_Sensor = "Success";

    // Penanganan jika suhu lebih dari 30°C
    if (Temp > 30.2) {
      Temp = 30.2 + (Temp - 30.2) * 0.2;  // Setiap kenaikan 1 derajat dihitung sebagai 0.2 derajat
    }
  }

  Serial.print(F("Status_Read_Sensor : "));
  Serial.print(Status_Read_Sensor);
  Serial.print(F(" | Humidity : "));
  Serial.print(Humd);
  Serial.print(F("% | Temperature : "));
  Serial.print(Temp);
  Serial.println(F("°C"));
}
//________________________________________________________________________________

//________________________________________________________________________________Read_LDR_Sensor()
// Subroutine for getting the LDR sensor data.
void Read_LDR_Sensor() {
  LDRvalue = analogRead(LDR);
  
  // Ensure valid range
  if (LDRvalue < 0 || LDRvalue > 4095) {
    LDRvalue = 0;
  } else {
    LDRvalue = map(LDRvalue, 0, 4095, 0, 1000);  // Map LDR value from 0-100
    LDRvalue = (LDRvalue - 1000) * -1;
  }

  Blynk.virtualWrite(V3, LDRvalue);  // Send LDR value to Virtual Pin V3 on Blynk

  Serial.print("Light Intensity : ");
  Serial.println(LDRvalue);
}
//________________________________________________________________________________

//________________________________________________________________________________Read_Rain_Sensor()
// Subroutine for getting the Rain sensor data.
void Read_Rain_Sensor() {
  RainValue = analogRead(Rain);

  // Ensure valid range
  if (RainValue < 0 || RainValue > 4095) {
    RainValue = 0;
  } else {
    RainValue = map(RainValue, 0, 4095, 0, 100);  // Map Rain value from 0-100
    RainValue = (RainValue - 100) * -1;           // Adjust for percentage scale

    if (RainValue <= 96) {
      RainValue = 0;  // Set ke 0 jika nilainya kurang dari atau sama dengan 96
    } else {
      RainValue = (RainValue - 96) * 25;  // Kalikan dengan 25 jika lebih besar dari 96
    }
  }

  Blynk.virtualWrite(V2, RainValue);  // Send Rain sensor value to Virtual Pin V2 on Blynk

  Serial.print("Raindrop : ");
  Serial.println(RainValue);
}
//________________________________________________________________________________

//________________________________________________________________________________VOID SETUP()
void setup() {
  Serial.begin(115200);
  pinMode(On_Board_LED_PIN, OUTPUT);
  pinMode(LDR, INPUT);
  pinMode(Rain, INPUT);

  // Initialize DHT11
  dht11.begin();

  // Blynk setup
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, password);

  // WiFi setup
  WiFi.mode(WIFI_STA);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("WiFi connected");

  // Timer for sensors
  timer.setInterval(60000L, Getting_DHT11_Sensor_Data);  // Set ke 15 detik
  timer.setInterval(60000L, Read_LDR_Sensor);
  timer.setInterval(60000L, Read_Rain_Sensor);
}
//________________________________________________________________________________

//________________________________________________________________________________VOID LOOP()
void loop() {
  Blynk.run();  // Keep Blynk connection active
  timer.run();  // Run the timer for periodic sensor updates

  // Send all sensor data to Blynk
  Blynk.virtualWrite(V0, Temp);      // Send temperature to virtual pin V0
  Blynk.virtualWrite(V1, Humd);      // Send humidity to virtual pin V1
  Blynk.virtualWrite(V3, LDRvalue);  // Send LDR value to virtual pin V3
  Blynk.virtualWrite(V2, RainValue); // Send Rain sensor value to virtual pin V2

  // Check WiFi connection and send data to Google Sheets
  if (WiFi.status() == WL_CONNECTED) {
    String Send_Data_URL = Web_App_URL + "?sts=write";
    Send_Data_URL += "&srs=" + Status_Read_Sensor;
    Send_Data_URL += "&temp=" + String(Temp);
    Send_Data_URL += "&humd=" + String(Humd);
    Send_Data_URL += "&ldr=" + String(LDRvalue);  // Tambahkan LDR value
    Send_Data_URL += "&rain=" + String(RainValue);  // Tambahkan Rain value

    HTTPClient http;
    http.begin(Send_Data_URL.c_str());
    int httpCode = http.GET();

    if (httpCode > 0) {
      String payload = http.getString();
      Serial.println("Payload: " + payload);
    }
    http.end();
  } else {
    Serial.println("WiFi disconnected, trying to reconnect...");
    WiFi.begin(ssid, password);
    delay(5000);  // Beri waktu untuk koneksi ulang
  }

  delay(60000);  // Delay before next reading
}
//________________________________________________________________________________