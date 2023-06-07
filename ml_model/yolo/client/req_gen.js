const fs = require("fs");
const http = require("http");
const FormData = require("form-data");
const loadtest = require("loadtest");

const requestsPerSecond = parseInt(process.argv[2]);
const batchSize = parseInt(process.argv[3]);
const duration = parseInt(process.argv[4]);

const serice_ip = "localhost:8000"
let counter = 0

const images = ["images/cars.jpg", "images/zidane.jpg", "images/bus.jpg"]

function createArrayOfSizeX(sizeX) {
  let images_path = new Array(sizeX)

  for(let i = 0; i <= sizeX; i++) {
    const randomIndex = Math.floor(Math.random() * images.length)
    images_path[i] = images[randomIndex]
  }

  return  images_path;
}


// Define the custom request generator function
function requestGenerator(params, options, client, callback) {
  // Read the image file and convert it to a buffer
  const imagePaths = createArrayOfSizeX(batchSize)

  // Create a new FormData instance
  const formData = new FormData();

  for (const imagePath of imagePaths) {
    const imageBuffer = fs.readFileSync(imagePath);
    formData.append("images", imageBuffer, {
      filename: imagePath,
      contentType: "image/jpeg",
    });
  }

  // Set the necessary headers for the API request
  const headers = formData.getHeaders();

  options.headers = headers;
  options.method = "POST";

  const request = client(options, callback);
  // Handle errors
  request.on("error", (error) => {
    console.error("Request error:", error);
  });

  // Handle the response
  request.on("response", (response) => {
    let data = "";

    response.on("data", (chunk) => {
      data += chunk;
    });

    response.on("end", () => {
      counter++;
      console.log("Response: ", counter);
    });
  });

  formData.pipe(request);
  return request;
}

// Define the load testing options
const options = {
  url: `http://${serice_ip}/predict?model=yolov3`,
  concurrency: 1,
  requestGenerator: requestGenerator,
  requestsPerSecond: requestsPerSecond,
  //maxRequests: requestsPerSecond*duration,
  maxSeconds: duration,
  agentKeepAlive: true,
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
  url: 'http://128.110.218.25:31334/health',
  maxSeconds: 35,  // Total number of requests to be made
  concurrency: 1,  // Number of requests to be made concurrently
  requestGenerator: requestGenerator,
  requestsPerSecond: requestsPerSecond,
};
*/

// Perform the load testing
loadtest.loadTest(options, function (error, result) {
  if (error) {
    console.error("Load testing error:", error);
  } else {
    console.log(result);
  }

  return
});
