const fs = require("fs");
const http = require("http");
const FormData = require("form-data");
const loadtest = require("loadtest");

const requestsPerSecond = process.argv[2];
const batchSize = process.argv[3];
const serice_ip = "128.110.218.27:31586"


// Define the custom request generator function
function requestGenerator(params, options, client, callback) {
  // Read the image file and convert it to a buffer
  const imagePaths = Array.from({ length: batchSize }, () => "images/cars.jpg");

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
      console.log("Response:", response.statusCode, data);
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
    fs.writeFile("loadtest.log.txt", JSON.stringify(result), "utf8", (err) => {
      if (err) {
        console.error("An error occurred while writing to the file:", err);
        return;
      }
    });
  }
});
