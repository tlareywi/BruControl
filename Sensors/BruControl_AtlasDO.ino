// Released under MIT License
// Copyright (c) 2022 Trystan Larey-Williams
//
// Provides integration of Atlas Scientific lab grade DO sensor with BruControl brewing automation sotware using an
// Arduino microprocessor with the Atlas Scientific EZO DO circuit board. Tested with an ESP32 dev board with integrated WiFi.
//
// On startup or after being reset, this Sketch will execute a calibration routine where the program will wait up to 60s
// for the probe's readings to stabilize at which time it will send the 'cal' command to the probe. Per Atlas Scientific,
// this calibration proceedure should be run when the probe is not submerged in open air. Ensure the probe is exposed to
// air when resetting the board for proper calibration.  
//
// In addition to reading DO meter values and posting them to a BruControl global, this Sketch will also pull a temperature
// value from BruControl that is used to configure temperature compensation on the meter, updated every 10s by default. 
//
// Includes modified example code from Atlas Scientific @ https://files.atlas-scientific.com/Arduino-Uno-DO-sample-code.pdf.
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


///
/// You may need to install these packages from the library manager in the Arduino IDE in order to build.
///
#include <SoftwareSerial.h> 
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

///
/// Set network SSID and password as appropriate for your WiFi network configuration.  
///
#define WIFI_NETWORK "networkid"
#define WIFI_PASSWORD "yourwifipassword"
#define WIFI_TIMEOUT 30000

///
/// Modify to match your arduino's wiring configutatrion. 
/// Note, we're using 'soft serial' so any GPIO pins can be used as RX/TX; do not use the hardware serial pins.
///                        
#define rx 23                                      
#define tx 22 

///
/// Set the appropriate address for your BruControl softeware with 'Data Exchange' enabled. 
/// Be sure to open port 8000 and preferably reserve BruControl's IP address on your router to ensure it doesn't change. 
///
String bruControl = "http://192.168.86.109:8000/globals";
String bruControlTemp1 = "http://192.168.86.109:8000/global/Temp1"; // Replace 'Temp1' with a global name from BruControl used for DO temperature compensation.
String bruControlDOGlobalName = "DO1"; // Replace with the name of the global in BruControl you want to update with the DO value.

#define TEMP_POLL_INTERVAL_MS 10000
#define CALIBRATION_LENGTH_MS 60000

SoftwareSerial myserial(rx, tx);                    

String inputstring = "";                            
String sensorstring = "";                           
boolean input_string_complete = false;             
boolean sensor_string_complete = false;            
float DO;    

HTTPClient http;


void connectToWifi() {
  Serial.println("Connecting to Wifi");  
  WiFi.mode( WIFI_STA );
  WiFi.begin( WIFI_NETWORK, WIFI_PASSWORD );

  unsigned long startConnectTime = millis();
  while( WiFi.status() != WL_CONNECTED && millis() - startConnectTime < WIFI_TIMEOUT ) {
    Serial.print(".");
    delay( 500 );
  }

  if( WiFi.status() == WL_CONNECTED ) {
    Serial.print("\n");
    Serial.println(WiFi.localIP());
  }  
}


StaticJsonDocument<128> doc;
char tempBuf[7];

void SetTempCompensation() {
  http.begin( bruControlTemp1 );
  if( http.GET() == 200 ) {                        // Get fermenter temp from BruControl
    String payload = http.getString();
    if( deserializeJson(doc, payload) == 0 ) {
      String strVal = doc["Value"];                 // Parse JSON and extract value
      float tempF = strVal.toFloat();
      float tempC = (tempF - 32) * 0.5556;          // Convert to degrees C
      dtostrf( tempC, 0, 2, tempBuf ); 
      myserial.print( "T," );
      myserial.print( tempBuf );                    // Send temperature compensation command to Atlas board           
      myserial.print( '\r' ); 
    }
  }
  http.end();
}


