# Audio-Visualizer
Takes WAV file and generates visualization as MP4
You can customize color gradient, number of sound bars, inspect audio file's frequency & volume graphs with pyFFTW & PyQT Graph

### Usage
Change audio file to your one (works only with WAV)
`audioFile = "MyAudioFile.wav"`

#### Optional settings
##### If you want to, you can set resolution of video
`w, h = 1920, 1080`
##### You can smoothen the audio curve for better visuals (this reduces the distance between maximum and minimum points of frequency magnitudes)
`sh *= (1 - (sh/h)**(1./2)) * 3. # 1./2 or 1./8 or 1./312 - n'th root: no limit`
##### You can change number of bars
`datas = visualize(100)   # 100 bars will be drawn`
##### If you want to see a larger protion of the frequency spectrum, increase f_ratio (min 0.0, max 1.0)
`f_ratio = 0.2`
##### You can change update frequency of frequency spectrum to get a smoother video (0.03 is actually perfect. Higher consumes much more RAM)
`update_periodicity = 0.03`
##### You can change background color of outout video (default: black)
`win.fill((0, 0, 0))`



### Cons (These could be optimized)
* Becomes very RAM intensive, if audio files are longer than 2 minutes.
* Requires some relatively hard-to-install modules
