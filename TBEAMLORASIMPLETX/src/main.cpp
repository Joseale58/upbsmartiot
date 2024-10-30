// #include <Arduino.h>
// #include <SPI.h>
// #include <LoRa.h>

// #define SCK 5
// #define MISO 19
// #define MOSI 27
// #define SS 18
// #define RST 23
// #define DIO 26
// #define BAND 915E6

// int contador = 0;
// void setup() {
//   Serial.begin(115200);
//   SPI.begin(SCK,MISO,MOSI,SS);
//   LoRa.setPins(SS,RST,DIO);
//   if (!LoRa.begin(915E6))
//   {
//     Serial.print("No inicio el radio");
//     while (1);
//   }
//   Serial.print("Radio inicializado exitosamente");
//   LoRa.setFrequency(915E6);
// }

// void loop() {
//   int a;
//   while(LoRa.beginPacket() == 0)
//   {
//     Serial.print("esperando por el radio...");
//     delay(100);
//   }
//   Serial.print("enviando data");
//   Serial.println(contador);

//   LoRa.beginPacket();
//   Serial.println("incio paquete");
//   LoRa.print("hola");
//   Serial.println("escribio hola");
//   LoRa.print(contador);
//   Serial.println("incremetno contador");
//   a = LoRa.endPacket();
//   if (a) Serial.println("transmision exitosa");
//   else Serial.println("error de tx");
//   Serial.println("termino paquete");
//   contador++;

//   delay(1000);
// }

// Only supports SX1276/SX1278

#include <LoRa.h>
#include "LoRaBoards.h"
#include "ClosedCube_HDC1080.h" // Biblioteca para el sensor HDC1080 (Temperatura y humedad)
#include <TinyGPSPlus.h> // Biblioteca para el GPS


// Directivas de preprocesador
#ifndef CONFIG_RADIO_FREQ
#define CONFIG_RADIO_FREQ           915.0
#endif
#ifndef CONFIG_RADIO_OUTPUT_POWER
#define CONFIG_RADIO_OUTPUT_POWER   17
#endif
#ifndef CONFIG_RADIO_BW
#define CONFIG_RADIO_BW             125.0
#endif


#if !defined(USING_SX1276) && !defined(USING_SX1278)
#error "LoRa example is only allowed to run SX1276/78. For other RF models, please run examples/RadioLibExamples"
#endif

int counter = 0;


// Pines para la comunicación I2C al sensor de humedad
int sda = 4;
int scl = 0;

// Temperatura sensor
ClosedCube_HDC1080 sensor;
float medidasTemp[10]; // Arreglo para guardar las medidas a promediar
float medidasHum[10]; // Arreglo para guardar las medidas a promediar
float calcularPromedioTemp();
float calcularPromedioHum();

// Para el GPS
TinyGPSPlus gps; // Objeto para manejar el GPS 
void smartDelay(long ms);  



