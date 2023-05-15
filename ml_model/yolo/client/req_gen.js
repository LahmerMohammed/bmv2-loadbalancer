const fs = require('fs');
const http = require('http');
const FormData = require('form-data');
const loadtest = require('loadtest');

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

// Define the custom request generator function
function requestGenerator(params, options, client, callback) {
  options.headers = headers;
  options.method = 'POST';
  
  const request = client(options, callback);
  formData.pipe(request);
  return request;
}

// Define the load testing options
const options = {
  url: 'http://10.198.0.13:31977/predict?model=yolov3',
  maxRequests: 1,  // Total number of requests to be made
  concurrency: 1,  // Number of requests to be made concurrently
  requestGenerator: requestGenerator,
};

// Perform the load testing
loadtest.loadTest(options, function (error, result) {
  if (error) {
    console.error('Load testing error:', error);
  } else {
    console.log(result);
  }
});
