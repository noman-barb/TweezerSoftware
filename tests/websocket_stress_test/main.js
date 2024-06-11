const WebSocket = require('ws');

const ws = new WebSocket('ws://10.0.63.153:4041');

let messageCount = 0;
let dataSize = 0;

// Function to convert bytes to megabytes
function bytesToMB(bytes) {
  return bytes / (1024 * 1024);
}

// Function to reset counters and log the results
function resetCounters() {
  console.log(`Messages per second: ${messageCount}`);
  console.log(`Data received per second: ${bytesToMB(dataSize).toFixed(2)} MB`);
  messageCount = 0;
  dataSize = 0;
}

ws.on('open', () => {
  console.log('Connected to the WebSocket server');
  setInterval(resetCounters, 1000); // Log and reset counters every second
});

ws.on('message', (data) => {

  // get the message as string
  const message = data.toString();

  // get data in readable format
  console.log('Received message:', message);
  messageCount++;
   dataSize += data.length;
});

ws.on('close', () => {
  // close the connection
  console.log('Disconnected from the WebSocket server');
});

ws.on('error', (error) => {
  console.error('WebSocket error:', error);
});


//keep sending a msg "hello" every 1 second;

setInterval(() => {
  // send json "msg: hello"
  ws.send(JSON.stringify({ msg: 'hello' }));

}, 1000);