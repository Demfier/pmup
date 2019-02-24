'use strict';

const socket = io("127.0.0.1:5000");
const recogInput = document.querySelector('.recog-input');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();
recognition.lang = 'en-US';
recognition.interimResults = true;
recognition.maxAlternatives = 1;
recognition.continuous = true;

let interimTranscript = '';
let finalTranscript = '';
let reportTranscript = '';
let prevztranscriptIdx = 0;
var speakButton = document.querySelector('button[name="speak"]');
var off = true;
var blob = null;
var volume = null;
var audioInput = null;
var bufferSize;
var sampleRate;
var context;
var processor;
var livestream;
var source;
var leftchannel = [];
var rightchannel = [];
var recordingLength = 0;

speakButton.addEventListener('click', () => {
  off = !off;
  if (off)
  {
    recognition.stop();
    $('#listener').removeClass('lds-ring');

    source.disconnect(processor);
    processor.disconnect(context.destination);
    var tracks = livestream.getTracks();
    tracks.forEach(function(track) {
      track.stop()
    });

    recogInput.innerHTML = '<i style="color:#ddd;">Recognized speech appears here</i>';

    console.log('Audio stream stopped.');

    if(!reportTranscript)
    {
      if(finalTranscript)
      {
        reportTranscript = finalTranscript;
      }
      else if(interimTranscript)
      {
        reportTranscript = interimTranscript;
      }
    }

    console.log('Transcript to report: ' + reportTranscript);

    // we flat the left and right channels down
    var leftBuffer = mergeBuffers(leftchannel, recordingLength);
    var rightBuffer = mergeBuffers(rightchannel, recordingLength);
    // we interleave both channels together
    var interleaved = interleave(leftBuffer, rightBuffer);

    // we create our wav file
    var buffer = new ArrayBuffer(44 + interleaved.length * 2);
    var view = new DataView(buffer);

    // RIFF chunk descriptor
    writeUTFBytes(view, 0, 'RIFF');
    view.setUint32(4, 44 + interleaved.length * 2, true);
    writeUTFBytes(view, 8, 'WAVE');
    // FMT sub-chunk
    writeUTFBytes(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    // stereo (2 channels)
    view.setUint16(22, 2, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 4, true);
    view.setUint16(32, 4, true);
    view.setUint16(34, 16, true);
    // data sub-chunk
    writeUTFBytes(view, 36, 'data');
    view.setUint32(40, interleaved.length * 2, true);

    // write the PCM samples
    var lng = interleaved.length;
    var index = 44;
    var volume = 1;
    for (var i = 0; i < lng; i++){
        view.setInt16(index, interleaved[i] * (0x7FFF * volume), true);
        index += 2;
    }

    // Final binary blob
    blob = new Blob([ view ], { type : 'audio/wav' });

    // Send this blob to the python service.
    console.log('Audio blob object to report:');
    console.log(blob);

    // var data = {"text": reportTranscript};

    // var xhttp = new XMLHttpRequest();
    // xhttp.onreadystatechange = function() {
    //   if (this.readyState == 4 && this.status == 200) {
    //     // console.log(this.responseText);
    //   }
    // };
    // xhttp.open("POST", "/submitText/", true);
    // xhttp.setRequestHeader("Content-type", "application/json");
    // xhttp.send(JSON.stringify(data));

    // socket.emit('textinput', reportTranscript);

    $.ajax({
      type: 'POST',
      url: 'http://localhost:8080/',
      data: blob,
      processData: false,
      contentType: false
    }).done(function(audioResp) {
      $.ajax({
        type: 'POST',
        url: 'http://localhost:8080/text',
        data: reportTranscript,
        processData: false,
        contentType: false
      }).done(function(textResp) {
        audioResp = parseFloat(audioResp);
        textResp = parseFloat(textResp);
        console.log('Audio response: ', audioResp);
        console.log('Text response: ', textResp);
      });
    });

    // socket.emit('audioblob', blob);

    // // Prompt to save it locally
    // var url = (window.URL || window.webkitURL).createObjectURL(blob);
    // var link = window.document.createElement('a');
    // link.href = url;
    // link.download = 'output.wav';
    // var click = document.createEvent("Event");
    // click.initEvent("click", true, true);
    // link.dispatchEvent(click);
  }
  else
  {
    blob = null;
    finalTranscript = '';
    reportTranscript = '';
    leftchannel = [];
    rightchannel = [];
    recordingLength = 0;

    recognition.start();
    $('#listener').addClass('lds-ring');
    console.log('Audio stream started.');
    navigator
      .mediaDevices.getUserMedia({ audio: true, video: false })
      .then(function(stream) {
        livestream = stream;
        context = new AudioContext();
        bufferSize = 1024;
        processor = context.createScriptProcessor(bufferSize, 1, 1);
        source = context.createMediaStreamSource(stream);

        source.connect(processor);
        processor.connect(context.destination);
        sampleRate = context.sampleRate;
        volume = context.createGain();

        // creates an audio node from the microphone incoming stream
        audioInput = context.createMediaStreamSource(stream);

        // connect the stream to the gain node
        audioInput.connect(volume);

        processor.onaudioprocess = function(e) {
          // This is the raw data stream.
          var numChannels = e.inputBuffer.numberOfChannels;

          // We clone the samples
          leftchannel.push(new Float32Array(e.inputBuffer.getChannelData(0)));

          if(numChannels > 1) {
            rightchannel.push(new Float32Array(e.inputBuffer.getChannelData(1)));
          }

          recordingLength += bufferSize;
          // console.log(e);
        };
    });
  }
});

recognition.onresult = (event) => {
  interimTranscript = '';
  for (let i = event.resultIndex, len = event.results.length; i < len; i++) {
    let transcript = event.results[i][0].transcript;
    if (event.results[i].isFinal) {
      finalTranscript = transcript;
      reportTranscript += transcript;
    } else {
      interimTranscript += transcript;
    }
  }
  console.log(interimTranscript);
  if(interimTranscript) {
    recogInput.innerHTML = '<i style="color:#ddd;">' + interimTranscript + '</i>';
  } else {
    recogInput.innerHTML = finalTranscript;
  }
};

recognition.onerror = (err) => {
  console.log("Error in speech recognition: " + err);
};

function interleave(leftChannel, rightChannel){
  var length = leftChannel.length + rightChannel.length;
  var result = new Float32Array(length);

  var inputIndex = 0;

  for (var index = 0; index < length; ){
    result[index++] = leftChannel[inputIndex];
    result[index++] = rightChannel[inputIndex];
    inputIndex++;
  }
  return result;
}

function mergeBuffers(channelBuffer, recordingLength){
  var result = new Float32Array(recordingLength);
  var offset = 0;
  var lng = channelBuffer.length;
  for (var i = 0; i < lng; i++){
    var buffer = channelBuffer[i];
    result.set(buffer, offset);
    offset += buffer.length;
  }
  return result;
}

function writeUTFBytes(view, offset, string){
  var lng = string.length;
  for (var i = 0; i < lng; i++){
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}

function synthVoice(text) {
  const synth = window.speechSynthesis;
  const utterance = new SpeechSynthesisUtterance();
  utterance.text = text;
  synth.speak(utterance);
}

socket.on('speakJoke', function(txt) {
  console.log("Trying to speak a joke: ", txt);
  if(txt) synthVoice(txt);
});

socket.on('speakQuote', function(txt) {
  console.log("Trying to speak a quote: ", txt);
  if(txt) synthVoice(txt);
});
