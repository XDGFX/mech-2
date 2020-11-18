#include <Client.h>
#include <SPI.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>

char ssid[] = "legacy";
char pass[] = "";
char host[] = "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com";
uint16_t port = 31415;
char clientid[] = "alien_self_isolation_test_arduino";
char username[] = "student";
char password[] = "smartPass";
char topicname[] = "ALIEN_SELF_ISOLATION-alien/7";

// Motor PWM
#define PWM_L1 10
#define PWM_R 5
// Motor DIR
#define PWM_L2 11
#define DIR_R 6

// Variable for PWM motor speed output
int motorPwm = 100;

// Callback function header
void callback(char *topic, byte *payload, unsigned int length);

WiFiClient wificlient;
PubSubClient client(host, port, callback, wificlient);

void setup()
{
  Serial.begin(9600);
  //
  while (!Serial)
  {
    delay(1000);
  }

  // Set PWM and DIR connections as outputs
  pinMode(PWM_L1, OUTPUT);
  pinMode(PWM_R, OUTPUT);
  pinMode(PWM_L2, OUTPUT);
  pinMode(DIR_R, OUTPUT);

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

  // if (payload[0] == '1')
  // {
  //   Serial.print('Oyy');
  // }

  // payload[0] is the direction:
  // 0: Straight
  // 1: Left
  // 2: Right

  // payload[1] is the distance:
  // 0: Stop
  // 1: Go

  // IF DIRECTION IS LEFT
  // Turn left
  if (payload[0] == '1')
  {
    Serial.print("jkehjrg");
    // Set direction to turn
    // digitalWrite(PWM_L1, 255);
    // digitalWrite(PWM_L2, 0);

    // Write PWM to controller
    analogWrite(PWM_L1, 255);
    analogWrite(PWM_L2, 0);
  }
  // IF DIRECTION IS RIGHT
  // Turn right
  else if (payload[0] == '2')
  {
    // Set direction to turn
    // digitalWrite(DIR_L, 0);
    // digitalWrite(DIR_R, 1);

    // Write PWM to controller
    analogWrite(PWM_L1, 0);
    analogWrite(PWM_L2, 255);
  }
  // IF DIRECTION ~0 AND DISTANCE >0
  // Drive forward
  else if (payload[0] == '3')
  {
    // Set direction to turn
    analogWrite(PWM_L1, 128);
    analogWrite(PWM_L2, 0);
  }
  // Otherwise, stop
  else if (payload[0] == '0')
  {
    // Write PWM to controller
    analogWrite(PWM_L1, 0);
    analogWrite(PWM_L2, 0);
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
