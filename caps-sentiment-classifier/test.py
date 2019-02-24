# example run:
#  python test.py --data_type custom --load_model_weight *.pth--vocab_size NUM --gpu 1

import argparse

import pickle
import pandas as pd
import torch
import torchnet as tnt
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchnet.logger import VisdomPlotLogger, VisdomLogger
from torchnlp.samplers import BucketBatchSampler

from model import Model
from utils import load_data, MarginLoss, collate_fn, FocalLoss


def reset_meters():
    meter_accuracy.reset()
    meter_loss.reset()
    meter_confusion.reset()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Train Text Classification')
    parser.add_argument('--data_type', default='imdb', type=str,
                        choices=['imdb', 'newsgroups', 'reuters', 'webkb',
                                 'cade', 'dbpedia', 'agnews', 'yahoo',
                                 'sogou', 'yelp', 'amazon', 'custom'],
                        help='dataset type')
    parser.add_argument('--fine_grained', action='store_true',
                        help='use fine grained class or not, it only works for reuters, yelp and amazon')
    parser.add_argument('--text_length', default=5000, type=int,
                        help='the number of words about the text to load')
    parser.add_argument('--routing_type', default='k_means', type=str,
                        choices=['k_means', 'dynamic'], help='routing type')
    parser.add_argument('--num_iterations', default=3, type=int,
                        help='routing iterations number')
    parser.add_argument('--batch_size', default=30, type=int,
                        help='batch size')
    parser.add_argument('--load_model_weight', default=None, type=str,
                        help='saved model weight to load')
    parser.add_argument('--gpu', default=1, type=int, help='GPU to use')

    opt = parser.parse_args()
    DATA_TYPE = opt.data_type
    FINE_GRAINED = opt.fine_grained
    TEXT_LENGTH = opt.text_length
    ROUTING_TYPE = opt.routing_type
    NUM_ITERATIONS = opt.num_iterations
    BATCH_SIZE = opt.batch_size
    MODEL_WEIGHT = opt.load_model_weight
    GPU = opt.gpu

    vocab_size, num_class, test_dataset = load_data(data_type='custom',
                                                    preprocessing=False,
                                                    fine_grained=FINE_GRAINED,
                                                    verbose=True,
                                                    text_length=TEXT_LENGTH)

    print("[!] vocab_size: {}, num_class: {}".format(vocab_size, num_class))
    test_sampler = BucketBatchSampler(test_dataset, BATCH_SIZE, False,
                                      sort_key=lambda row: len(row['text']))
    test_iterator = DataLoader(test_dataset, batch_sampler=test_sampler,
                               collate_fn=collate_fn)

    model = Model(vocab_size, num_class=num_class, routing_type=ROUTING_TYPE,
                  num_iterations=NUM_ITERATIONS)
    if MODEL_WEIGHT is not None:
        model.load_state_dict(torch.load('epochs/' + MODEL_WEIGHT))
    margin_loss, focal_loss = MarginLoss(), FocalLoss()
    if torch.cuda.is_available():
        model, margin_loss, focal_loss = model.to('cuda:{}'.format(GPU)), margin_loss.to('cuda:{}'.format(GPU)), focal_loss.to('cuda:{}'.format(GPU))

    optimizer = Adam(model.parameters())

    results = {'train_loss': [], 'train_accuracy': [], 'test_loss': [], 'test_accuracy': []}
    meter_accuracy = tnt.meter.ClassErrorMeter(accuracy=True)
    meter_loss = tnt.meter.AverageValueMeter()
    meter_confusion = tnt.meter.ConfusionMeter(num_class, normalized=True)

    reset_meters()
    model.eval()

    with torch.no_grad():
        for data, target in test_iterator:
            focal_label, margin_label = target, torch.eye(num_class).index_select(dim=0, index=target)
            if torch.cuda.is_available():
                data, focal_label, margin_label = data.to('cuda:{}'.format(GPU)), focal_label.to('cuda:{}'.format(GPU)), margin_label.to(
                                'cuda:{}'.format(GPU))
            classes = model(data)
            loss = focal_loss(classes, focal_label) + margin_loss(classes, margin_label)
            meter_loss.add(loss.detach().cpu().item())
            meter_accuracy.add(classes.detach().cpu(), target)
            meter_confusion.add(classes.detach().cpu(), target)
            results['test_accuracy'].append(meter_accuracy.value()[0])
            print('Test accuracy: {}'.format(meter_accuracy.value()))
    print('Final average accuracy: {}'.format(sum(results['test_accuracy']) / len(results['test_accuracy'])))
