package main

import (
	"archive/zip"
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"
	"time"

	"strings"

	tf "github.com/wamuir/graft/tensorflow" //changed to graft
	"github.com/wamuir/graft/tensorflow/op" //changed to graft
)

// Define a struct to hold the JSON response data
type StatsResponse struct {
	Throughput    float64 `json:"throughput"`
	TotalRequests int     `json:"total_requests"`
}

var (
	graph              *tf.Graph
	session            *tf.Session
	dataMutex          sync.Mutex
	throughputs        []float64
	last_req_timestamp = time.Now()
	req_counter        = 0.0
	counter            int64
)

type StatusResponse struct {
	Status string `json:"status"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	// Create the StatusResponse struct instance
	response := StatusResponse{
		Status: "ok",
	}

	// Convert the struct to JSON
	jsonResponse, err := json.Marshal(response)
	if err != nil {
		http.Error(w, "Error creating JSON response", http.StatusInternalServerError)
		return
	}

	// Set the content type header to application/json
	w.Header().Set("Content-Type", "application/json")

	// Write the JSON response
	w.Write(jsonResponse)
}

func statsHandler(w http.ResponseWriter, r *http.Request) {

	totalReceivedRequests := 0
	dataMutex.Lock()

	if req_counter > 0 {
		throughputs = append(throughputs, req_counter)
		req_counter = 0
	}

	throughputs := removeElements(throughputs, 1)

	for _, num := range throughputs {
		totalReceivedRequests += int(num)
	}

	throughput := float64(totalReceivedRequests / len(throughputs))
	throughputs = make([]float64, 0)
	dataMutex.Unlock()

	// Create the StatsResponse struct instance
	stats := StatsResponse{
		Throughput:    throughput,
		TotalRequests: int(totalReceivedRequests),
	}

	// Convert the struct to JSON
	jsonResponse, err := json.Marshal(stats)
	if err != nil {
		http.Error(w, "Error creating JSON response", http.StatusInternalServerError)
		return
	}

	// Set the content type header to application/json
	w.Header().Set("Content-Type", "application/json")

	// Write the JSON response
	w.Write(jsonResponse)

}

// Middleware function for /predict endpoint
func predictMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

		next.ServeHTTP(w, r)

		dataMutex.Lock()

		timeDiff := time.Since(last_req_timestamp).Seconds()
		counter++
		if timeDiff >= 1 {
			throughputs = append(throughputs, req_counter/timeDiff)
			req_counter = 1
			last_req_timestamp = time.Now()
		} else {
			req_counter++
		}

		dataMutex.Unlock()

	})
}

func predictHandler(w http.ResponseWriter, r *http.Request) {

	// Check if the request method is POST
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	// Parse the multipart form data
	err := r.ParseMultipartForm(10 << 20) // Limit the maximum request size to 10MB
	if err != nil {
		http.Error(w, "Failed to parse multipart form data", http.StatusBadRequest)
		return
	}

	// Get the "images" field from the form data
	files := r.MultipartForm.File["images"]
	if len(files) == 0 {
		http.Error(w, "No images found in the request", http.StatusBadRequest)
		return
	}

	imagesByte := make([][]byte, len(files))
	index := 0

	// Iterate over the list of images
	for _, fileHeader := range files {
		// Open the file
		file, err := fileHeader.Open()
		if err != nil {
			http.Error(w, "Failed to open image file", http.StatusInternalServerError)
			return
		}

		imageByte, err := ioutil.ReadAll(file)
		if err != nil {
			http.Error(w, "Cannot read image file", http.StatusInternalServerError)
			return
		}

		file.Close()

		imagesByte[index] = imageByte
		index = index + 1
	}

	result := predict(imagesByte)

	response, err := json.Marshal(result)
	if err != nil {
		log.Fatal(err)
	}

	// Set the response content type to JSON
	w.Header().Set("Content-Type", "application/json")

	// Write the JSON response
	w.Write(response)

}

func startServer() {

	// Create a new instance of the multiplexer (router)
	mux := http.NewServeMux()

	// Apply the middleware to the /predict endpoint
	mux.Handle("/predict", predictMiddleware(http.HandlerFunc(predictHandler)))
	mux.Handle("/health", http.HandlerFunc(healthHandler))
	mux.Handle("/stats", http.HandlerFunc(statsHandler))
	log.Println("Server listening on port 8000")
	log.Fatal(http.ListenAndServe(":8000", mux))
}

func main() {
	// Download model if not downloaded
	// Load the serialized GraphDef from a file.

	log.Printf("Loading the model ...")
	modelfile, _, err := modelFiles("./model")
	if err != nil {
		log.Fatal(err)
	}
	model, err := ioutil.ReadFile(modelfile)
	if err != nil {
		log.Fatal(err)
	}

	// Construct an in-memory graph from the serialized form.
	graph = tf.NewGraph()
	if err := graph.Import(model, ""); err != nil {
		log.Fatal(err)
	}

	// Create a session for inference over graph.
	session, err = tf.NewSession(graph, nil)
	if err != nil {
		log.Fatal(err)
	}
	defer session.Close()

	warmupData := make([][]byte, 10)
	for i := 0; i < 10; i++ {
		fileBytes, err := ioutil.ReadFile("images/cars.jpg")
		if err != nil {
			fmt.Println("Error reading file:", err)
			return
		}
		warmupData[i] = fileBytes
	}
	predict(warmupData)
	startServer()
}

func predict(images [][]byte) []map[string]string {

	tensor, _ := getBatchTensor(images)

	output, err := session.Run(
		map[tf.Output]*tf.Tensor{
			graph.Operation("input").Output(0): tensor,
		},
		[]tf.Output{
			graph.Operation("output").Output(0),
		},
		nil)
	if err != nil {
		log.Fatal(err)
	}
	// output[0].Value() is a vector containing probabilities of
	// labels for each image in the "batch". The batch size was 1.
	// Find the most probably label index.
	probabilities := output[0].Value().([][]float32)

	results := make([]map[string]string, 0)

	for _, p := range probabilities {
		results = append(results, printBestLabel(p))
	}
	return results

}

func printBestLabel(probabilities []float32) map[string]string {
	_, labelsfile, err := modelFiles("./model")

	bestIdx := 0

	for i, p := range probabilities {
		if p > probabilities[bestIdx] {
			bestIdx = i
		}
	}
	// Found the best match. Read the string from labelsFile, which
	// contains one line per label.
	file, err := os.Open(labelsfile)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()
	scanner := bufio.NewScanner(file)
	var labels []string
	for scanner.Scan() {
		labels = append(labels, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		log.Printf("ERROR: failed to read %s: %v", labelsfile, err)
	}

	data := map[string]string{
		"probability": strconv.FormatFloat(float64(probabilities[bestIdx])*100.0, 'f', 2, 64),
		"object":      labels[bestIdx],
	}

	return data
}

// Convert the image in filename to a Tensor suitable as input to the Inception model.
func makeTensorFromImage(imageBytes []byte) (*tf.Tensor, error) {
	// DecodeJpeg uses a scalar String-valued tensor as input.

	tensorImg, err := tf.NewTensor(string(imageBytes))
	if err != nil {
		return nil, err
	}

	// Construct a graph to normalize the image
	graphImg, input, output, err := constructGraphToNormalizeImage()
	if err != nil {
		return nil, err
	}
	// Execute that graph to normalize this one image
	sessionImg, err := tf.NewSession(graphImg, nil)
	if err != nil {
		return nil, err
	}
	defer sessionImg.Close()
	normalized, err := sessionImg.Run(
		map[tf.Output]*tf.Tensor{input: tensorImg},
		[]tf.Output{output},
		nil)
	if err != nil {
		return nil, err
	}
	return normalized[0], nil
}

func constructGraphToNormalizeImage() (graph *tf.Graph, input, output tf.Output, err error) {

	const (
		H, W  = 224, 224
		Mean  = float32(117)
		Scale = float32(1)
	)
	s := op.NewScope()
	input = op.Placeholder(s, tf.String)
	output = op.Div(s,
		op.Sub(s,
			op.ResizeBilinear(s,
				op.ExpandDims(s,
					op.Cast(s,
						op.DecodeJpeg(s, input, op.DecodeJpegChannels(3)), tf.Float),
					op.Const(s.SubScope("make_batch"), int32(0))),
				op.Const(s.SubScope("size"), []int32{H, W})),
			op.Const(s.SubScope("mean"), Mean)),
		op.Const(s.SubScope("scale"), Scale))
	graph, err = s.Finalize()
	return graph, input, output, err
}

func modelFiles(dir string) (modelfile, labelsfile string, err error) {
	const URL = "https://storage.googleapis.com/download.tensorflow.org/models/inception5h.zip"
	var (
		model   = filepath.Join(dir, "tensorflow_inception_graph.pb")
		labels  = filepath.Join(dir, "imagenet_comp_graph_label_strings.txt")
		zipfile = filepath.Join(dir, "inception5h.zip")
	)
	if filesExist(model, labels) == nil {
		return model, labels, nil
	}
	log.Println("Did not find model in", dir, "downloading from", URL)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", "", err
	}
	if err := download(URL, zipfile); err != nil {
		return "", "", fmt.Errorf("failed to download %v - %v", URL, err)
	}
	if err := unzip(dir, zipfile); err != nil {
		return "", "", fmt.Errorf("failed to extract contents from model archive: %v", err)
	}
	os.Remove(zipfile)
	return model, labels, filesExist(model, labels)
}

func filesExist(files ...string) error {
	for _, f := range files {
		if _, err := os.Stat(f); err != nil {
			return fmt.Errorf("unable to stat %s: %v", f, err)
		}
	}
	return nil
}

func download(URL, filename string) error {
	resp, err := http.Get(URL)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	file, err := os.OpenFile(filename, os.O_RDWR|os.O_CREATE, 0644)
	if err != nil {
		return err
	}
	defer file.Close()
	_, err = io.Copy(file, resp.Body)
	return err
}

func unzip(dir, zipfile string) error {
	r, err := zip.OpenReader(zipfile)
	if err != nil {
		return err
	}
	defer r.Close()
	for _, f := range r.File {
		src, err := f.Open()
		if err != nil {
			return err
		}
		log.Println("Extracting", f.Name)
		dst, err := os.OpenFile(filepath.Join(dir, f.Name), os.O_WRONLY|os.O_CREATE, 0644)
		if err != nil {
			return err
		}
		if _, err := io.Copy(dst, src); err != nil {
			return err
		}
		dst.Close()
	}
	return nil
}

func getBatchTensor(images [][]byte) (*tf.Tensor, error) {

	batchOfImages := make([][][][]float32, len(images))

	index := 0

	for _, image := range images {
		tensor, _ := makeTensorFromImage(image)

		imageArr := tensor.Value().([][][][]float32)

		batchOfImages[index] = imageArr[0]

		index++
	}

	imagesTensor, err := tf.NewTensor(batchOfImages)
	return imagesTensor, err

}

func printBestLabelsTopK(probabilities []float32, topK int) map[string]string {
	_, labelsfile, err := modelFiles("./model")

	bestIndexes := make([]int, topK)
	for i := 0; i < topK; i++ {
		bestIndexes[i] = i
	}

	for i := topK; i < len(probabilities); i++ {
		minIdx := 0
		for j := 1; j < topK; j++ {
			if probabilities[bestIndexes[j]] < probabilities[bestIndexes[minIdx]] {
				minIdx = j
			}
		}
		if probabilities[i] > probabilities[bestIndexes[minIdx]] {
			bestIndexes[minIdx] = i
		}
	}

	file, err := os.Open(labelsfile)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var labels []string
	for scanner.Scan() {
		labels = append(labels, scanner.Text())
	}
	if err := scanner.Err(); err != nil {
		log.Printf("ERROR: failed to read %s: %v", labelsfile, err)
	}

	data := make(map[string]string)
	for _, idx := range bestIndexes {
		label := labels[idx]
		proba := strconv.FormatFloat(float64(probabilities[idx])*100.0, 'f', 2, 64)
		data[label] = proba
	}

	return data
}

func formatFloats(floats []float32) string {
	strs := make([]string, len(floats))
	for i, f := range floats {
		strs[i] = strconv.FormatFloat(float64(f)*100.0, 'f', 2, 64)
	}
	return strings.Join(strs, ", ")
}

func removeElements(arr []float64, x float64) []float64 {
	result := []float64{}
	for _, num := range arr {
		if num > x {
			result = append(result, num)
		}
	}
	return result
}
