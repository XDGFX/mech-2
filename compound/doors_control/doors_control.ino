#include <Client.h>
#include <SPI.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>
#include <Servo.h>

char ssid[] = "legacy";
char pass[] = "";
char host[] = "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com";
uint16_t port = 31415;
char clientid[] = "alien_self_isolation_test_arduino";
char username[] = "student";
char password[] = "smartPass";
char topicname[] = "ALIEN_SELF_ISOLATION-alien/7";

// Create servo items
Servo door_A;
Servo door_B;
Servo door_C;
Servo door_D;

// Define servo pins
#define door_pin_A 5
#define door_pin_B 6
#define door_pin_C 9
#define door_pin_D 10

// Callback function header
void callback(char *topic, byte *payload, unsigned int length);

WiFiClient wificlient;
PubSubClient client(host, port, callback, wificlient);

void setup()
{
  Serial.begin(9600);
  //
//  while (!Serial)
//  {
//    delay(1000);
//  }
  
  // Set servo connections
  door_A.attach(door_pin_A);
  door_B.attach(door_pin_B);
  door_C.attach(door_pin_C);
  door_D.attach(door_pin_D);

  //
  Serial.println("begin wifi");
  //
  WiFi.begin(ssid);
  reconnect();
}

void loop()
{

  //reconnect if connection is lost
  if (!client.connected() && WiFi.status() == 3)
  {
    reconnect();
  }

  //maintain MQTT connection
  client.loop();

  //MUST delay to allow ESP8266 WIFI functions to run
  delay(10);
}

void callback(char *topic, byte *payload, unsigned int length)
{
  //Print out some debugging info
  Serial.println("Callback update.");

  for (int i = 0; i < length; i++)
  {
    Serial.print((char)payload[i]);
  }
  Serial.println();

  // payload[0] is the command encoded as follows:
  // 0: Door A Open
  // 1: Door A Close
  // 2: Door B Open
  // 3: Door B Close
  // 4: Door C Open
  // 5: Door C Close
  // 6: Door D Open
  // 7: Door D Close


  if (payload[0] == '0')
  {
    door_A.write(30);
  }
  else if (payload[0] == '1')
  {
    door_A.write(90);
  }
  else if (payload[0] == '2')
  {
    door_B.write(30);
  }
  else if (payload[0] == '3')
  {
    door_B.write(90);
  }
  else if (payload[0] == '4')
  {
    door_C.write(30);
  }
  else if (payload[0] == '5')
  {
    door_C.write(90);
  }
  else if (payload[0] == '6')
  {
    door_D.write(30);
  }
  else if (payload[0] == '7')
  {
    door_D.write(90);
  }
 
}

//networking functions

void reconnect()
{

  //attempt to connect to the wifi if connection is lost
  if (WiFi.status() != WL_CONNECTED)
  {
    //debug printing
    Serial.print("Connecting to ");
    Serial.println(ssid);

    //loop while we wait for connection
    while (WiFi.status() != WL_CONNECTED)
    {
      delay(500);
      Serial.print(".");
    }

    //print out some more debug once connected
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
  }

  //make sure we are connected to WIFI before attemping to reconnect to MQTT
  if (WiFi.status() == WL_CONNECTED)
  {
    // Loop until we're reconnected to the MQTT server
    while (!client.connected())
    {
      Serial.print("Attempting MQTT connection...");

      //if connected, subscribe to the topic(s) we want to be notified about
      if (client.connect(clientid, username, password))
      {
        Serial.print("\tMTQQ Connected");
        client.subscribe(topicname);
      }

      //otherwise print failed for debugging
      else
      {
        Serial.println("\tFailed.");
        abort();
      }
    }
  }
}