void setup()
{

    Serial.begin(115200); // Velocidad de la conexión 
    //Wire.begin(sda, scl); // Inicializa el bus I2C en los pines SDA y SCL
    sensor.begin(0x40); // Inicializa el sensor HDC1080 en la dirección I2C 0x40
    Serial1.begin(9600, SERIAL_8N1, 34, 12);  // Inicializa el GPS en el puerto serial 1


    //Configura el hardware de la placa LilyGO TTGO T-Beam.
    setupBoards();

    // When the power is turned on, a delay is required.
    delay(1500);

    #ifdef  RADIO_TCXO_ENABLE
        pinMode(RADIO_TCXO_ENABLE, OUTPUT);
        digitalWrite(RADIO_TCXO_ENABLE, HIGH);
    #endif

    Serial.println("LoRa Sender");

    //Este comando establece los pines de control del módulo LoRa: CS, RST y DIO0.
    LoRa.setPins(RADIO_CS_PIN, RADIO_RST_PIN, RADIO_DIO0_PIN);

    //Este bloque inicializa el módulo LoRa a una frecuencia de radio especificada.
    if (!LoRa.begin(CONFIG_RADIO_FREQ * 1000000)) {
        Serial.println("Starting LoRa failed!");
        while (1);
    }

    //Se configura la potencia de transmisión del módulo LoRa.
    LoRa.setTxPower(CONFIG_RADIO_OUTPUT_POWER);

    //Se configura el ancho de banda de la señal de LoRa
    LoRa.setSignalBandwidth(CONFIG_RADIO_BW * 1000);

    //El spreading factor controla la cantidad de "repeticiones" en la transmisión, lo que afecta tanto la velocidad de datos como la sensibilidad de la señal. Valores más altos aumentan el alcance, pero reducen la velocidad de transmisión. 10, es un buen equilibrio
    LoRa.setSpreadingFactor(10);


    //El preamble length establece la longitud de la "cabecera" de la transmisión, que es una serie de bits que precede a los datos.
    LoRa.setPreambleLength(16);

    // El sync word es una serie de bits que se utilizan para sincronizar la comunicación entre dos dispositivos. Si el receptor no recibe el sync word correcto, descarta el paquete.
    LoRa.setSyncWord(0xAB);

    //Este comando deshabilita la verificación de redundancia cíclica (CRC), que es un mecanismo de detección de errores. Al desactivar CRC, se mejora ligeramente la velocidad de transmisión, pero se pierde la capacidad de verificar automáticamente si los datos recibidos son correctos.
    LoRa.disableCrc();

    //IQ Inversion es una técnica utilizada en LoRa para hacer que las señales sean más fáciles de distinguir. Aquí, el código desactiva la inversión de IQ, lo que significa que los datos se envían en su forma normal, sin invertir el espectro.
    LoRa.disableInvertIQ();

    //El coding rate (o tasa de codificación) afecta la relación entre los bits de datos y los bits de corrección de errores. Aquí, el valor 7 representa una tasa de corrección de 4/7, lo que significa que cada grupo de 7 bits transmitidos incluye 3 bits de corrección de errores. Esto mejora la confiabilidad de la comunicación
    LoRa.setCodingRate4(7);
}

void loop()
{
    Serial.print("Sending packet: ");
    Serial.println(counter);

    for (int i = 0; i < 10; i++) {
        Serial.println("Sensor: " + String(counter));
        float temperature = sensor.readTemperature();
        float humidity = sensor.readHumidity();
        delay(100);
        medidasTemp[i] = temperature;
        medidasHum[i] = humidity;
        delay(100);
    }

    delay(100);

    String promedioTemp = String(calcularPromedioTemp());
    String promedioHum = String(calcularPromedioHum());

    delay(100);

    String message = "Joselito${\"lat\": {\"value\":" + String(gps.location.lat(), 6) + "},\"lon\": {\"value\":" + String(gps.location.lng(), 6) + "},\"temp\": {\"value\":" + String(promedioTemp) + "},\"humedad\": {\"value\":" + String(promedioHum) + "}}";

    Serial.println( message);

    // send packet
    LoRa.beginPacket();
    LoRa.print(message);
    LoRa.endPacket();

    // if (u8g2) {
    //     char buf[256];
    //     u8g2->clearBuffer();
    //     u8g2->drawStr(0, 12, "Transmitting: OK!");
    //     snprintf(buf, sizeof(buf), "Sending: %d", counter);
    //     u8g2->drawStr(0, 30, buf);
    //     u8g2->sendBuffer();
    // }
    counter++;
    delay(5000);
}


// Función para calcular el promedio de las medidas
float calcularPromedioTemp() {
  float sum = 0; // Variable para guardar la suma de las medidas
  int medidas_size = sizeof(medidasTemp)/sizeof(medidasTemp[0]); // Tamaño del arreglo de medidas
  for (int i = 0; i < medidas_size; i++) {
    sum += medidasTemp[i]; // Suma de las medidas
  }
  float average = sum / medidas_size; // Cálculo del promedio
  return average;
}

// Función para calcular el promedio de las medidas
float calcularPromedioHum() {
  float sum = 0; // Variable para guardar la suma de las medidas
  int medidas_size = sizeof(medidasHum)/sizeof(medidasHum[0]); // Tamaño del arreglo de medidas
  for (int i = 0; i < medidas_size; i++) {
    sum += medidasHum[i]; // Suma de las medidas
  }
  float average = sum / medidas_size; // Cálculo del promedio
  return average;
}
