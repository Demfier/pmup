#app.py

from flask import Flask, request #import main Flask class and request object
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/', methods = ['POST'])
@cross_origin()
def audio_message():
    # Open file and write binary (blob) data
    f = open('./file.wav', 'wb')
    f.write(request.data)
    f.close()
    return "Binary message written!"

if __name__ == '__main__':
    app.run(debug=True, port=5000) #run app in debug mode on port 5000
