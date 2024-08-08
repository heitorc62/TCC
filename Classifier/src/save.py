import os
import torch
import numpy as np
import pandas as pd
import json

def make_path(path):
    dir = os.path.dirname(path)
    if dir: 
        if not os.path.exists(dir):
            os.makedirs(dir)
            
def save_model(model, output_dir):
    # Save the model
    model_path = os.path.join(output_dir, "model.pth")
    make_path(model_path)
    torch.save(model.state_dict(), model_path)

    
def save_stats(stats, output_dir):
    stats_path = os.path.join(output_dir, "stats.csv")
    make_path(stats_path)
    print("stats = ")
    print(stats)
    with open(stats_path, 'w') as f:
        json.dump(stats, f)