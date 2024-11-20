


#define OUTPUT_PIN 4

String ID = "FR_J37FH";


void setup(void) {

  pinMode(OUTPUT_PIN, OUTPUT);

  Serial.begin(9600);
  Serial.setTimeout(50);

  tone(OUTPUT_PIN, 1,1);

}

void process_command() {
    // Read the full input and manually check for "_END"
    String input_command = Serial.readString();
    
    // Verify if the command is valid: should start with "CMD_" and end with "_END"
    if (!input_command.startsWith("CMD_") || !input_command.endsWith("_END")) {
        return;  // Invalid command, exit the function
    }

    // Remove the prefix "CMD_" and the suffix "_END"
    input_command = input_command.substring(4); // Remove "CMD_"
    input_command = input_command.substring(0, input_command.length() - 4); // Remove "_END"

    // Process the command
    if (input_command.startsWith("IDENTIFY")) {
        // Command: IDENTIFY
        Serial.print("DATA_ID:");
        Serial.print(ID);  // Assuming `ID` is defined elsewhere
        Serial.print("_END\n");
    } 
    else if (input_command.startsWith("SETFR_")) {
        // Command: SETFR_ (Set Frame Rate)
        int frame_rate = input_command.substring(6).toInt(); // Extract the frame rate after "SETFR_"

        Serial.print("DATA_FR:");
        Serial.print(frame_rate);  // Assuming `ID` is defined elsewhere
        Serial.print("_END\n");

      
        if (frame_rate <= 0) {
            // Invalid frame rate, stop any output signal
            tone(OUTPUT_PIN, 1,1);  
        } else {
            // Set the frame rate (or frequency) using the tone function
            tone(OUTPUT_PIN, frame_rate);
        }
    }
}



void loop(void) {


  if (Serial.available()>0){
    process_command();
  } 

 
}