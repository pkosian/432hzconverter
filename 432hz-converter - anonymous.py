import os, shutil, threading, pydub, mutagen, time

inputPath = "" # Ex: 'C:/Users/.../Music/'
outputPath = "" # Ex: 'C:/Users/.../Music/432/'
minRating = 5
vel = 432 / 440
overwrite = False
append = " (432hz)"
justcopy = "432hz"
filetype = ".mp3"
maxthreads = 16

try:
    os.mkdir(outputPath)
except:
    pass

existingFileNames = [n.name for n in os.scandir(outputPath)]

def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def slowDownFile(f):
    rating = 0
    fpath = f.path
    tagfile = mutagen.File(fpath)
    try:
        rating = int(tagfile['TXXX:POPM'].text[0])
    except:
        pass
    if rating >= minRating:
        if justcopy in f.name:
            shutil.copy(f.path, outputPath)
            print("Copied: ", f.name)
        elif overwrite or not f.name[:-4] + append + filetype in existingFileNames:
            print("Converting: ", f.name)
            af = pydub.AudioSegment.from_file(fpath)
            afNew = speed_change(af, vel)
            newpath = outputPath + f.name[:-4] + append + filetype
            afNew.export(newpath, format = 'mp3', parameters=["-q:a", "0"])
            newTagFile = mutagen.File(newpath)
            newTagFile = tagfile
            newTagFile.save(newpath)
            print("Finished: ", f.name)
        else:
            print("File already exists: " + f.name)
    else:
        print("Rating not high enough: ", f.name)

threads = []
d = os.scandir(inputPath)
for f in d:
    t = threading.Thread(target=slowDownFile, args=(f,))
    threads.append(t)
for t in threads:
    while len([t for t in threads if t.is_alive()]) == maxthreads:
        time.sleep(0.1)
    t.start()
for t in threads:
    t.join()
