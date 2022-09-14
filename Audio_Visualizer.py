import math
import glob
import os

import pygame
import wave

import numpy as np
import pyfftw                    # https://stackoverflow.com/questions/25527291/fastest-method-to-do-an-fft
import multiprocessing

import pyqtgraph as pg
from PIL import Image
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
import time


audioFile = "AudioFile.wav"

w, h = 1920, 1080


# === Preparation of the audio data (init) === #
file = wave.open(audioFile, "rb")

data = np.frombuffer(file.readframes(-1), dtype=np.int32)  # int32 could cause an error if file is mono channel / different quality
n    = file.getnframes()         # array length
sr   = file.getframerate()       # sample rate (int)

val  = 1  # int(n * 0.01)            # How much percent of whole audio should it take as one bar/point? (data smoothening and reduction)
                                 # val = 1 -> default;  0.005-0.010 fine

# x/y-Axis of plot data
time_axis  = np.linspace(0, n/sr, int(n / val), endpoint=False)
sound_axis = data


# === Fourier transform of audio signal === #
def sound_ft(_sound_axis):
    _sound_ft = pyfftw.FFTW(
        _sound_axis.astype("complex64"),               # complex number (give the original sound values)
        np.zeros_like(_sound_axis).astype("complex64"),
        threads=multiprocessing.cpu_count(),
        direction='FFTW_FORWARD',
        flags=('FFTW_MEASURE', ),
        planning_timelimit=None
    )
    return _sound_ft()

magnitude_spectrum = np.abs(sound_ft(sound_axis))      # not complex array anymore, just magnitude

frequency          = np.linspace(0, sr, len(magnitude_spectrum))
f_ratio            = 0.2                               # i.e.: 0.5 = half of it;  1 -> default
num_frequency_bins = int(len(frequency) * f_ratio)     # check frequencies up to this level


# === Chart with PyQtGraph === #
py_layout = pg.GraphicsLayoutWidget()
py_layout.setWindowTitle("Audio Analysis: " + audioFile)

audio_graph = py_layout.addPlot(x=time_axis, y=sound_axis, row=0, col=0, title="Audio Volume Graph")
freq_graph  = py_layout.addPlot(x=frequency[:num_frequency_bins], y=magnitude_spectrum[:num_frequency_bins], row=1, col=0, title="Current Audio Frequency Map")

audio_graph.setLabel("left", "Audio Wave")
audio_graph.setLabel("bottom", "Time", units="s")
freq_graph.setLabel("left", "Magnitude")
freq_graph.setLabel("bottom", "Frequency", units="Hz")

track_line = pg.InfiniteLine(pos=0, pen="r")
audio_graph.addItem(track_line)

# py_layout.show()
# pg.QtWidgets.QApplication.instance().exec()  # uncomment for debugging


def play_audio():
    pygame.mixer.init()
    pygame.mixer.music.load(audioFile)
    pygame.mixer.music.play()

def mus_pos():
    return pygame.mixer.music.get_pos()/1000.0  # just get pos of playing music


update_periodicity = 0.03                       # secs  (refresh every X seconds -> to move the red line)


def show_audiotrack():
    global freq_graph

    py_layout.show()
    pygame.mixer.init()

    time_vals, freq_vals, magn_vals = process_data()

    play_audio()

    # ===> Play them afterwards
    while True:
    # Audio track

        # Delete red InfiniteLine (which was added before), create new updated one (push line)
        for g_item in audio_graph.allChildItems():
            if "InfiniteLine" in str(g_item):
                audio_graph.removeItem(g_item)
                break
        audio_graph.addItem(pg.InfiniteLine(pos=mus_pos(), pen="r"))


    # Audio frequency
        freq_graph.clear()
        freq_graph.plot().setData(
            freq_vals[math.floor(mus_pos() / update_periodicity)],
            magn_vals[math.floor(mus_pos() / update_periodicity)]
        )

        pg.QtWidgets.QApplication.processEvents()

        time.sleep(update_periodicity)

        if mus_pos() < 0:  break  # means music is over


