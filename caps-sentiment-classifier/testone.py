import torch
import pickle
from model import Model


def get_polarity(enc_text, model):
    with torch.no_grad():
        classes = model(enc_text)
        prob_sum = torch.sum(classes, dim=0)  # contains cumulative prob. for each class (0/1)
        print(prob_sum)
        return (1 - (float(prob_sum[0])/prob_sum[1]))


if __name__ == '__main__':
    # while True:
    #     text = input('Enter a sentence to know it\'s sentiment (q to quit): ')
    #     if text == 'q':
    #         break
    #     model.load_state_dict(torch.load(MODEL_DIR))
    #     enc_text = sentence_encoder.encode(text)
    #     if torch.cuda.is_available():
    #         model.to('cuda:{}'.format(GPU))
    #         enc_text = enc_text.to('cuda:{}'.format(GPU))
    #     model.eval()
    #     print(get_polarity(enc_text, model))
