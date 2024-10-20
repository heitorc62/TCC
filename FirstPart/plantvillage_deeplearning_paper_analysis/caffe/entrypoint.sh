#!/bin/bash
cd src/
python create_data_distribution.py

cd ../scripts/
bash generate_data_color-80-20.sh

#cd ../
#caffe train \
#    -solver train/test_setup_solver.prototxt \
#    -weights train/bvlc_googlenet.caffemodel \
#    -gpu all &> caffe.log