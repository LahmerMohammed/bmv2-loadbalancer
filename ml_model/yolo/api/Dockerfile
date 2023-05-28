FROM node:18.8 AS node_builder

WORKDIR /app

COPY package*.json ./

RUN apt-get update \
    && apt-get install -y libglvnd-dev mesa-utils ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN npm init -y
RUN npm install

FROM python:3.10

WORKDIR /app

COPY --from=node_builder /app/node_modules /app/node_modules

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y libglvnd-dev mesa-utils ffmpeg libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt \
    && mkdir -p /root/.cvlib/object_detection/yolo/yolov3 \
    && yolo_path=/root/.cvlib/object_detection/yolo/yolov3 \
    && wget https://pjreddie.com/media/files/yolov3.weights -O ${yolo_path}/yolov3.weights \
    && wget https://github.com/pjreddie/darknet/raw/master/cfg/yolov3.cfg -O ${yolo_path}/yolov3.cfg \
    && wget https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.txt -O ${yolo_path}/yolov3.txt

COPY . .

CMD [ "node", "index.js" ]