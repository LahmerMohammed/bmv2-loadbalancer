const express = require("express");
const multer = require("multer");
const swaggerUi = require("swagger-ui-express");
const swaggerJsdoc = require("swagger-jsdoc");
const { Mutex } = require('async-mutex');
const tf = require('@tensorflow/tfjs-node');
const cocoSsd = require('@tensorflow-models/coco-ssd');
const fs = require('fs');


const storage = multer.diskStorage({ 
    destination: function(req, file, cb) {
        cb(null, './assets')
    },
    filename: function(req, file, cb) {
        cb(null, process.hrtime.bigint() + '-' + file.originalname)
    }
});

const app = express();
const upload = multer({ storage });

const mutex = new Mutex();

let REQUEST_STATS = []

let model;

async function loadModel() {
  model = await cocoSsd.load();
  console.log("Model loaded successfully .") 
}

loadModel();

// Custom middleware to log incoming requests
app.use((req, res, next) => {
  console.log('Incoming Request:', 'Method:', req.method, 'URL:', req.url);
  next();
});



/**
 * @swagger
 * /predict:
 *   post:
 *     summary: Upload an image for object detection
 *     requestBody:
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               image:
 *                 type: string
 *                 format: binary
 *     responses:
 *       200:
 *         description: Image uploaded successfully
 *       400:
 *         description: Bad request - no image file provided
 */
app.post("/predict", upload.array("images"), async (req, res) => {
  const start = process.hrtime();
  console.log(Math.floor(Date.now() / 1000))

  res.on("finish", async () => {
    console.log(Math.floor(Date.now() / 1000))

    const end = process.hrtime(start);
    const processingTimeInMs = parseFloat(Math.round(end[0] * 1000 + end[1] / 1000000).toFixed(1));

    // Create a timestamp
    const timestamp = Date.now();

    // Acquire the mutex lock
    const release = await mutex.acquire();
    try {
      REQUEST_STATS.push({ timestamp: timestamp, processing_time: processingTimeInMs })
    } finally {
      release();
    }
    
  });

  const uploadedImage = req.files[0];

  if (!uploadedImage) {
    res.status(400).json({ error: 'No image file uploaded' });
    return;
  }

  const imagePath = uploadedImage.path;

  const imageBuffer = fs.readFileSync(imagePath);
  const imageTensor = tf.node.decodeImage(imageBuffer)

  const [height, width, channels] = imageTensor.shape;
  const imageTensor3D = imageTensor.reshape([imageTensor.shape[0], imageTensor.shape[1], channels]);
  
  let predictions = {}

  predictions = await model.detect(imageTensor3D);
 

  // Convert the predictions to a JSON format
  const jsonPredictions = JSON.stringify(predictions);

  // Cleanup resources
  tf.dispose([imageTensor, imageTensor3D, predictions]);

  // Delete the image file
  fs.unlinkSync(imagePath);

  res.status(200).json({ predictions: jsonPredictions });
});


/**
 * @swagger
 * /stats:
 *   get:
 *     summary: Get request statistics
 *     parameters:
 *       - in: query
 *         name: window
 *         required: true
 *         schema:
 *           type: integer
 *         description: Window size in milliseconds
 *     responses:
 *       200:
 *         description: Successful response
 *       400:
 *         description: Invalid window size
 *       500:
 *         description: Error retrieving request data
 */
app.get('/stats', async (req, res) => {
  const windowSize = parseInt(req.query.window);
  if (isNaN(windowSize)) {
    res.status(400).json({ error: 'Invalid window size' });
    return;
  }


  let stats = [];

  const release = await mutex.acquire(); 
  try {

    if (REQUEST_STATS.length == 0)
      res.status(200).json({ info: 'There is no stats.'})

    const currentTime = Date.now();
    const windowStartTime = currentTime - windowSize;

    // Filter entries in REQUEST_STATS with timestamp > windowStartTime
    stats = REQUEST_STATS.filter(entry => entry.timestamp > windowStartTime);
    
  }finally {
    release();
  }

  console.log(stats)

  if (stats.length == 0) {
    res.status(200).json({ info: 'There is no stats.'})
    return;
  }

  // Calculate average latency
  const totalLatency = stats.reduce((sum, entry) => sum + entry.processing_time, 0);
  const averageLatency = totalLatency / stats.length
  
  

  // Calculate the time difference between the first and last entries
  const firstEntry = stats[0];
  const lastEntry = stats[stats.length - 1];
  const timeDifference = (lastEntry.timestamp - firstEntry.timestamp) / 1000;

  res.status(200).json({ 
    "request_latency": averageLatency,
    "request_rate": stats.length / timeDifference,
    "total_requests": stats.length,
   });

  
});


// Health endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});



const swaggerOptions = {
  definition: {
    openapi: "3.0.0",
    info: {
      title: "Image Upload API",
      version: "1.0.0",
      description: "API for uploading and processing images",
    },
    servers: [
      {
        url: "http://localhost:8000",
      },
    ],
  },
  apis: ["./index.js"], // Add the path to your main application file
};

// Initialize Swagger-jsdoc
const swaggerSpec = swaggerJsdoc(swaggerOptions);

// Serve Swagger UI
app.use("/docs", swaggerUi.serve, swaggerUi.setup(swaggerSpec));

// Swagger endpoint
app.get("/swagger.json", (req, res) => {
  res.setHeader("Content-Type", "application/json");
  res.send(swaggerSpec);
});

// Start the server
const port = 8000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
