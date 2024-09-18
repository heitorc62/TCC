#!/bin/bash

. .yolo_env/bin/activate
yolo task=detect mode=train model=yolov8n.pt data=tomato.yaml epochs=50 imgsz=640 device=0
