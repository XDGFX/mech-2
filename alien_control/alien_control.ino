#include <Client.h>
#include <SPI.h>
#include <WiFiNINA.h>
#include <PubSubClient.h>

// Settings for WiFi and MQTT connection
char ssid[] = "Pixel";
char pass[] = "BRNIVOZG";
char host[] = "ec2-3-10-235-26.eu-west-2.compute.amazonaws.com";
uint16_t port = 31415;
char clientid[] = "alien_self_isolation-ALIEN";
char username[] = "student";
char password[] = "smartPass";
char topicname[] = "ALIEN_SELF_ISOLATION-alien/7";

// Settings for connection status polling
const char sendTopic[] = "ALIEN_SELF_ISOLATION-alien/8";
const char connectedMessage[] = "4";

// Physical output pins for motors
#define PWM_L1 10
#define PWM_L2 11
#define PWM_R1 5
#define PWM_R2 3

// Variable for PWM motor speed output, and time active
int motorPwm = 30;
int turnPwm = 30;
int timeActive = 40;
int timeForwards = 200;

// Polling for connection status
int timeRemain = -1;
int prevMillis = 0;
int currentMillis = 0;
int timeInterval = 1000;

// Callback function header
void callback(char *topic, byte *payload, unsigned int length);

WiFiClient wificlient;
PubSubClient client(host, port, callback, wificlient);

void setup()
{
  Serial.begin(9600);

  // Set PWM and DIR connections as outputs
  pinMode(PWM_L1, OUTPUT);
  pinMode(PWM_R1, OUTPUT);
  pinMode(PWM_L2, OUTPUT);
  pinMode(PWM_R2, OUTPUT);

  Serial.println("Begin WiFi");

  WiFi.begin(ssid, pass);
  reconnect();
}

void loop()
{

  // Reconnect if connection is lost
  if (!client.connected() && WiFi.status() == 3)
  {
    reconnect();
  }

  // Maintain MQTT connection
  client.loop();

  // Delay to allow WiFi functions to run
  delay(10);

  // Publish connected status at required polling interval
  if ((currentMillis - prevMillis) >= timeInterval)
  {
    client.publish(sendTopic, connectedMessage);
    prevMillis = currentMillis;
  }

  currentMillis = millis();
}

// Callback upon message received
void callback(char *topic, byte *payload, unsigned int length)
{
  // Debug info
  Serial.println("Callback update.");

  for (int i = 0; i < length; i++)
  {
    Serial.print((char)payload[i]);
  }

  Serial.println();

  // payload[0] is the message:
  // 0: Straight
  // 1: Left
  // 2: Right
  // 3: Stop

  // Turn left
  if (payload[0] == '1')
  {
    Serial.println("Turning left");
    analogWrite(PWM_L1, turnPwm);
    analogWrite(PWM_L2, 0);

    analogWrite(PWM_R1, 0);        // 0
    analogWrite(PWM_R2, turnPwm); // motorpwm

    delay(timeActive);

    analogWrite(PWM_L1, 0);
    analogWrite(PWM_R2, 0);
  }

  // Turn right
  else if (payload[0] == '2')
  {
    Serial.println("Turning right");
    analogWrite(PWM_L1, 0);
    analogWrite(PWM_L2, turnPwm);

    analogWrite(PWM_R1, turnPwm);
    analogWrite(PWM_R2, 0);

    delay(timeActive);

    analogWrite(PWM_R1, 0);
    analogWrite(PWM_L2, 0);
  }
  
  // Drive forward
  else if (payload[0] == '3')
  {
    Serial.println("Driving forwards");
    analogWrite(PWM_L1, 0);
    analogWrite(PWM_L2, motorPwm);

    analogWrite(PWM_R1, 0);
    analogWrite(PWM_R2, motorPwm);

    delay(timeForwards);

    analogWrite(PWM_L2, 0);
    analogWrite(PWM_R2, 0);
  }

  // Otherwise, stop
  else if (payload[0] == '0')
  {
    analogWrite(PWM_L1, 0);
    analogWrite(PWM_L2, 0);
    analogWrite(PWM_R1, 0);
    analogWrite(PWM_R2, 0);
  }
}

// Networking functions
void reconnect()
{
  // Attempt to connect to the wifi if connection is lost
  if (WiFi.status() != WL_CONNECTED)
  {
    // Debug info
    Serial.print("Connecting to ");
    Serial.println(ssid);

    // Loop while we wait for connection
    while (WiFi.status() != WL_CONNECTED)
    {
      delay(500);
      Serial.print(".");
    }

    // Arduino is now connected
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
  }

  // Ensure we are connected to WIFI before attemping to reconnect to MQTT
  if (WiFi.status() == WL_CONNECTED)
  {
    // Loop until we're reconnected to the MQTT server
    while (!client.connected())
    {
      Serial.print("Attempting MQTT connection...");

      // If connected, subscribe to the topic(s) we want to be notified about
      if (client.connect(clientid, username, password))
      {
        Serial.print("\tMTQQ Connected");
        client.subscribe(topicname);
      }

      // Otherwise print failed for debugging
      else
      {
        Serial.println("\tFailed.");
        abort();
      }
    }
  }
}
