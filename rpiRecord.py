# -*- coding: utf-8 -*-
"""
Created on Mon Jun 18 13:16:16 2018

@author: nejck

This module includes classes needed for Nielsen far field voice processor
feasibility study. All classes are inherited from threading.Thread class, so they
can run in parallel.

RPI includes methods to run python file on raspberry pi, open socket, connect
to socket and record audio.

playWave is designed to play wav files in media folder within project

playRecord is designed to record wav files in /media/record folder

sineWave is for playing simple sine tones

"""

import os
import time
import wave
import socket

import numpy as np
import paramiko
import threading
import pyaudio
import logging

import config


DIRPATH = os.getcwd()
MEDIAPATH = os.path.join(DIRPATH, "media")
RECORDPATH = os.path.join(MEDIAPATH, "recording")

if not os.path.exists(MEDIAPATH):
    os.makedirs(MEDIAPATH)
if not os.path.exists(RECORDPATH):
    os.makedirs(RECORDPATH)

# turning off paramiko logger
logging.getLogger("paramiko").setLevel(logging.WARNING)


class RPI(threading.Thread):

    def __init__(self, **kwargs):#, duration=10, factorsLab=None):#, **kwargs):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(__name__)

#        self.duration = float(duration)
#        self.factorsLab = factorsLab
        for key in kwargs:
            setattr(self, key, kwargs[key])

        self._init_socket()


    def _init_socket(self):

        # dictionary with all key:values from RPI section
        self.rpi = dict(config.getConfig().items("RPI"))

        # create server
        host = socket.gethostbyname(socket.gethostname())
        port = 5000

        self.mySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # allow address to be immediately reused
        self.mySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mySock.bind((host, port))
        self.mySock.listen(1)


    def __call__(self, *args):
        return self.recordRPI(args)

    def connectRPI(self):

        print "ssh to rpi"
        self.logger.info("ssh to raspberry")
        # run client
        self.ssh_connect(self.rpi["url"], int(self.rpi["port"]), self.rpi["user"], self.rpi["passwd"])
        print "waiting for response"
        self.conn, addr = self.mySock.accept()
        self.logger.info("connection with raspberry estabilished")
        print "connection estabilished"


    def ssh_connect(self, host, port, user, passw):
        """
        Use ssh to turn client on. Inputs are self explanatory.
        """
        try:
            s = paramiko.SSHClient()
            s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            s.connect(host, port, user, passw)
            command = "python /home/pi/lucami.py"
            s.invoke_shell()
            (stdin, stdout, stderr) = s.exec_command(command)
            s.close
        except Exception as e:
            self.logger.error("Connection to raspberry failed: {}".format(e.message))
            print "Connection failed"
            print e

    def recordRPI(self, duration=10, factorsLab=None, opposite=None, adjacent=None, beamWidth=40, queue=None):
        args = (duration, factorsLab, opposite, adjacent, beamWidth)
        self.connectRPI()
        self.logger.info("Raspberry recording factorsLab {}".format(factorsLab))
        while 1:
            data = self.conn.recv(1024)
            if not data or data == "start recording": break
            if data == "send_data": self.conn.send(" ".join(args))
        self.conn.close()

    def close_socket(self):
        self.mySock.close()


class playWave(threading.Thread):
    """
    A simple class based on PyAudio to play wav file.
    It's a threading class. You can play audio while your application
    continues to do stuff.

    inputs: filename (string): file you want to play
            que (queue object): queue
            outDeviceDevice (string): TV (hdmi) or other (aux)
            duration (float): duration of playback. if greater than audio length,
                              loop audio
    """
    def __init__(self, filename, outDevice=None, duration=None, startTime=None, queue=None, nextActTrig=False):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.p = pyaudio.PyAudio()
#        self.outDeviceIndex = 4

        if outDevice == "TV":
            for i in range(self.p.get_device_count()):
                if "SAMSUNG" in self.p.get_device_info_by_index(i)["name"]:
                    self.outDevice = i
        else:
            for i in range(self.p.get_device_count()):
                if "Analog (3+4)" in self.p.get_device_info_by_index(i)["name"]:
                    self.outDevice = i

        self.filename = os.path.join(MEDIAPATH, filename)
        self.isplaying = None
        self.startTime = startTime
        if startTime:
            self.startTime = float(startTime)

        self.queue = queue
        self.nextActTrig = nextActTrig

        self.wf = wave.open(self.filename, 'rb')
        frames = self.wf.getnframes()
        self.rate = self.wf.getframerate()

        if not duration:
            self.duration = frames / float(self.rate)
        else:
            self.duration = float(duration)

        self.delta = 0
        self.CHUNK = 1024

    def run(self) :
        """
        Just another name for self.start()
        """

        if self.startTime:
            time.sleep(self.startTime)

        self.logger.debug("Playing {}".format(os.path.basename(self.filename)))

        self.isplaying=1

        self.stream = self.p.open(format=self.p.get_format_from_width(self.wf.getsampwidth()),
                        channels=self.wf.getnchannels(),
                        rate=self.rate,
                        output=True,
                        output_device_index=self.outDevice)

        self.logger.debug("Playing {}".format(os.path.basename(self.filename)))

        data = data = self.wf.readframes(self.CHUNK)
        self.start = time.time()

        print "Stream has been started at {}".format(self.start)

        while self.delta < self.duration and self.isplaying:
            self.stream.write(data)
