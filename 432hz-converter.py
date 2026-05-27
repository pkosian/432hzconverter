import os, shutil, threading, pydub, mutagen, time, settings

def speed_change(sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def slowDownFile(f):
    f_path = f.path
    f_name = f.name
    print("Converting: ", f_name)
    af = pydub.AudioSegment.from_file(f_path)
    af_new = speed_change(af, settings.vel)
    new_path = settings.output_path + f_name[:-4] + settings.append + settings.filetype
    af_new.export(new_path, format = 'mp3', parameters=["-q:a", "0"])
    new_tag_file = mutagen.File(new_path)
    new_tag_file = mutagen.File(f_path)
    new_tag_file.save(new_path)
    print("Finished converting: ", f_name)

def copyFile(f):
    shutil.copy(f.path, settings.output_path)
    print("Copied: ", f.name)

if __name__ == "__main__":
    input = []
    output = []
    try:
        input = os.scandir(settings.input_path)
    except:
        print("Can't find input folder.")
    try:
        output = os.scandir(settings.output_path)
    except:
        try:
            output = os.mkdir(settings.output_path)
        except:
            print("Can't create new output folder.")
    input_array = []
    for f in input:
        input_array.append(f)
    output_array = []
    for f in output:
        output_array.append(f)
    # Gather files for conversion
    to_convert = []
    to_copy = []
    already_exists = []
    for f in input_array:
        tag_file = mutagen.File(f.path)
        rating = 0
        try:
            rating = int(tag_file['TXXX:POPM'].text[0])
        except:
            pass
        if rating >= settings.min_rating:
            if settings.just_copy in f.name:
                to_copy.append(f)
            elif settings.overwrite:
                to_convert.append(f)
            elif not (f.name[:-4] + settings.append + settings.filetype) in [o.name for o in output_array]:
                to_convert.append(f)
            else:
                already_exists.append(f)
                print("File already exists: " + f.name)
        else:
            print("Rating not high enough: " + f.name)
    # Delete remnant files
    for f in output_array:
        new_files = to_convert + to_copy + already_exists
        if not (f.name [:-12] + settings.filetype) in [nf.name for nf in new_files]:
            os.remove(f.path)
            print("Deleted remnant file: " + f.name)
    # Process files
    threads = []
    for f in to_copy:
        t = threading.Thread(target=copyFile, args=(f,))
        threads.append(t)
    for f in to_convert:
        t = threading.Thread(target=slowDownFile, args=(f,))
        threads.append(t)
    for t in threads:
        while len([t for t in threads if t.is_alive()]) == settings.maxthreads:
            time.sleep(0.05)
        t.start()
    for t in threads:
        t.join()
