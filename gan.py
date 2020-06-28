import os
from options.test_options import TestOptions
from models import create_model

import matplotlib.pyplot as plt
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image


def transfer(img_path, imsize = 256, logging = True):
    opt = TestOptions(logging).parse()  # get test options

    # hard-code some parameters for test
    opt.num_threads = 0   # test code only supports num_threads = 1
    opt.batch_size = 1    # test code only supports batch_size = 1
    opt.serial_batches = True  # disable data shuffling; comment this line if results on randomly chosen images are needed.
    opt.no_flip = True    # no flip; comment this line if results on flipped images are needed.
    opt.display_id = -1   # no visdom display; the test code saves the results to a HTML file.
    
    opt.dataroot = ''
    opt.name = 'horse2zebra_pretrained'        # name of folder with model
    opt.model = 'test'
    opt.no_dropout = True

    opt.crop_size = imsize
    opt.load_size = imsize

    model = create_model(opt, logging)      # create a model given opt.model and other options
    model.setup(opt)               # regular setup: load and print networks; create schedulers
    
    img = image_loader(img_path, imsize)
    data = {'A': img, 'A_paths': ''}
    model.set_input(data)
    model.test()
    visuals = model.get_current_visuals()  # get image results

    return visuals['fake']

        
def image_loader(image_name, imsize):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    loader = transforms.Compose([
        transforms.Resize(imsize),
        transforms.CenterCrop(imsize),
        transforms.ToTensor()])

    image = Image.open(image_name)  
    image = loader(image).unsqueeze(0)
    return image.to(device, torch.float)


def draw_img(img):
    plt.imshow(np.rollaxis(img.add(1).div(2).cpu().detach()[0].numpy(), 0, 3))
    plt.show()


if __name__ == '__main__':
    # for test
    # draw_img(transfer('./corgi_800x800.jpg'))
    pass