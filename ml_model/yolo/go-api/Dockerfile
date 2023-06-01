# Stage 1: Install TensorFlow C library
FROM debian:buster-slim AS tf-installer

# Install TensorFlow C library dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libcurl4-openssl-dev \
    libssl-dev

# Download and install the TensorFlow C library
RUN curl -L "https://storage.googleapis.com/tensorflow/libtensorflow/libtensorflow-cpu-linux-x86_64-2.6.0.tar.gz" | tar -C /usr/local -xz

# Set the library path
ENV LD_LIBRARY_PATH=/usr/local/lib

# Stage 2: Build the Go binary
FROM golang:1.16.7 AS builder

WORKDIR /app

# Copy the Go source code
COPY . .

RUN go mod init go-model

RUN go mod tidy

RUN go install

# Build the Go binary
RUN go build -o myapp

# Stage 3: Create the final image
FROM debian:buster-slim

# Copy the TensorFlow C library from tf-installer stage
COPY --from=tf-installer /usr/local /usr/local

# Set the library path
ENV LD_LIBRARY_PATH=/usr/local/lib

# Install additional dependencies if required
# RUN apt-get update && apt-get install -y ...

# Copy the Go binary from the builder stage
COPY --from=builder /app/myapp /app/myapp

# Set the working directory
WORKDIR /app

# Expose any necessary ports
EXPOSE 8080

# Run the Go binary
CMD ["./myapp"]
