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
//   Serial.print("reciebe callback");

// }

// void loop() {
//   // try to parse packet
//   int packetSize = LoRa.parsePacket();
//   if (packetSize) {
//     // received a packet
//     Serial.print("Received packet '");

//     // read packet
//     while (LoRa.available()) {
//       Serial.print((char)LoRa.read());
//     }

//     // print RSSI of packet
//     Serial.print("' with RSSI ");
//     Serial.println(LoRa.packetRssi());
//   }
// }

// Only supports SX1276/SX1278
#include <LoRa.h>
#include "LoRaBoards.h"

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
#error "LoRa example is only allowed to run SX1276/78. For other RF models, please run examples/RadioLibExamples
#endif

void setup()
{
    //Configura el hardware de la placa LilyGO TTGO T-Beam.
    setupBoards();

    // When the power is turned on, a delay is required.
    delay(1500);

    Serial.println("LoRa Receiver");

    #ifdef  RADIO_TCXO_ENABLE
        pinMode(RADIO_TCXO_ENABLE, OUTPUT);
        digitalWrite(RADIO_TCXO_ENABLE, HIGH);
    #endif


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

    //Finalmente, este comando coloca al módulo LoRa en modo de recepción. Esto significa que el dispositivo está listo para recibir datos desde otros módulos LoRa.
    LoRa.receive();

}

void loop()
{
    // try to parse packet
    int packetSize = LoRa.parsePacket();
    if (packetSize) {
        // received a packet
        Serial.print("Received packet '");

        String recv = "";
        // read packet
        while (LoRa.available()) {
            recv += (char)LoRa.read();
        }

        Serial.println(recv);

        // print RSSI of packet
        Serial.print("' with RSSI ");
        Serial.println(LoRa.packetRssi());
        if (u8g2) {
            u8g2->clearBuffer();
            char buf[256];
            u8g2->drawStr(0, 12, "Received OK!");
            u8g2->drawStr(0, 26, recv.c_str());
            snprintf(buf, sizeof(buf), "RSSI:%i", LoRa.packetRssi());
            u8g2->drawStr(0, 40, buf);
            snprintf(buf, sizeof(buf), "SNR:%.1f", LoRa.packetSnr());
            u8g2->drawStr(0, 56, buf);
            u8g2->sendBuffer();
        }
    }
}