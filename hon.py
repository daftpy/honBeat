import os, sys, time, winsound
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic

# Pyinstaller stuff
def resource_path(relative_path):
    # Get absolute path to resource
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MainWorker(QRunnable):

    def __init__(self, bpm, beats, subvalue, *args, **kwargs):
        super(MainWorker, self).__init__()
        self.bpm = bpm
        self.beats = beats
        self.running = False
        # Subdivid is false to avoid subdividing before the first beat
        self.subdivide = False
        self.subvalue = subvalue

    def run(self):
        self.running = True
        self.beats = 4
        st = ct = time.perf_counter() # subdivide timer and current timer
        current_beat = 1
        sub_counter = 1
        while self.running:
            # If its time for a new beat, play the new beat
            if time.perf_counter() > ct + (60/self.bpm):
                if current_beat == 1: # Beat 1 gets a special emphasis
                    winsound.PlaySound("beat.wav", winsound.SND_ASYNC)
                    # After the very first beat, start subdividing
                    self.subdivide = True
                else: # other beats get a normal beat sound
                    winsound.PlaySound("beat2.wav", winsound.SND_ASYNC)
                if current_beat < self.beats:
                    current_beat += 1
                    # Turn the subdivider back on at the start of
                    # every new beat
                    self.subdivide = True
                else:
                    # Once we are at the end of beats go back to beat 1
                    current_beat = 1
                    self.subdivide = True # Make sure subdivison is back on
                    # if the metronome is already activated
                st = ct = time.perf_counter() # update both timers
            else:
                if self.subdivide:
                    # If its time to subdivide, play the subdivision
                    if time.perf_counter() > st + ((60/self.bpm)/self.subvalue) \
                        and current_beat >= 1:
                        winsound.PlaySound("sub.wav", winsound.SND_ASYNC)
                        sub_counter += 1
                        st = time.perf_counter()
                        if sub_counter >= self.subvalue:
                            # When the counter reaches the amount of
                            # subdivisions we need, turn it off
                            self.subdivide = False
                            sub_counter = 1
            time.sleep(.01) # for my processors sake

    def stop(self):
        self.running = False

    def adjust_bpm(self, bpm):
        self.bpm = bpm

    def adjust_beats(self, beats):
        self.beats = beats

    def adjust_subvalue(self, value):
        self.subvalue = value

    def toggle_metronome(self):
        self.running = not self.running
        if self.running is True:
            self.run()


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.threadpool = QThreadPool()
        self.mainworker = MainWorker(90, 4, 2)
        self.threadpool.start(self.mainworker)
        design = resource_path('design.ui')

        uic.loadUi(design, self)
        self.beatSlider.valueChanged.connect(
            lambda: self.beatsDisplay.setText(
                str(self.beatSlider.value())
            )
        )
        self.subdivisionSlider.valueChanged.connect(
            lambda: self.subdivisionDisplay.setText(
                str(self.subdivisionSlider.value())
            )
        )
        self.bpmDial.valueChanged.connect(
            lambda: self.bpmDisplay.setText(str(self.bpmDial.value()))
        )

        self.beatSlider.valueChanged.connect(
            lambda beats: self.mainworker.adjust_beats(beats)
        )
        self.subdivisionSlider.valueChanged.connect(
            lambda value: self.mainworker.adjust_subvalue(value)
        )
        self.bpmDial.valueChanged.connect(
            lambda bpm: self.mainworker.adjust_bpm(bpm)
        )

        self.playButton.clicked.connect(lambda: self.toggle_metronome())
        

    def closeEvent(self, event):
        print('closing')
        self.mainworker.stop()
        QMainWindow.closeEvent(self, event)

    def toggle_metronome(self):
        if self.mainworker.running == False:
            self.mainworker = MainWorker(
                self.bpmDial.value(),
                self.beatSlider.value(),
                self.subdivisionSlider.value()
            )
            self.threadpool.start(self.mainworker)
        else:
            self.mainworker.stop()

def main():
    app = QApplication(sys.argv)
    main = MainWindow()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
