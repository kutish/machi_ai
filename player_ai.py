from torch.nn import Linear, Dropout, ReLU, Module, Softmax


class GenericAI(Module):
    def __init__(self, input_dim, additional_inputs):
        super(GenericAI, self).__init__()
        self.fc1 = Linear(input_dim + additional_inputs, 512)
        self.dropout1 = Dropout(0.1)
        self.relu1 = ReLU()

        self.fc2 = Linear(512, 256)
        self.dropout2 = Dropout(0.05)
        self.relu2 = ReLU()

        self.fc3 = Linear(256, 128)
        self.dropout3 = Dropout(0.05)
        self.relu3 = ReLU()

        self.fc4 = Linear(128, 2)
        self.softmax = Softmax(dim=1)

    def forward(self, x):
        x = self.fc1(x)
        x = self.dropout1(x)
        x = self.relu1(x)

        x = self.fc2(x)
        x = self.dropout2(x)
        x = self.relu2(x)

        x = self.fc3(x)
        x = self.dropout3(x)
        x = self.relu3(x)

        x = self.fc4(x)
        x = self.softmax(x)
        return x
