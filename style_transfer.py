from PIL import Image

import asyncio

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import torchvision.transforms as transforms
import torchvision.models as models

import copy


CNN = ''


class ContentLoss(nn.Module):
    def __init__(self, target,):
        super(ContentLoss, self).__init__()
        self.target = target.detach()
        self.loss = F.mse_loss(self.target, self.target )


    def forward(self, input):
        self.loss = F.mse_loss(input, self.target)
        return input


class StyleLossForSingleImage(nn.Module):
    def __init__(self, target_feature):
        super(StyleLossForSingleImage, self).__init__()
        self.target = self.gram_matrix(target_feature).detach()
        self.loss = F.mse_loss(self.target, self.target)


    def forward(self, input):
        G = self.gram_matrix(input)
        self.loss = F.mse_loss(G, self.target)
        return input


    def gram_matrix(self, input):
        batch_size , h, w, f_map_num = input.size()
        features = input.view(batch_size * h, w * f_map_num)
        G = torch.mm(features, features.t())

        return G.div(batch_size * h * w * f_map_num)



class StyleLossForDoubleImage(nn.Module):
    def __init__(self, target1, target2):
        super(StyleLossForDoubleImage, self).__init__()
        self.center = target1.shape[3]//2
        self.g_target1 = self.gram_matrix( target1[:,:,:,:self.center] ).detach()
        self.g_target2 = self.gram_matrix( target2[:,:,:,self.center:] ).detach()
        
        self.loss1 = F.mse_loss(self.g_target1, self.g_target1)  # init loss 1
        self.loss2 = F.mse_loss(self.g_target2, self.g_target2)  # init loss 2
        self.loss = self.loss1 + self.loss2

    def forward(self, x):
        g_x1 = self.gram_matrix( x[:,:,:,:self.center] )
        g_x2 = self.gram_matrix( x[:,:,:,self.center:] )

        self.loss1 = F.mse_loss(g_x1, self.g_target1)
        self.loss2 = F.mse_loss(g_x2, self.g_target2)
        self.loss = self.loss1 + self.loss2

        return x

    def gram_matrix(self, x):
        batch_size , h, w, f_map_num = x.size()
        features = x.reshape(batch_size * h, w * f_map_num)
        G = torch.mm(features, features.t())

        return G.div(batch_size * h * w * f_map_num)



class Normalization(nn.Module):
    def __init__(self, device):
        super(Normalization, self).__init__()
        mean = torch.tensor([0.485, 0.456, 0.406]).to(device)
        std = torch.tensor([0.229, 0.224, 0.225]).to(device)
        self.mean = mean.clone().detach().view(-1, 1, 1)
        self.std = std.clone().detach().view(-1, 1, 1)


    def forward(self, img):
        return (img - self.mean) / self.std



class Simple_style_transfer:
    def __init__(self, style_img, content_img, imsize = 1024, num_steps=500,
                    style_weight=100000, content_weight=1):

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.imsize = imsize
        self.style_img = self.image_loader(style_img)
        self.content_img = self.image_loader(content_img)
        self.input_img = self.content_img.clone()
        
        self.content_layers = ['conv_4']
        self.style_layers = ['conv_2','conv_3', 'conv_4', 'conv_5']

        self.num_steps = num_steps
        self.style_weight = style_weight
        self.content_weight = content_weight


    def image_loader(self, image_name):
        loader = transforms.Compose([
            transforms.Resize(self.imsize),
            transforms.CenterCrop(self.imsize),
            transforms.ToTensor()])

        image = Image.open(image_name)
        image = loader(image).unsqueeze(0)
        return image.to(self.device, torch.float)


    def get_style_model_and_losses(self):
        cnn = copy.deepcopy(CNN)

        normalization = Normalization(self.device).to(self.device)

        content_losses = []
        style_losses = []

        model = nn.Sequential(normalization)

        i = 0
        for layer in cnn.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = 'conv_{}'.format(i)
            elif isinstance(layer, nn.ReLU):
                name = 'relu_{}'.format(i)
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = 'pool_{}'.format(i)
            elif isinstance(layer, nn.BatchNorm2d):
                name = 'bn_{}'.format(i)
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

            model.add_module(name, layer)

            if name in self.content_layers:
                target = model(self.content_img).detach()
                content_loss = ContentLoss(target)
                model.add_module("content_loss_{}".format(i), content_loss)
                content_losses.append(content_loss)

            if name in self.style_layers:
                target_feature = model(self.style_img).detach()
                style_loss = StyleLossForSingleImage(target_feature)
                model.add_module("style_loss_{}".format(i), style_loss)
                style_losses.append(style_loss)

        for i in range(len(model) - 1, -1, -1):
            if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLossForSingleImage):
                break

        model = model[:(i + 1)]

        return model, style_losses, content_losses


    def get_input_optimizer(self):
        optimizer = optim.LBFGS([self.input_img.requires_grad_()]) 
        return optimizer


    async def test(self):
        num = 0
        while num < 20:
            num += 1
            print(num)

            await asyncio.sleep(1)

        return num


    async def transfer(self):
        global CNN

        if CNN == '':
            CNN = models.vgg19(pretrained=True).features.to(self.device).eval()

        model, style_losses, content_losses = self.get_style_model_and_losses()
        optimizer = self.get_input_optimizer()

        run = [0]
        while run[0] <= self.num_steps:
            print(run[0])
            
            await asyncio.sleep(0)

            def closure():
                self.input_img.data.clamp_(0, 1)

                optimizer.zero_grad()

                model(self.input_img)

                style_score = 0
                content_score = 0

                for sl in style_losses:
                    style_score += sl.loss
                for cl in content_losses:
                    content_score += cl.loss
                
                style_score *= self.style_weight
                content_score *= self.content_weight

                loss = style_score + content_score
                loss.backward()

                run[0] += 1

                return style_score + content_score

            optimizer.step(closure)


        self.input_img.data.clamp_(0, 1)

        return self.input_img