def visualize(N=200):
    pygame.init()
    win = pygame.display.set_mode((w, h))
    pygame.display.set_caption("Audio Visualiser ({})".format(audioFile))
    pygame.display.init()

    vid_datas = []
    time_vals, freq_vals, magn_vals = process_data()
    val_num = len(freq_vals[0])

    sh_max  = max(max(a) for a in magn_vals)  # get max magnitude value of all times

    play_audio()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if mus_pos() < 0:
            break

        win.fill((0, 0, 0))


        # N: rect number on screen (take 1/N long part of frequency chart and show it as a rectangle), 200 fine!
        for i in range(N):
            # sound rect height
            try:
                sh = max( magn_vals[math.floor(mus_pos() / update_periodicity)][int(val_num * i/N):int(val_num * (i+1)/N)] ) / sh_max * h
            except Exception as e:
                _  = e
                sh = 0

            sh *= (1 - (sh/h)**(1./2)) * 3  # high sh values get reduced more, low ones less (smoothen the audio curve for visuals)

            color = (int(255 * (-i/N + 1)), 0, int(255 * i/N))
            pygame.draw.rect(win, color, (w/N * i + i, h/2 - max(sh, w/N/2), w/N, max(sh*2, w/N)), border_radius=30)


        pygame.display.flip()
        pygame.time.Clock().tick(80)  # update X times per second (FPS)

        # Record screen (append string data of img, later process it)
        vid_datas.append( pygame.image.tostring(win, "RGBA") )

    return vid_datas


def save_vid(vid_datas):
    t_ = time.time()

    fps    = len(vid_datas) / pygame.mixer.Sound(audioFile).get_length()  # https://github.com/baowenbo/DAIN
    images = [os.path.join(os.getcwd(), f"temp/img_{i}.jpg") for i in range(len(vid_datas))]

    # Create file
    if not os.path.exists(os.path.join(os.getcwd(), "temp")):  os.mkdir(os.path.join(os.getcwd(), "temp"))

    # Create images
    for i in range(len(vid_datas)):
        Image.frombytes("RGBA", (w, h), vid_datas[i]).convert('RGB').save(f"temp/img_{i}.jpg")
        print("\rPerforming:\tVideo conversion - {} secs".format(round(time.time() - t_, 4)), end="")

    # Create video
    clip = ImageSequenceClip(images, fps=fps)
    clip.write_videofile(os.path.join(os.getcwd(), "Visualizer_{}.mp4".format(audioFile.replace(".wav", ""))))


    # Remove all temporary data
    for f in glob.glob(os.path.join(os.getcwd(), "temp", '*')):
        os.remove(f)
    os.rmdir(os.path.join(os.getcwd(), "temp"))

    print("\rPerforming:\tVideo conversion - {} secs\t\t\t-> done".format(round(time.time()-t_, 4)))
    print("\tFPS: {} fps\n\tVideo length: {} secs\n\tAudio length: {} secs".format(
        round(fps, 3), clip.duration, pygame.mixer.Sound(audioFile).get_length()
    ))

    clip.close()




def process_data():
    print("Performing: Started preparation of data...")
    t = time.time()

    time_vals = []
    freq_vals = []  # nested array of frequencies
    magn_vals = []

    u_times = math.ceil(pygame.mixer.Sound(audioFile).get_length() / update_periodicity)

    # ===> Store all values beforehand
    for i in range(u_times):  # total update times
        dt = time.time()
        time_vals.append(update_periodicity * i)

        x = get_nearest_index(time_axis, (i * update_periodicity))
        y = get_nearest_index(time_axis, ((i + 3) * update_periodicity))  # 3... changeable

        _sound_ft = sound_ft(sound_axis[x:y])
        _magnitude_spectrum = np.abs(_sound_ft)
        _frequency = np.linspace(0, sr, len(_magnitude_spectrum))
        _nfb = int(len(_frequency) * f_ratio)

        freq_vals.append(_frequency[:_nfb])
        magn_vals.append(_magnitude_spectrum[:_nfb])
        print("\r\t" + str(i + 1) + " of " + str(u_times) + "\t\t" + str(round(time.time() - dt, 4)) + " secs", end="")

    print("\nFinished preparation of data (in {} secs)\n".format(time.time() - t))

    return [time_vals, freq_vals, magn_vals]


def get_nearest_index(array, value):
    return np.absolute(array - value).argmin()




# show_audiotrack()
# pg.QtWidgets.QApplication.instance().exec()  # if you want to retain that window opened, uncomment these


datas = visualize(100)
save_vid(datas)
