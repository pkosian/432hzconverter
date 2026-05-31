import os, shutil, threading, pydub, mutagen, time, settings, queue

def speed_change (sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def slowDownFile (f):
    f_name = f.name
    f_path = f.path
    print("Converting: ", f_name)
    af = pydub.AudioSegment.from_file(f_path)
    af_new = speed_change(af, settings.vel)
    new_path = settings.output_path + f_name[:-4] + settings.append + settings.filetype
    af_new.export(new_path, format = 'mp3', parameters=["-q:a", "0"])
    new_tag_file = mutagen.File(new_path)
    new_tag_file = mutagen.File(f_path)
    new_tag_file.save(new_path)
    print("Finished converting: ", f_name)

def copyFile (f):
    shutil.copy(f.path, settings.output_path)
    print("Copied: ", f.name)

def checkConditions (f, q):
    tag_file = mutagen.File(f.path)
    rating = 0
    try:
        rating = int(tag_file['TXXX:POPM'].text[0])
    except:
        pass
    if rating >= settings.min_rating:
        if settings.just_copy in f.name:
            q.put(["to_copy", f])
        elif settings.overwrite:
            q.put(["to_convert", f])
        elif not (f.name[:-4] + settings.append + settings.filetype) in [o.name for o in output_array]:
            q.put(["to_convert", f])
        else:
            if settings.remove_remnants:
                print("File already exists: " + f.name)
                q.put(["already_exists", f])
    else:
        print("Rating not high enough: " + f.name)

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
    gather_threads = []
    q = queue.Queue()
    for f in input_array:
        t = threading.Thread(target=checkConditions, args=(f,q))
        gather_threads.append(t)
    for gt in gather_threads:
        while len([t for t in gather_threads if t.is_alive()]) == settings.maxthreads:
            time.sleep(0.05)
        gt.start()
    for gt in gather_threads:
        gt.join()
    to_convert = []
    to_copy = []
    already_exists = []
    while not q.empty():
        result = q.get()
        if result[0] == "to_convert":
            to_convert.append(result[1])
        elif result[0] == "to_copy":
            to_copy.append(result[1])
        elif result[0] == "already_exists":
            already_exists.append(result[1])
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
