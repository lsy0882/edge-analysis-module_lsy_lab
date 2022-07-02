import numpy as np

class cam_mlp:
    def __init__(self):
        self.layer1_weight=None
        self.layer1_bias=None
        self.layer2_weight=None
        self.layer2_bias=None
        self.layer3_weight=None

    def load_layer(self,dict_layer):
        self.layer1_weight=dict_layer[0]['1'][0]['weight'].transpose()
        self.layer1_bias=dict_layer[0]['1'][1]['bias']

        self.layer2_weight=dict_layer[0]['2'][0]['weight'].transpose()
        self.layer2_bias=dict_layer[0]['2'][1]['bias']
        
        self.layer3_weight=dict_layer[0]['3'][0]['weight'].transpose()
        self.layer3_bias=dict_layer[0]['3'][1]['bias']

    def forward(self,x):
        out=np.maximum(0,np.dot(x,self.layer1_weight)+self.layer1_bias)
        out1=np.maximum(0,np.dot(out,self.layer2_weight)+self.layer2_bias)
        out2=np.maximum(0,np.dot(out1,self.layer3_weight)+self.layer3_bias)
        return out2