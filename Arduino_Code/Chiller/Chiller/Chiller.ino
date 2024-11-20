#include <Wire.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <LiquidCrystal_I2C.h>

#define ONE_WIRE_BUS 13

#define PUMP_IN 10
#define INCREM_IN 9
#define DECREM_IN 8

#define PELTIER_OUT 12
#define PUMP_OUT 6
#define WIGGLE_ROOM 0.1

#define DELTA_TIME_BEFORE_SET_POINT_CHANGE 100
#define DELTA_CHANGE_SET_POINT_ON_BTN_CLICK 0.1

#define TEMP_UPDATE_INTERVAL 10000

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
LiquidCrystal_I2C lcd(0x27, 20, 4);

float current_temp = -1.0;
float set_point = 20.0;
int isFlowOn = 0;
int isFlowOnHardware = 0;
int isFlowOnSoftware = 0;
unsigned long last_button_click_time = -1;
unsigned long last_temp_request_time = -1;

String ID = "CH826";

float roundToFirstDecimal(float number) {
  return round(number * 10.0) / 10.0;
}

void setup(void) {

  // Pinmodes//////////////////

  pinMode(ONE_WIRE_BUS, INPUT_PULLUP);

  pinMode(PUMP_IN, INPUT_PULLUP);
  pinMode(INCREM_IN, INPUT_PULLUP);
  pinMode(DECREM_IN, INPUT_PULLUP);

  pinMode(PELTIER_OUT, OUTPUT);
  pinMode(PUMP_OUT, OUTPUT);

  ///////////////////////////////

  // initialize LCD

  lcd.begin(20, 4); // Specify the number of columns and rows
  lcd.setBacklight(1);
  lcd.setContrast(1);
  lcd.setCursor(0, 0);
  lcd.print("Chiller Starting");

  ////////////////////////////////

  Serial.begin(9600);
  Serial.setTimeout(50);
  sensors.begin();


  //////////////////////////////////
}

void get_current_temp(){
  if (millis()-last_temp_request_time<TEMP_UPDATE_INTERVAL)
    return;
  sensors.requestTemperatures();
  float temperatureC = sensors.getTempCByIndex(0);
  if (temperatureC != DEVICE_DISCONNECTED_C) {
  current_temp = temperatureC;
  last_temp_request_time = millis();
  }
}

void lcd_print(){
  char buffer[10];

  lcd.setCursor(0, 0);
  lcd.print("Set Pt : ");
  dtostrf(roundToFirstDecimal(set_point), 4, 1, buffer);
  lcd.print(buffer);
  lcd.print("     ");

  lcd.setCursor(0, 1);
  lcd.print("Current: ");
  dtostrf(roundToFirstDecimal(current_temp), 4, 1, buffer);
  lcd.print(buffer);

  lcd.setCursor(0, 2);
  lcd.print("Flow   : ");
  lcd.print(isFlowOn>0 ? "ON":"OFF");
  lcd.print("   ");

  // Calculate and print uptime
  unsigned long currentMillis = millis();
  unsigned long totalSeconds = currentMillis / 1000;
  unsigned long hours = totalSeconds / 3600;
  unsigned long minutes = (totalSeconds % 3600) / 60;
  unsigned long seconds = totalSeconds % 60;

  lcd.setCursor(0, 3);
  sprintf(buffer, "%04lu:%02lu:%02lu", hours, minutes, seconds);
  lcd.print("Up Time: ");
  lcd.print(buffer);
}

void peltier_control(){

  float delta = current_temp - set_point;

  if (delta>0){
    digitalWrite(PELTIER_OUT, HIGH);
  }
  else if (delta<-WIGGLE_ROOM) {
    digitalWrite(PELTIER_OUT, LOW);
  }
}
void turn_flow_on_off(){
  analogWrite(PUMP_OUT, isFlowOn? 255:0);
}

void get_button_click(){

  if (millis() - last_button_click_time<DELTA_TIME_BEFORE_SET_POINT_CHANGE)
    return;

  if (digitalRead(INCREM_IN)==LOW){

    set_point+=DELTA_CHANGE_SET_POINT_ON_BTN_CLICK;

  }
  if (digitalRead(DECREM_IN)==LOW){
    set_point-=DELTA_CHANGE_SET_POINT_ON_BTN_CLICK;
  }

  isFlowOnHardware =  digitalRead(PUMP_IN);

  last_button_click_time = millis();
}


void process_command(){

    String input_command = Serial.readStringUntil("_END");
    // verify if the command is valid
    // it should start with CMD_ and end with _END
    if (!input_command.startsWith("CMD_") || !input_command.endsWith("_END")){
        return;
    }

    // now we can process the command
    input_command = input_command.substring(4);
    input_command = input_command.substring(0,input_command.length()-4);
  

    if (input_command.startsWith("IDENTIFY")){
        Serial.print("DATA_ID:");
        Serial.print(ID);
        Serial.print("_END\n");
    }
    else if (input_command.startsWith("SETTEMP_")){
        float temperature_to_set = input_command.substring(8).toFloat();
        set_point = roundToFirstDecimal(temperature_to_set);
              
        Serial.print("DATA_ST:");
        Serial.print(set_point,1);
        Serial.print("_END\n");
      
    }
    else if (input_command.startsWith("SETFLOW_")){
        isFlowOnSoftware = input_command.substring(8).toInt();
        Serial.print("DATA_FL:");
        Serial.print(isFlowOn,1);
        Serial.print("_END\n");
      
    }
    else if (input_command.startsWith("GETTEMPCT")){
      
        Serial.print("DATA_CT:");
        Serial.print(current_temp,1);
        Serial.print("_END\n");
    }
    else if (input_command.startsWith("GETTEMPST")){
      
        Serial.print("DATA_ST:");
        Serial.print(set_point,1);
        Serial.print("_END\n");
    }

    else if (input_command.startsWith("GETFLOWIF")){  
        Serial.print("DATA_FL:");
        Serial.print(isFlowOn,1);
        Serial.print("_END\n");
    }
  
}


void loop(void) {


  get_current_temp();

  peltier_control();
  lcd_print();
  turn_flow_on_off();
  get_button_click();

  isFlowOn = isFlowOnSoftware;

  if (Serial.available()>0){
    process_command();
  } 

 
}