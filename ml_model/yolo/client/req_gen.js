const fs = require('fs');
const http = require('http');
const FormData = require('form-data');
const loadtest = require('loadtest');


// Define the custom request generator function
function requestGenerator(params, options, client, callback) {

// Read the image file and convert it to a buffer
const imagePath = 'images/cars.jpg';
const imageBuffer = fs.readFileSync(imagePath);

// Create a new FormData instance
const formData = new FormData();

// Append the image field to the form data
formData.append('image', imageBuffer, {
  filename: 'cars.jpg',
  contentType: 'image/jpeg'
});

// Set the necessary headers for the API request
const headers = formData.getHeaders();



  options.headers = headers;
  options.method = 'POST';
  
  const request = client(options, callback);
  // Handle errors
  request.on('error', (error) => {
    console.error('Request error:', error);
  });

  // Handle the response
  request.on('response', (response) => {
    let data = '';

    response.on('data', (chunk) => {
      data += chunk;
    });

    response.on('end', () => {
      console.log('Response:', response.statusCode, data);
    });
  });

  formData.pipe(request);
  return request;
}

// Define the load testing options
const options = {
  url: 'http://10.198.0.13:31977/predict?model=yolov3',
  concurrency: 10,  // Number of requests to be made concurrently
  requestGenerator: requestGenerator,
  requestsPerSecond: 10,
  maxSeconds: 100,

};

/*

// Define the custom request generator function
function requestGenerator(params, options, client, callback) {
  options.method = 'GET';

  const request = client(options, callback);

  // Handle errors
  request.on('error', (error) => {
    console.error('Request error:', error);
  });

  // Handle the response
  request.on('response', (response) => {
    let data = '';

    response.on('data', (chunk) => {
      data += chunk;
    });

    response.on('end', () => {
      console.log('Response:', response.statusCode, data);
    });
  });

  return request;
}

// Define the load testing options
const options = {
  url: 'http://10.198.0.13:31977/health',
  maxSeconds: 10,  // Total number of requests to be made
  concurrency: 10,  // Number of requests to be made concurrently
  requestGenerator: requestGenerator,
  requestsPerSecond: 10,
};

*/

// Perform the load testing
loadtest.loadTest(options, function (error, result) {
  if (error) {
    console.error('Load testing error:', error);
  } else {
    console.log(result);
  }
});
