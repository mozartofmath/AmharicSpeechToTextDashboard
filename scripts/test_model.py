import sys

from scripts.dataset_loader import load_audio_files, load_transcripts, load_spectrograms_with_transcripts, load_spectrograms_with_transcripts_in_batches
from scripts.resize_and_augment import resize_audios_mono, augment_audio, equalize_transcript_dimension
from scripts.transcript_encoder import fit_label_encoder, encode_transcripts, decode_predicted
#from jiwer import wer

import librosa   #for audio processing
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os
import logging

def perform_predictions(path):
    sample_rate = 44100

    audio_files, maximum_length = load_audio_files(path, sample_rate, True)
    logging.info('loaded audio files')

    print("The longest audio is", maximum_length/sample_rate, 'seconds long')
    #print("max length", maximum_length)

    demo_audio = list(audio_files.keys())[0]

    transcripts = load_transcripts("./data/trsTrain.txt")
    logging.info('loaded transcripts')

    audio_files = resize_audios_mono(audio_files, 440295)
    #print("resized shape", audio_files[demo_audio].shape)

    import pickle
    enc = open('./models/encoder.pkl', 'rb')
    char_encoder = pickle.load(enc)

    transcripts_encoded = encode_transcripts(transcripts, char_encoder)
    enc_aug_transcripts = equalize_transcript_dimension(audio_files, transcripts_encoded, 130)

    #print('model summary')

    import tensorflow as tf
    from scripts.new_model import LogMelgramLayer, CTCLayer

    def load_model():
        model = tf.keras.models.load_model('./models/new_model_v1_8500.h5', 
                                            custom_objects = {
                                                'LogMelgramLayer': LogMelgramLayer ,
                                                'CTCLayer': CTCLayer}
                                            )
        return model
    model = load_model()
    logging.info("Loaded Speech To Text Model")
    #print(model.summary())

    def load_data(audio_files, encoded_transcripts):
        X_train = []
        y_train = []
        for audio in audio_files:
            X_train.append(audio_files[audio])
            y_train.append(encoded_transcripts[audio])
        return np.array(X_train), np.array(y_train)

    X_test, y_test = load_data(audio_files, enc_aug_transcripts)
    print(X_test.shape, y_test.shape)

    if len(y_test) == 0:
        y_test = np.array([0]*70)

    predicted = model.predict([X_test,y_test])
    predicted_trans = decode_predicted(predicted, char_encoder)
    real_trans = [''.join(char_encoder.inverse_transform(y)) for y in y_test]
    logging.info("Computed predictions using the STT model")
    return X_test, predicted_trans, real_trans

#print(perform_predictions('./data/')[1])
# for i in range(len(y_test)):
#     print("Test", i)
#     print("pridicted:",predicted_trans[i])
#     print("actual:",real_trans[i])
#     #print("word error rate:", wer(real_trans[i], predicted_trans[i]))