import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import random

# Parameters and DataLoaders
input_size = 5
output_size = 2

batch_size = 30
data_size = 100
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
class RandomDataset(Dataset):

    def __init__(self, size, length):
        self.len = length
        self.data = torch.randn(length, size)

    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return self.len

rand_loader = DataLoader(dataset=RandomDataset(input_size, data_size),
                         batch_size=batch_size, shuffle=True)

class Model(nn.Module):
    # Our model

    def __init__(self, input_size, output_size):
        super(Model, self).__init__()
        self.fc = nn.Linear(input_size, output_size)
        self.register_buffer("debug_param",torch.Tensor([1]))

    def _local_usage(self):
        print("local usge {}".format(self.debug_param))

    def reset_debug_param(self):
        self.debug_param = self.debug_param*0+1

    def forward(self, input):
        output = self.fc(input)
        print("\tIn Model: input size", input.size(),
              "output size", output.size())
        self.debug_param *= 2
        self._local_usage()

        return output


model = Model(input_size, output_size)
if torch.cuda.device_count() > 1:
  print("Let's use", torch.cuda.device_count(), "GPUs!")
  # dim = 0 [30, xxx] -> [10, ...], [10, ...], [10, ...] on 3 GPUs
  model = nn.DataParallel(model)

model.to(device)

for data in rand_loader:
    input = data.to(device)
    model.module.reset_debug_param()
    output = model(input)
    print("at current iteration {}".format(model.module.debug_param))
    print("Outside: input size", input.size(),
          "output_size", output.size())
