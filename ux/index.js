'use strict';

const express = require('express');
const app = express();
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');
const quotes = require('./consts.js');

// Set up quotes.
var quoteCollection = {};
quoteCollection.quotes = [];
for(var i = 0; i < quotes.sad.length; i = i + 2)
{
  quoteCollection.quotes.push({"author": quotes.sad[i+1], "quote": quotes.sad[i]});
}

// Every joke has a type, a setup and a punchline.
quoteCollection.jokes = quotes.jokes;

// console.log(quoteCollection.jokes);
// console.log(quoteCollection.quotes);

app.use(bodyParser.json({ limit: '50mb' }));
app.use(bodyParser.raw({ type: 'audio/wav', limit: '50mb' }));
app.use(bodyParser.urlencoded({ extended: true })); // for parsing application/x-www-form-urlencoded

app.use(express.static(__dirname + '/views')); // html
app.use(express.static(__dirname + '/public')); // js, css, images

var views = path.join(__dirname, 'views');

const server = app.listen(process.env.PORT || 5000, () => {
  console.log('Express server listening on port %d in %s mode', server.address().port, app.settings.env);
});

const io = require('socket.io')(server);
io.on('connection', function(socket){
  console.log('--- INFO: Incoming connection');
});

// Web UI
app.get('/', (req, res) => {
  res.sendFile(path.join(views, 'index.html'));
});

app.get('/about/', (req, res) => {
  res.sendFile(path.join(views, 'about.html'));
});

app.post('/submitText/', (req, res) => {
  console.log("Request received: ", req.body);
  res.send('Text received');
});

app.post('/submitAudio/', (req, res) => {
  console.log("Request received: ", req.body);
  res.send('Audio received');
});

io.on('connection', function(socket) {
  socket.on('textinput', (text) => {
    console.log('--- TEXT: ' + text);

    // This will be based on mood analysis.
    tellaquote();
    // tellajoke();
  });

  let tellajoke = function() {
    console.log('Sending a joke');
    let idx = Math.floor(Math.random() * quotes.jokes.length);
    console.log('Joke: ' + quotes.jokes[idx].setup + ' ' + quotes.jokes[idx].punchline);
    socket.emit('speakJoke', quotes.jokes[idx].setup);
    setTimeout(function() {
      socket.emit('speakJoke', quotes.jokes[idx].punchline)
    }, 3000);
  }

  let tellaquote = function() {
    console.log('Sending a quote');
    let idx = Math.floor(Math.random() * quoteCollection.quotes.length);
    console.log(
      'Quote: ' + quoteCollection.quotes[idx].quote +
      ', Author: ' + quoteCollection.quotes[idx].author);

    let pi = Math.floor(Math.random() * quotes.cheers.length);
    let primer =
      quotes.cheers[pi].first + quoteCollection.quotes[idx].author +
      quotes.cheers[pi].second;
    socket.emit('speakQuote', primer);

    setTimeout(function() {
      socket.emit('speakQuote', quoteCollection.quotes[idx].quote)
    }, 3000);
  }

  // socket.on('audioblob', (blob) => {
  //   console.log(blob);
  //   var fileReader = new FileReader();
  //   fileReader.onload = function() {
  //     fs.writeFileSync('test.wav', Buffer.from(new Uint8Array(this.result)));
  //   };
  //   fileReader.readAsArrayBuffer(blob);
  // });
});
