# Base image
FROM golang:1.16.7

# Install dependencies for Golang and TensorFlow C lib

# Disable APT post-invoke script

# Install dependencies for Golang and TensorFlow C library
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    zlib1g-dev


# Install TensorFlow C library
# Install TensorFlow C library
RUN wget https://storage.googleapis.com/tensorflow/libtensorflow/libtensorflow-cpu-linux-x86_64-2.11.0.tar.gz && \
    tar -C /usr/local -xzf libtensorflow-cpu-linux-x86_64-2.11.0.tar.gz && \
    ldconfig /usr/local/lib /usr/local && \
    rm libtensorflow-cpu-linux-x86_64-2.11.0.tar.gz


# Set the working directory
WORKDIR /app

# Copy your code or files to the working directory if needed
COPY . /app


ENV CGO_CFLAGS="-I/usr/local/include"
ENV CGO_LDFLAGS="-L/usr/local/lib"
ENV CGO_ENABLED=1


RUN go version
# Install the required Go packages
RUN go mod init go-model

RUN go mod tidy
RUN go get github.com/wamuir/graft/tensorflow@v0.3.1

# Build the Go binary
RUN go build -o myapp


CMD ["./myapp"]