void setup() {                                        //set up the hardware
  Serial.begin(9600);                                 //set baud rate for the hardware serial port_0 to 9600
  myserial.begin(9600);                               //set baud rate for the software serial port to 9600
  if (!myserial) { // If the object did not initialize, then its configuration is invalid
    Serial.println("Invalid SoftwareSerial pin configuration, check config"); 
    while (1) { // Don't continue with invalid configuration
      delay (1000);
    }
  } 
  inputstring.reserve(10);                            //set aside some bytes for receiving data from the PC
  sensorstring.reserve(30);                           //set aside some bytes for receiving data from Atlas Scientific product

  while( WiFi.status() != WL_CONNECTED )
    connectToWifi();

  // Perform calibration routine. Set BruControl data to -1 to indicate calibration.
  http.begin(bruControl);
  http.addHeader("Content-Type", "application/json");
  http.PUT("[{\"Name\":\"DO1\",\"Value\":\"-1.00\"}]");
  http.end();

  unsigned long calibrationStart = millis();
  String atlasData;
  float tempData = 0.0;
  unsigned int numIdenticalSamples = 0;
  while( millis() - calibrationStart < CALIBRATION_LENGTH_MS && numIdenticalSamples < 10 ) {
    SetTempCompensation();
    while( myserial.available() > 0 ) {                     
      char inchar = (char)myserial.read();             
      if (inchar == '\r') {                          
        float data = atlasData.toFloat();
        if( data == tempData )
          ++numIdenticalSamples;
        else
          tempData = data;
      }
      else
        atlasData += inchar;                
    }
    atlasData = ""; 
    delay( 250 ); 
  }

  // Send cal command if either 60s is up or we stabalized samples
   Serial.print( "Sending calibration command ... " );
   myserial.print( "cal\r" ); 
}


void serialEvent() {                                  //if the hardware serial port_0 receives a char
  inputstring = Serial.readStringUntil(13);           //read the string until we see a <CR>
  input_string_complete = true;                       //set the flag used to tell if we have received a completed string from the PC
}

unsigned long getTimer = 0;

void loop() {
  int status = WiFi.status();

  if( millis() - getTimer > TEMP_POLL_INTERVAL_MS && status == WL_CONNECTED ) {
    SetTempCompensation();
    getTimer = millis();
  }

  if (input_string_complete == true) {                //if a string from the PC has been received in its entirety
    myserial.print(inputstring);                      //send that string to the Atlas Scientific product
    myserial.print('\r');                             //add a <CR> to the end of the string
    inputstring = "";                                 //clear the string
    input_string_complete = false;                    //reset the flag used to tell if we have received a completed string from the PC
  }

  if (myserial.available() > 0) {                     //if we see that the Atlas Scientific product has sent a character
    char inchar = (char)myserial.read();              //get the char we just received 
    if (inchar == '\r') {                             //if the incoming character is a <CR>
      sensor_string_complete = true;                  //set the flag
    }
    else {
      sensorstring += inchar;                         //append incoming character to string
    }
  }

  if (sensor_string_complete == true) {               //if a string from the Atlas Scientific product has been received in its entirety
    Serial.println(sensorstring);                     //send that string to the PC's serial monitor
    if( status == WL_CONNECTED && sensorstring[0] != '*' ) {
      http.begin(bruControl);
      http.addHeader("Content-Type", "application/json");
      http.PUT("[{\"Name\":\"" + bruControlDOGlobalName + "\",\"Value\":\"" + sensorstring + "\"}]");
      http.end();
    }
    else if( status != WL_CONNECTED ) {
      connectToWifi();                                // Keep trying to reconnect
    }

    while( myserial.available() > 0 )                 // Waiting on the put can overflow the input buffer. Clear it after we unblock.
      myserial.read();

    sensorstring = "";                                //clear the string
    sensor_string_complete = false;                   //reset the flag used to tell if we have received a completed string from the Atlas Scientific product
  }
}
