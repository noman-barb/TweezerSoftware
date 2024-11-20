const WebSocket = require('ws');
const fs = require('fs');

const ws = new WebSocket('ws://10.0.63.153:4031/ws');

let currentTemperature = -1;
let startTime = Date.now();

// Function to append temperature to CSV file
const appendTemperatureToCSV = (time, temperature) => {

  console.log('Time:', time, 'Temperature:', temperature);
  const logEntry = `${time},${temperature}\n`;
  
  
  fs.appendFile('temperature_logfile.csv', logEntry, (err) => {
    if (err) {
      console.error('Error writing to CSV file:', err);
    }
  });
};

// Initialize the CSV file with headers
fs.writeFile('temperature_logfile.csv', 'time(s),objective_temperature\n', (err) => {
  if (err) {
    console.error('Error initializing CSV file:', err);
  }
});

ws.on('open', () => {
  console.log('Connected to the WebSocket server');

  // Start appending data every second
  setInterval(() => {
    const currentTime = ((Date.now() - startTime) / 1000).toFixed(2); // Calculate elapsed time in seconds
    
    appendTemperatureToCSV(currentTime, currentTemperature);
  }, 1000);
});

ws.on('message', (data) => {
  // Get the message as a string
  const message = data.toString();
  // Get data in readable format
  console.log('Received message:', message);

  currentTemperature = JSON.parse(message).objective_temperature;
});

ws.on('close', () => {
  console.log('Disconnected from the WebSocket server');
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
});
