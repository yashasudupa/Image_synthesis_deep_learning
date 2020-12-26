import pandas as pd
import numpy as np
import torch
from torch import nn, optim
import torch.nn.functional as F
from torchvision import datasets
import torchvision.transforms as transforms
from torch.utils.data.sampler import SubsetRandomSampler
from torch.utils.data import DataLoader
from torch.utils.data import TensorDataset
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import scipy.io as io
from numpy import savetxt

def load_datasets(val_data_size = 0.2, batch_size = 100):

    #vocab = torch.load("mnist/MNIST/processed/training.pt")
    #print("PT samples", vocab)

    transform = transforms.Compose([transforms.RandomHorizontalFlip(0.5), \
                        transforms.RandomGrayscale(0.1), \
                        transforms.ToTensor(), \
                        transforms.Normalize((0.5,), (0.5,))])

    train_data = datasets.MNIST('MNIST/processed/training.pt', train=True, 
                                download=False, 
                                transform=transform)

    test_data = datasets.MNIST('MNIST/processed/test.pt', train=False, 
                                download=False, 
                                transform=transform)

    print(train_data)
    
    # Load training and testing datasets
    mat = io.loadmat('mnist.mat')
   
    tx_data = mat['trainX']
    tx_data = np.reshape(tx_data, (60000, 28, 28))
    tx_data = torch.from_numpy(tx_data)
    tx_data.transform = transforms.Compose([transforms.RandomHorizontalFlip(0.5), \
                        transforms.RandomGrayscale(0.1), \
                        transforms.ToTensor(), \
                        transforms.Normalize((0.5), \
                                            (0.5))])

    tx_target = mat['trainY'].T
    tx_target = torch.from_numpy(tx_target)
    #print(np.shape(tx_data))
    #print(np.shape(tx_target))
    #train_data = (tx_data, tx_target)    
    #print(train_data)

    ty_data = mat['testX']
    ty_data = np.reshape(ty_data, (10000, 28, 28))
    ty_data = torch.from_numpy(ty_data)
    ty_data.transform = transforms.Compose([transforms.RandomHorizontalFlip(0.5), \
                        transforms.RandomGrayscale(0.1), \
                        transforms.ToTensor(), \
                        transforms.Normalize((0.5), \
                                            (0.5))])

    ty_target = mat['testY'].T
    ty_target = torch.from_numpy(ty_target)
    #print(np.shape(ty_data))
    #print(np.shape(ty_target))
    #test_data = (ty_data, ty_target)
    #print(test_data)
    
    # Shuffling the training and validation datasets
    idx = list(range(len(train_data)))

    np.random.shuffle(idx)
    val_split_index = int(np.floor(val_data_size * len(train_data)))
    train_idx, val_idx = idx[val_split_index:], idx[:val_split_index]

    train_sampler = SubsetRandomSampler(train_idx)
    val_sampler = SubsetRandomSampler(val_idx)

    train_loader = DataLoader(train_data, \
                            batch_size=batch_size, \
                            sampler=train_sampler)
    val_loader = DataLoader(train_data, \
                            batch_size=batch_size, \
                            sampler=val_sampler)
    test_loader = DataLoader(test_data, \
                            batch_size=batch_size)
                            
    return train_loader, val_loader, test_loader

def cnn_network():
    """
    Building convolutional neural network
    """

    class CNN(nn.Module):
        def __init__(self):
            super(CNN, self).__init__()

            # conv2d(in_channels, out_channels, kernel_size, stride, pading)
            self.conv1 = nn.Conv2d(1, 10, 5, 1, 0)
            self.norm1 = nn.BatchNorm2d(10)
            
            self.conv2 = nn.Conv2d(10, 20, 3, 1, 0)
            self.norm2 = nn.BatchNorm2d(20)

            self.pool1 = nn.MaxPool2d(6, 2)
            self.pool2 = nn.MaxPool2d(2, 2)

            self.linear1 = nn.Linear(20 * 4 * 4, 100)
            self.norm3 = nn.BatchNorm1d(100)

            self.linear2 = nn.Linear(100, 10)
            self.dropout = nn.Dropout(0.2)
        def forward(self, x):
            x = self.pool1(self.norm1(F.relu(self.conv1(x))))
            x = self.pool2(self.norm2(F.relu(self.conv2(x))))
            x = x.view(-1, 20 * 4 * 4)
            x = self.dropout(x)
            x = self.norm3(F.relu(self.linear1(x)))
            x = self.dropout(x)
            x = F.log_softmax(self.linear2(x), dim=1)
            return x
    return CNN()

def training_testing_CNN(train_loader, val_loader, test_loader):

    epochs=50
    model = cnn_network()
    loss_function = nn.NLLLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    losses = 0
    acc = 0
    iterations = 0    
    train_losses, val_losses, train_acc, val_acc= [], [], [], []
    val_losss = 0
    val_accs = 0
    iter_2 = 0

    x_axis = []
    # For loop through the epochs
    for e in range(1, epochs+1):
        model.train()
        """
        Loop through the batches (created using
        the train loader)
        """
        for data, target in train_loader:
            iterations += 1
            # Forward and backward pass of the training data
            pred = model(data) 
            loss = loss_function(pred, target)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            losses += loss.item()
            p = torch.exp(pred)
            top_p, top_class = p.topk(1, dim=1)
            acc += accuracy_score(target, top_class)

         # Validation of model for given epoch
        if e%5 == 0 or e == 1:
            x_axis.append(e)
            with torch.no_grad():
                model.eval()
                
                #For loop through the batches of
                #the validation set
                
                for data_val, target_val in val_loader:
                    iter_2 += 1
                    val_pred = model(data_val)
                    val_loss = loss_function(val_pred, target_val)
                    val_losss += val_loss.item()
                    val_p = torch.exp(val_pred)
                    top_p, val_top_class = val_p.topk(1, dim=1)
                    val_accs += accuracy_score(target_val, 
                                            val_top_class)        
            # Losses and accuracy are appended to be printed
            train_losses.append(losses/iterations)
            val_losses.append(val_losss/iter_2)
            train_acc.append(acc/iterations)
            val_acc.append(val_accs/iter_2)
            print("Epoch: {}/{}.. ".format(e, epochs), \
                "Training Loss: {:.3f}.. "\
                .format(losses/iterations), \
                "Validation Loss: {:.3f}.. "\
                .format(val_losss/iter_2), \
                "Training Accuracy: {:.3f}.. "\
                .format(acc/iterations), \
                "Validation Accuracy: {:.3f}"\
                .format(val_accs/iter_2))

    plt.plot(x_axis,train_losses, label='Training loss')
    plt.plot(x_axis, val_losses, label='Validation loss')
    plt.legend(frameon=False)
    plt.show()

    plt.plot(x_axis, train_acc, label="Training accuracy")
    plt.plot(x_axis, val_acc, label="Validation accuracy")
    plt.legend(frameon=False)
    plt.show()

    model.eval()
    iter_3 = 0
    acc_test = 0
    for data_test, target_test in test_loader:
        iter_3 += 1
        test_pred = model(data_test)
        test_pred = torch.exp(test_pred)
        top_p, top_class_test = test_pred.topk(1, dim=1)
        acc_test += accuracy_score(target_test, top_class_test)
    print(acc_test/iter_3)
    
if __name__ == '__main__':
    train_loader, val_loader, test_loader = load_datasets()
    training_testing_CNN(train_loader, val_loader, test_loader)

