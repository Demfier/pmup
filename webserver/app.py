# app.py
from flask import Flask, request #import main Flask class and request object
from flask_cors import CORS, cross_origin
import torch
import pickle
from .model import Model
from .audio import audio_dep
import tensorflow as tf

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

loaded_model = tf.get_default_graph()
MODEL_DIR = './yelp.pth'
SENTENCE_ENCODER_PATH = './sentence_encoder'
# GPU = 1  # 0/1
model = Model(931271, num_class=2, routing_type='k_means', num_iterations=1)
sentence_encoder = pickle.load(open(SENTENCE_ENCODER_PATH, 'rb'))

def get_polarity(enc_text, model):
    with torch.no_grad():
        classes = model(enc_text)
        prob_sum = torch.sum(classes, dim=0)  # contains cumulative prob. for each class (0/1)
        print(prob_sum)
        return float(1 - (float(prob_sum[1])/prob_sum[0]))


@app.route('/', methods = ['POST'])
@cross_origin()
def audio_message():
    global loaded_model
    with loaded_model.as_default():
        # Open file and write binary (blob) data
        file_path = './file.wav'
        f = open(file_path, 'wb')
        f.write(request.data)
        f.close()
        x = audio_dep(file_path);
        # print(x)
        return str(x)

@app.route('/text', methods = ['POST'])
@cross_origin()
def text_message():
    print(request.data)
    text = str(request.data)
    model.load_state_dict(torch.load(MODEL_DIR, map_location='cpu'))
    enc_text = sentence_encoder.encode(text)
    model.eval()
    resp = get_polarity(enc_text, model)
    print(resp)
    return str(resp)


if __name__ == '__main__':
    app.run(debug=True, port=5000)  # run app in debug mode on port 5000
