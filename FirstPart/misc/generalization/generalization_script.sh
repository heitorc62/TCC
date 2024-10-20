#!/bin/bash

nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/REGULAR/from_scratch/model.pth \
    &> out/REGULAR2.out
nohup python generalization.py \
     --cuda_device 1 \
     --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP/from_scratch/model.pth \
     &> out/EXP.out
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP_WB/from_scratch/model.pth \
    &> out/EXP_WB.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB/from_scratch/model.pth \
    &> out/WB.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB_EXP/from_scratch/model.pth \
    &> out/WB_EXP.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP_RMBG/from_scratch/model.pth \
    &> out/EXP_RMBG.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP_WB_RMBG/from_scratch/model.pth \
    &> out/EXP_WB_RMBG.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/RMBG/from_scratch/model.pth \
    &> out/RMBG.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB_EXP_RMBG/from_scratch/model.pth \
    &> out/WB_EXP_RMBG.out 
nohup python generalization.py \
    --cuda_device 1 \
    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB_RMBG/from_scratch/model.pth \
    &> out/WB_RMBG.out