#            data = self.wf.readframes(self.CHUNK)
            data = data = self.wf.readframes(self.CHUNK)
            self.delta = time.time() - self.start
            if data == "":
                self.wf.rewind()
                data = self.wf.readframes(self.CHUNK)

        print "Stream has been stopped at {}".format(self.start + self.delta)

        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.logger.debug("Playing {} complete".format(os.path.basename(self.filename)))

        # if queue object supplied, fill queue with timestamp
        if self.nextActTrig:
            self.queue.put(time.time())

    def stop(self):
        self.isplaying = 0

class recordWave(threading.Thread):
    """
    A simple class based on PyAudio to record wav file.
    It's a threading class. You can record audio while your application
    continues to do stuff.

    inputs: filename (string): file you want to store recording
            duration (float): duration of recording
    """

    def __init__(self, factorsLab, duration, startTime=None, queue=None, nextActTrig=False):

        threading.Thread.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.p = pyaudio.PyAudio()
        self.duration = duration # in seconds, may be float
        self.startRecording = None
        self.filename = factorsLab
        self.startTime = startTime
        self.queue = queue
        self.nextActTrig = nextActTrig
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
#        self.FORMAT = pyaudio.paFloat32
        self.CHANNELS = 1
        self.RATE = 48000
        if duration:
            self.RECORD_SECONDS = float(duration)
        else:
            self.RECORD_SECONDS = 3600
        self.playing = 1

    def run(self):

        if self.startTime:
            time.sleep(int(self.startTime))

        self.logger.debug("Recording {}".format(os.path.basename(self.filename)))

        stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
        frames = []
        self.startRecording = time.time()

        print("* recording --> {}".format(self.startRecording))

        for i in range(int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            if not self.playing:
                break
            data = stream.read(self.CHUNK)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        self.p.terminate()

        print("* done recording --> {}".format(time.time()))
        self.logger.debug("Recording of {} complete".format(os.path.basename(self.filename)))


        recordingFilename = os.path.join(RECORDPATH, "{}_REF_{}.wav".format(self.startRecording, self.filename))

        self.logger.debug("Storing {}".format(os.path.basename(self.filename)))

        # write wav
        wf = wave.open(recordingFilename, 'w')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        self.logger.debug("Storing of {} complete".format(os.path.basename(self.filename)))


        if self.nextActTrig:
            self.queue.put(time.time())

    def stop(self):
        self.playing = 0

class sineWave(threading.Thread):
    """simple threading class for generating sine waves"""

    def __init__(self, duration=2, frequency=400, volume=1, outDevice="TV", startTime=None, queue=None, nextActTrig=False):
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(__name__)

        self.duration = float(duration)
        self.frequency = int(frequency)
        self.p = pyaudio.PyAudio()
        self.volume = float(volume)
        self.rate = 44100
        self.startTime = startTime
        self.queue = queue
        self.nextActTrig = nextActTrig
#        if outDevice == "TV":
#            self.outDeviceIndex = 4
#        else:
#            self.outDeviceIndex = 4

        if outDevice == "TV":
            for i in range(self.p.get_device_count()):
                if "SAMSUNG" in self.p.get_device_info_by_index(i)["name"]:
                    self.outDevice = i
        else:
            for i in range(self.p.get_device_count()):
                if "Analog (3+4)" in self.p.get_device_info_by_index(i)["name"]:
                    self.outDevice = i


    def run(self):

        if self.startTime:
            time.sleep(float(self.startTime))

        self.logger.info("sine: {} s {} Hz".format(self.duration, self.frequency))
        # generate samples, note conversion to float32 array
        samples = (np.sin(2*np.pi*np.arange(self.rate*self.duration)*self.frequency/self.rate)).astype(np.float32)

        # for paFloat32 sample values must be in range [-1.0, 1.0]
        stream = self.p.open(format=pyaudio.paFloat32,
                            channels=1,
                            rate=self.rate,
                            output=True,
                            output_device_index=self.outDevice)


        self.logger.debug("Playing sineWave")
        # play. May repeat with different volume values (if done interactively)
        stream.write((self.volume*samples).tobytes())

        stream.stop_stream()
        stream.close()

        self.p.terminate()

        self.logger.debug("Playing sineWave finished")

        if self.nextActTrig:
            self.queue.put(time.time())