![alt pump_logo](ux/public/images/icon.png)
> An app to cheer you up in those hard times


## About
Got the Monday blues?

Pmup (pronounced pŭmp) is the perfect "Pick Me Up" app for you. It uses advanced machine learning and artificial intelligence methods to detect the slightest hint of sadness in your voice and motivate you. In short, it listens, analyses and appreciates.

In order to alleviate ambiguity-resolution problem in text (For e.g., "I am okay" can be spoken in a variety of ways), we derive features from the *way* you speak too. Behind the scenes, it uses two models to analyze the speech input:

1.  **Acoustic:** It parses the audio-data from the microphone and extracts the [Mel-Frequency Cepstrum (MFC)]("https://en.wikipedia.org/wiki/Mel-frequency_cepstrum"). The MFC captures various properties of the sound like loudness, and pitch. It can be thought of as the features derived from the spectrogram which are the defacto visualisation for spoken audio data. Thus, we decided to feed the MFC features to a Convolutional Neural Network (CNN) which classifies the data into various emotions by generating a probability distribution over the classes. The model is trained on open source datasets: [RAVDESS](https://zenodo.org/record/1188976#.XHKbs4V7nCI) and [SAVEE](http://kahlan.eps.surrey.ac.uk/savee/Download.html)and has an accuracy of ~75%.

2.  **Text:** Next it uses the HTML5 speech2Text engine to convert captured audio to text. Here we've implemented an optimized version of [Compositional coding capsule network with k-means routing for text classification](https://arxiv.org/pdf/1810.09177v3.pdf), one of state-of-the-art methods for sentiment analysis in text. It basically uses [capsule nets](https://arxiv.org/abs/1710.09829) for multi-class classification of the text data. This model is trained on the Yelp reviews and Amazon polarity data, and has a test accuracy of ~94%.

Finally, we combine predictions from both the models to estimate emotions in real-time. Pmup, then, uses this inferred emotion to either tell you jokes, motivativational quotes or just be your pal.

## Setup instructions
Although we would be hosting the app online soon, you can follow the given steps to run the app locally:

- Clone this repository by `git clone git@github.com:Demfier/pmup.git` and switch to its root directory by `cd pmup`
- Install and setup the following dependencies on your system (using `virtualenv` is highly recommended):
  - NodeJS
  - Python3
  - Flask
  - PyTorch
  - Tensorflow
  - Numpy
  - Pandas
  - Keras (<=2.1.3)
  - Scikit-learn
  - Librosa
- Run `node index.js` from the `ux` folder to start your node server
- Open another terminal and run `flask run -p 8080` from the `webserver` folder
- Navigate to `https://localhost:5000` in your browser
- Tap the mic and start speaking
- Once you are finished, tap the mic again

Based on our algorithms, you should either hear a motivational quote if sad, or you'll hear a super-funny joke :wink:

## Privacy
Respecting privacy, we never store any voice data, or do any voice fingerprinting. All voice data is instantaneous analysed and deleted.

## Next steps
We found that combining results from both audio and text helps but still, the network seems to be very shallow and hence, we will now attempt to make an end-to-end deep learning model which processes text and audio at the same time by using some fusion techniques such as [LMF](http://anthology.aclweb.org/attachments/P/P18/P18-1209.Presentation.pdf) to learn a shared a representation for the different modalities

## Team members
[Gaurav](https://github.com/demfier), [Aseem](https://github.com/aseemrb), [Rishav](https://github.com/rra94)
