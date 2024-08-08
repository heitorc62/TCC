#!/bin/bash

#nohup python run.py \
#    --epochs 10 \
#    --device cuda:1 \
#    --dataset_dir /home/heitorc62/PlantsConv/dataset/Plant_leave_diseases_dataset_without_augmentation \
#    --testset_dir /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/generalization/datasets/IPM_dataset \
#    --output_dir /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/Classifier3/results/REGULAR \
#    &> out/REGULAR.out &


nohup python run.py \
    --epochs 10 \
    --device cuda:1 \
    --dataset_dir /home/heitorc62/PlantsConv/dataset/TCC_datasets/EXP \
    --testset_dir /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/generalization/datasets/IPM_dataset \
    --output_dir /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/Classifier3/results/EXP \
    &> out/EXP.out &


nohup python run.py \
    --epochs 10 \
    --device cuda:1 \
    --dataset_dir /home/heitorc62/PlantsConv/dataset/TCC_datasets/WB \
    --testset_dir /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/generalization/datasets/IPM_dataset \
    --output_dir /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/TCC/Classifier3/results/WB \
    &> out/WB.out &

#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP_WB/from_scratch/model.pth \
#    &> out/EXP_WB.out 
#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB/from_scratch/model.pth \
#    &> out/WB.out 
#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB_EXP/from_scratch/model.pth \
#    &> out/WB_EXP.out 
#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP_RMBG/from_scratch/model.pth \
#    &> out/EXP_RMBG.out 
#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/EXP_WB_RMBG/from_scratch/model.pth \
#    &> out/EXP_WB_RMBG.out 
#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/RMBG/from_scratch/model.pth \
#    &> out/RMBG.out 
#nohup python generalization.py \
#    --device cuda:1 \cuda_
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB_EXP_RMBG/from_scratch/model.pth \
#    &> out/WB_EXP_RMBG.out 
#nohup python generalization.py \
#    --device cuda:1 \
#    --model_path /home/heitorc62/PlantsConv/Plants-ConvNets-ViT/Classifier2/results/WB_RMBG/from_scratch/model.pth \
#    &> out/WB_RMBG.out