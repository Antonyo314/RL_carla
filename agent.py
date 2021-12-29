import glob
import os
import sys

try:
    sys.path.append(glob.glob('Carla/carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla
from collections import namedtuple, deque

import torch
import torch.nn as nn
import torch.nn.functional as F

from efficientnet_pytorch import EfficientNet

model = EfficientNet.from_name('efficientnet-b1')


class Net(nn.Module):
    def __init__(self, number_of_classes):
        super().__init__()
        self.number_of_classes = number_of_classes
        model = EfficientNet.from_name('efficientnet-b1')
        # Unfreeze model weights
        for param in model.parameters():
            param.requires_grad = True

        num_ftrs = model._fc.in_features
        model._fc = nn.Linear(num_ftrs, self.number_of_classes)


class Agent():
    def __init__(self):
        self.Q_model = None
        self.target_model = None
        self.REPLAY_MEMORY_SIZE = 100
        self.replay_memory = deque(maxlen=self.REPLAY_MEMORY_SIZE)
        self.NUMBER_OF_ACTIONS = 3
        self.target_update_count = 0
        self.MIN_REPLAY_MEMORY_SIZE = 100
    def create_model(self):
        return Net(self.NUMBER_OF_ACTIONS)
    def train(self):
        if len(self.replay_memory) < self.MIN_REPLAY_MEMORY_SIZE:
            return