#!/bin/bash

#SBATCH --workdir /home/mohanty/caffe_experiments/AWS_FRESH_RUN/experiment_configs/googLeNet/color-80-20/finetune
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 2
#SBATCH --mem 16384
#SBATCH --time 23:59:59
#SBATCH --partition gpu
#SBATCH --gres gpu:2
#SBATCH --qos gpu



# module add caffe
# module add cuda
echo STARTING AT `date`

sudo docker run --rm --runtime=nvidia -v $(pwd):$(pwd) -u $(id -u):$(id -g) -w $(pwd) --gpus all -ti bvlc/caffe:gpu caffe train -solver ./solver.prototxt -weights /home/plucas/projects/TCC/plantvillage_deeplearning_paper_analysis/googLeNet/color-80-20/finetune/bvlc_googlenet.caffemodel -gpu all &> caffe.log
# sbatch test.sh
echo FINISHED at `date`

