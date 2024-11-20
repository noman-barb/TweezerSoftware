#define N_AVG 20 // average by for every analogr reading
#define analogPinPID A5 // read value from opamp
#define analogPinReadTemp A0
#define pwmPin 6 // for controlling low pass filter
#define Kp 0.2 // proportional gain
#define Ki 0.2 // Integral gain
#define Kd  0.01   // Derivative gain

String ID = "C274";
int setpoint = 403; // Desired setpoint (0-1023)
int pwmValue = 80; // PWM output value

// PID variables
float previousError = 0;
float integral = 0;
unsigned long previousTime = 0;
int analogValue = 0;
int error = 0;
unsigned long currentTime = 0;
float derivative = 0;
float deltaTime = 0;
float output = 0;

int val = 0;
int i = 0;
float apparentTemperature = 0;
int readVal = 0;
float setPointTemperature = 20.01;




int average_analog_val(int _pin){
  val = 0;
  for (i=0;i<N_AVG;i++){
    val+=analogRead(_pin);
    delayMicroseconds(4);
  }
  val = val/N_AVG;

  return val;
}

void pid_func(){

  analogValue = average_analog_val(analogPinPID); // Read the analog value
  error = setpoint - analogValue; // Calculate error
  
  currentTime = millis();
  deltaTime = (currentTime - previousTime) / 1000.0; // Time difference in seconds
  
  integral += error * deltaTime; // Integrate the error over time
  derivative = (error - previousError) / deltaTime; // Calculate the rate of change of the error
  
  // PID output
  output = Kp * error + Ki * integral +  Kd * derivative;
  
  // Convert the output to a PWM value
  pwmValue = constrain((int)output, 0, 255);
  
  analogWrite(pwmPin, pwmValue); // Write PWM value

   // Update previous values for the next loop
  previousError = error;
  previousTime = currentTime;

  // Serial.println();
  // Serial.print(setpoint);
  // Serial.print("...");
  // Serial.print(analogValue);
  // Serial.println();

  // Serial.println(pwmValue);
}

void set_set_point(float st){
  setPointTemperature = st;
  // st = st*0.9765 + 0.1593 ;

  st = st - 0.15;

  setpoint = (st/10)*1023/5.0;
  setpoint = max(setpoint,350);
  setpoint = min(setpoint, 750);
}

float get_temperature(){

  readVal = average_analog_val(analogPinReadTemp);

  apparentTemperature = (readVal*5.0/1023)*10;

  return apparentTemperature +0.15;

  // return apparentTemperature*1.026 - 0.2387+0.02;

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
        set_set_point(temperature_to_set);
        Serial.print("DATA_ST:");
        Serial.print(temperature_to_set,1);
        Serial.print("_END\n");
    }
    else if (input_command.startsWith("GETTEMPOT")){
      
        Serial.print("DATA_OT:");
        Serial.print(get_temperature(),1);
        Serial.print("_END\n");
    }
    else if (input_command.startsWith("GETTEMPST")){
      
        Serial.print("DATA_ST:");
        Serial.print(setPointTemperature,1);
        Serial.print("_END\n");
    }
  
}


void setup() {
  pinMode(pwmPin, OUTPUT);
  Serial.begin(9600); // Initialize serial communication for debugging
  Serial.setTimeout(50);
  set_set_point(20.0);
}

void loop() {
  pid_func();
 
  if (Serial.available()>0){
    process_command();
  }  

  delay(50);
}