class Double_style_transfer():
    def __init__(self, style_1_img, style_2_img, content_img, imsize = 1024,
                    num_steps=500, style_weight=100000, content_weight=1):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.imsize = imsize
        self.style_1_img = self.image_loader(style_1_img)
        self.style_2_img = self.image_loader(style_2_img)
        self.content_img = self.image_loader(content_img)
        self.input_img = self.content_img.clone()
        
        self.content_layers = ['conv_4']
        self.style_layers = ['conv_2','conv_3', 'conv_4', 'conv_5']

        self.num_steps = num_steps
        self.style_weight = style_weight
        self.content_weight = content_weight


    def image_loader(self, image_name):
        loader = transforms.Compose([
            transforms.Resize(self.imsize),
            transforms.CenterCrop(self.imsize),
            transforms.ToTensor()])

        image = Image.open(image_name)
        image = loader(image).unsqueeze(0)
        return image.to(self.device, torch.float)


    def get_style_model_and_losses(self):
        cnn = copy.deepcopy(CNN)

        normalization = Normalization(self.device).to(self.device)

        content_losses = []
        style_losses = []

        model = nn.Sequential(normalization)

        i = 0
        for layer in cnn.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = 'conv_{}'.format(i)
            elif isinstance(layer, nn.ReLU):
                name = 'relu_{}'.format(i)
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = 'pool_{}'.format(i)
            elif isinstance(layer, nn.BatchNorm2d):
                name = 'bn_{}'.format(i)
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

            model.add_module(name, layer)

            if name in self.content_layers:
                target = model(self.content_img).detach()
                content_loss = ContentLoss(target)
                model.add_module("content_loss_{}".format(i), content_loss)
                content_losses.append(content_loss)

            if name in self.style_layers:
                target1 = model(self.style_1_img).detach()
                target2 = model(self.style_2_img).detach()
                style_loss = StyleLossForDoubleImage(target1, target2)
                model.add_module("style_loss_{}".format(i), style_loss)
                style_losses.append(style_loss)

        for i in range(len(model) - 1, -1, -1):
            if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLossForDoubleImage):
                break

        model = model[:(i + 1)]

        return model, style_losses, content_losses


    def get_input_optimizer(self):
        optimizer = optim.LBFGS([self.input_img.requires_grad_()]) 
        return optimizer


    async def test(self):
        num = 0
        while num < 20:
            num += 1
            print(num)

            await asyncio.sleep(1)

        return num


    async def transfer(self):
        global CNN

        if CNN == '':
            CNN = models.vgg19(pretrained=True).features.to(self.device).eval()

        model, style_losses, content_losses = self.get_style_model_and_losses()
        optimizer = self.get_input_optimizer()

        run = [0]
        while run[0] <= self.num_steps:
            print(run[0])
            
            await asyncio.sleep(0)

            def closure():
                self.input_img.data.clamp_(0, 1)

                optimizer.zero_grad()

                model(self.input_img)

                style_score = 0
                content_score = 0

                for sl in style_losses:
                    style_score += sl.loss
                for cl in content_losses:
                    content_score += cl.loss
                
                style_score *= self.style_weight
                content_score *= self.content_weight

                loss = style_score + content_score
                loss.backward()

                run[0] += 1

                return style_score + content_score

            optimizer.step(closure)


        self.input_img.data.clamp_(0, 1)

        return self.input_img