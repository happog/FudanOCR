# -*- coding:utf-8 -*-
from engine.trainer import Trainer
from engine.env import Env
from data.build import build_dataloader

from engine.trainer_collection.MORAN import MORAN_Trainer
# from engine.trainer_collection.GRCNN import GRCNN_Trainer
from engine.trainer_collection.RARE import RARE_Trainer
from engine.trainer_collection.SAR import SAR_Trainer
from engine.trainer_collection.CRNN import CRNN_Trainer
# from engine.trainer_collection.PixelLink import PixelLink_Trainer
# from engine.trainer_collection.LSN import LSN_Trainer
from engine.trainer_collection.AON import AON_Trainer
from engine.trainer_collection.DAN import DAN_Trainer



env = Env()
train_loader, test_loader = build_dataloader(env.opt)
newTrainer = DAN_Trainer(modelObject=env.model, opt=env.opt, train_loader=train_loader,
                           val_loader=test_loader).train()

