# e.g. run:
#  python main.py --data_type amazon --num_iterations 10 --num_epochs 5 --num_steps 100 --gpu 1

import argparse

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
                        choices=['imdb', 'newsgroups', 'reuters',
                                 'webkb', 'cade', 'dbpedia', 'agnews', 'yahoo',
                                 'sogou', 'yelp', 'amazon'],
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
                        help='train batch size')
    parser.add_argument('--num_epochs', default=100, type=int,
                        help='train epochs number')
    parser.add_argument('--num_steps', default=100, type=int,
                        help='test steps number')
    parser.add_argument('--load_model_weight', default=None, type=str,
                        help='saved model weight to load')
    parser.add_argument('--load_sle', default=0, type=bool,
                        help='Indicate if already have a sentence/label encoder')
    parser.add_argument('--gpu', default=None, type=int, help='the GPU to use')

    opt = parser.parse_args()
    GPU = opt.gpu
    DATA_TYPE = opt.data_type
    FINE_GRAINED = opt.fine_grained
    TEXT_LENGTH = opt.text_length
    ROUTING_TYPE = opt.routing_type
    NUM_ITERATIONS = opt.num_iterations
    BATCH_SIZE = opt.batch_size
    NUM_EPOCHS = opt.num_epochs
    NUM_STEPS = opt.num_steps
    MODEL_WEIGHT = opt.load_model_weight
    load_SLE = opt.load_sle

    # prepare dataset
    vocab_size, num_class, train_dataset, test_dataset = load_data(DATA_TYPE, preprocessing=True,
                                                                   fine_grained=FINE_GRAINED, verbose=True,
                                                                   text_length=TEXT_LENGTH, load_SLE=load_SLE)
    print("[!] vocab_size: {}, num_class: {}".format(vocab_size, num_class))
    train_sampler = BucketBatchSampler(train_dataset, BATCH_SIZE, False, sort_key=lambda row: len(row['text']))
    train_iterator = DataLoader(train_dataset, batch_sampler=train_sampler, collate_fn=collate_fn)
    test_sampler = BucketBatchSampler(test_dataset, BATCH_SIZE, False, sort_key=lambda row: len(row['text']))
    test_iterator = DataLoader(test_dataset, batch_sampler=test_sampler, collate_fn=collate_fn)

    model = Model(vocab_size, num_class=num_class, routing_type=ROUTING_TYPE, num_iterations=NUM_ITERATIONS)
    if MODEL_WEIGHT is not None:
        print('Loaded model.')
        model.load_state_dict(torch.load('epochs/' + MODEL_WEIGHT))

    margin_loss, focal_loss = MarginLoss(), FocalLoss()
    if torch.cuda.is_available():
        model, margin_loss, focal_loss = model.to('cuda:{}'.format(GPU)), margin_loss.to('cuda:{}'.format(GPU)), focal_loss.to('cuda:{}'.format(GPU))

    optimizer = Adam(model.parameters())
    print("# trainable parameters:", sum(param.numel() for param in model.parameters()))
    # record statistics
    results = {'train_loss': [], 'train_accuracy': [], 'test_loss': [], 'test_accuracy': []}
    # record current best test accuracy
    best_acc = 0
    meter_loss = tnt.meter.AverageValueMeter()
    meter_accuracy = tnt.meter.ClassErrorMeter(accuracy=True)
    meter_confusion = tnt.meter.ConfusionMeter(num_class, normalized=True)

    # config the visdom figures
    if FINE_GRAINED and DATA_TYPE in ['reuters', 'yelp', 'amazon']:
        env_name = DATA_TYPE + '_fine_grained'
    else:
        env_name = DATA_TYPE
    train_loss_logger = VisdomPlotLogger('line', env=env_name, opts={'title': 'Train Loss'})
    train_accuracy_logger = VisdomPlotLogger('line', env=env_name, opts={'title': 'Train Accuracy'})
    train_confusion_logger = VisdomLogger('heatmap', env=env_name, opts={'title': 'Train Confusion Matrix'})
    test_loss_logger = VisdomPlotLogger('line', env=env_name, opts={'title': 'Test Loss'})
    test_accuracy_logger = VisdomPlotLogger('line', env=env_name, opts={'title': 'Test Accuracy'})
    test_confusion_logger = VisdomLogger('heatmap', env=env_name, opts={'title': 'Test Confusion Matrix'})

    current_step = 0
    for epoch in range(1, NUM_EPOCHS + 1):
        for data, target in train_iterator:
            current_step += 1
            focal_label, margin_label = target, torch.eye(num_class).index_select(dim=0, index=target)
            if torch.cuda.is_available():
                data, focal_label, margin_label = data.to('cuda:{}'.format(GPU)), focal_label.to('cuda:{}'.format(GPU)), margin_label.to('cuda:{}'.format(GPU))
            # train model
            model.train()
            optimizer.zero_grad()
            classes = model(data)
            loss = focal_loss(classes, focal_label) + margin_loss(classes, margin_label)
            loss.backward()
            optimizer.step()
            # save the metrics
            meter_loss.add(loss.detach().cpu().item())
            meter_accuracy.add(classes.detach().cpu(), target)
            meter_confusion.add(classes.detach().cpu(), target)

            if current_step % NUM_STEPS == 0:
                # print the information about train
                train_loss_logger.log(current_step // NUM_STEPS, meter_loss.value()[0])
                train_accuracy_logger.log(current_step // NUM_STEPS, meter_accuracy.value()[0])
                train_confusion_logger.log(meter_confusion.value())
                results['train_loss'].append(meter_loss.value()[0])
                results['train_accuracy'].append(meter_accuracy.value()[0])
                print('[Step %d] Training Loss: %.4f Accuracy: %.2f%%' % (
                    current_step // NUM_STEPS, meter_loss.value()[0], meter_accuracy.value()[0]))
                reset_meters()

                # test model periodically
                model.eval()
                with torch.no_grad():
                    for data, target in test_iterator:
                        focal_label, margin_label = target, torch.eye(num_class).index_select(dim=0, index=target)
                        if torch.cuda.is_available():
                            data, focal_label, margin_label = data.to('cuda:{}'.format(GPU)), focal_label.to('cuda:{}'.format(GPU)), margin_label.to(
                                'cuda:{}'.format(GPU))
                        classes = model(data)
                        loss = focal_loss(classes, focal_label) + margin_loss(classes, margin_label)
                        # save the metrics
                        meter_loss.add(loss.detach().cpu().item())
                        meter_accuracy.add(classes.detach().cpu(), target)
                        meter_confusion.add(classes.detach().cpu(), target)
                    # print the information about test
                    test_loss_logger.log(current_step // NUM_STEPS, meter_loss.value()[0])
                    test_accuracy_logger.log(current_step // NUM_STEPS, meter_accuracy.value()[0])
                    test_confusion_logger.log(meter_confusion.value())
                    results['test_loss'].append(meter_loss.value()[0])
                    results['test_accuracy'].append(meter_accuracy.value()[0])

                # save best model
                if meter_accuracy.value()[0] > best_acc:
                    best_acc = meter_accuracy.value()[0]
                    if FINE_GRAINED and DATA_TYPE in ['reuters', 'yelp', 'amazon']:
                        torch.save(model.state_dict(), 'epochs/%s.pth' % (DATA_TYPE + '_fine_grained'))
                    else:
                        torch.save(model.state_dict(), 'epochs/%s.pth' % DATA_TYPE)
                print('[Step %d] Testing Loss: %.4f Accuracy: %.2f%% Best Accuracy: %.2f%%' % (
                    current_step // NUM_STEPS, meter_loss.value()[0], meter_accuracy.value()[0], best_acc))
                reset_meters()

                # save statistics
                out_path = 'statistics/'
                data_frame = pd.DataFrame(
                    data={'train_loss': results['train_loss'], 'train_accuracy': results['train_accuracy'],
                          'test_loss': results['test_loss'], 'test_accuracy': results['test_accuracy']},
                    index=range(1, current_step // NUM_STEPS + 1))
                if FINE_GRAINED and DATA_TYPE in ['reuters', 'yelp', 'amazon']:
                    data_frame.to_csv(out_path + DATA_TYPE + '_fine_grained' + '_results.csv', index_label='step')
                else:
                    data_frame.to_csv(out_path + DATA_TYPE + '_results.csv', index_label='step')
