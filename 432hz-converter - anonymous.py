import os, shutil, threading, pydub, mutagen, time

input_path = "" # Ex: 'C:/Users/.../Music/'
output_path = "" # Ex: 'C:/Users/.../Music/432/'
min_rating = 5
vel = 432 / 440
overwrite = False
append = " (432hz)"
just_copy = "432hz"
filetype = ".mp3"
maxthreads = 16

def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def slowDownFile(f):
    rating = 0
    f_path = f.path
    f_name = f.name
    tag_file = mutagen.File(f_path)
    try:
        rating = int(tag_file['TXXX:POPM'].text[0])
    except:
        pass
    if rating >= min_rating:
        if just_copy in f_name:
            shutil.copy(f_path, output_path)
            print("Copied: ", f_name)
        elif overwrite or not f_name[:-4] + append + filetype in existing_file_names:
            print("Converting: ", f_name)
            af = pydub.AudioSegment.from_file(f_path)
            af_new = speed_change(af, vel)
            new_path = output_path + f_name[:-4] + append + filetype
            af_new.export(new_path, format = 'mp3', parameters=["-q:a", "0"])
            new_tag_file = mutagen.File(new_path)
            new_tag_file = tag_file
            new_tag_file.save(new_path)
            print("Finished: ", f_name)
        else:
            print("File already exists: " + f_name)
    else:
        print("Rating not high enough: ", f_name)

threads = []
d = os.scandir(input_path)
try:
    os.mkdir(output_path)
except:
    pass
existing_file_names = [n.name for n in os.scandir(output_path)]
for f in d:
    t = threading.Thread(target=slowDownFile, args=(f,))
    threads.append(t)
for t in threads:
    while len([t for t in threads if t.is_alive()]) == maxthreads:
        time.sleep(0.05)
    t.start()
for t in threads:
    t.join()
