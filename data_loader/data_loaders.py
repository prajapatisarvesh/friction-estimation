import torch
import os
import torch.nn as nn
from PIL import Image
from base.base_data_loader import BaseDataLoader
import torchvision.transforms as transforms 
import  matplotlib.pyplot as plt
import numpy as np

mappings = {
    "none": 0,
    "hide": 0,
    "bone": 0.4,
    "brick": 0.7,
    "cardboard": 0.5,
    "carpet": 0.3,
    "ceilingtile": 0.6,
    "ceramic": 0.97,
    "chalkboard": 0.6,
    "clutter": 0.2,
    "concrete": 0.8,
    "cork": 0.4,
    "engineeredstone": 0.85,
    "fabric": 0,
    "fiberglass": 0.5,
    "fire": 0,
    "foliage": 0.3,
    "food": 0.2,
    "fur": 0.4,
    "gemstone": 0.9,
    "glass": 0.8,
    "hair": 0.2,
    "icannottell": 0,
    "ice": 0.1,
    "leather": 0.4,
    "liquid": 0.1,
    "metal": 0.8,
    "mirror": 0.9,
    "notonlist": 0,
    "paint": 0,
    "paper": 0,
    "pearl": 0.6,
    "photograph": 0.1,
    "clearplastic": 0.5,
    "plastic": 0.6,
    "rubber": 0.7,
    "sand": 0,
    "skin": 0.5,
    "sky": 0,
    "snow": 0,
    "soap": 0.3,
    "soil": 0.6,
    "sponge": 0.2,
    "stone": 0.8,
    "polishedstone": 0.9,
    "styrofoam": 0.2,
    "tile": 0.7,
    "wallpaper": 0.1,
    "water": 0,
    "wax": 0,
    "whiteboard": 0.5,
    "wicker": 0.4,
    "wood": 0.88,
    "treewood": 0.88,
    "badpolygon": 0,
    "multiplematerials": 0,
    "asphalt": 0.74
}

class AppleMLDMSLoader(BaseDataLoader):
    def __init__(self, csv_file, root_dir, mapped=False, transform=None):
        super().__init__(csv_file=csv_file, root_dir=root_dir, transform=transform)
        self.mapped = mapped
        print("[+] Data Loaded with rows: ", super().__len__())
        
    def convert_to_friction(self, mask):
        for i,j in enumerate(mappings.items()):
            mask[mask == i] = j[1]
        return mask
        
    def __getitem__(self, idx):
        image = self.csv_dataframe.iloc[idx, 0]
        mask = self.csv_dataframe.iloc[idx, 1]
        image = np.array(Image.open(image).convert('RGB'))
        mask = np.array(Image.open(mask))
        if self.mapped:
            mask = self.convert_to_friction(mask)
        
        if self.transform:
            augmentation = self.transform(image=image, mask=mask)
            image = augmentation['image']
            mask = augmentation['mask']
        return image, mask
    

class VastDataLoader(BaseDataLoader):
    def __init__(self, csv_file, root_dir):
        super().__init__(csv_file=csv_file, root_dir=root_dir, transform=None)
        self.transform_ = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((224, 224)),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ])
        self.min_ind = 250
        self.max_ind = 1800
        self.dark_min = torch.tensor(np.load(self.root_dir+'/data/vast_data/calibration/dark_min.npy'))
        self.light_max = torch.tensor(np.load(self.root_dir+'/data/vast_data/calibration/light_max.npy'))
        self.light_max = torch.clamp(self.light_max, min=2000)
        self.dark_min = self.dark_min[self.min_ind:self.max_ind]
        self.light_max = self.light_max[self.min_ind:self.max_ind]
        # print(self.dark_min.shape, self.light_max.shape)
        print("[+] Data Loaded with rows: ", super().__len__())
    

    def __getitem__(self, idx):
        image = self.csv_dataframe.iloc[idx, 0]
        spectral_data = self.csv_dataframe.iloc[idx, 1]
        image = Image.open(image)
        spectral_data = np.load(spectral_data)[1::2]
        transformed_image = self.transform_(image)
        if np.mean(spectral_data) <= 1800:
            return None
        spectral_data = torch.tensor(spectral_data)
        spectral_data = spectral_data[self.min_ind:self.max_ind]
        data = torch.clamp((spectral_data - self.dark_min) / (self.light_max - self.dark_min + 1e-6), min=0, max=1)
        return transformed_image, data