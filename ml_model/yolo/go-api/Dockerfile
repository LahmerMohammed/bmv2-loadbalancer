# Stage 1: Build the Go binary
FROM golang:1.16.7 AS builder

WORKDIR /app

# Copy the Go source code
COPY . .

# Build the Go binary
RUN go build -o myapp

# Stage 2: Create the final image
FROM debian:buster-slim

# Install TensorFlow C library dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libcurl4-openssl-dev \
    libssl-dev

# Download and install the TensorFlow C library
RUN wget https://storage.googleapis.com/tensorflow/libtensorflow/libtensorflow-cpu-linux-x86_64-2.6.0.tar.gz | tar -C /usr/local -xz

# Set the library path
ENV LD_LIBRARY_PATH=/usr/local/lib

# Copy the Go binary from the builder stage
COPY --from=builder /app/myapp /app/myapp

# Set the working directory
WORKDIR /app


CMD ["./myapp"]