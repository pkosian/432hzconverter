import os, shutil, threading, pydub, mutagen, time, settings, queue

def speed_change (sound, speed=1.0):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def slowDownFile (f):
    print("Converting: ", f[1])
    af = pydub.AudioSegment.from_file(f[0])
    af_new = speed_change(af, settings.vel)
    new_path = settings.output_path + f[1][:-4] + settings.append + settings.filetype
    af_new.export(new_path, format = 'mp3', parameters=["-q:a", "0"])
    new_tag_file = mutagen.File(new_path)
    new_tag_file = mutagen.File(f[0])
    new_tag_file.save(new_path)
    print("Finished converting: ", f[1])

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
            q.put(["to_copy", [f.path, f.name]])
        elif settings.overwrite:
            q.put(["to_convert", [f.path, f.name]])
        elif not (f.name[:-4] + settings.append + settings.filetype) in [o.name for o in output_array]:
            q.put(["to_convert", [f.path, f.name]])
        else:
            if settings.remove_remnants:
                print("File already exists: " + f.name)
                q.put(["already_exists", [f.path, f.name]])
    else:
        print("Rating not high enough: " + f.name)

def getActiveThreadCount (threads):
    return len([t for t in threads if t.is_alive()])

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
    q.put(["initialize queue"]) # Pseudo element to prevent skipping, see line 82
    for f in input_array:
        t = threading.Thread(target=checkConditions, args=(f,q))
        gather_threads.append(t)
    for gt in gather_threads:
        while getActiveThreadCount(gather_threads) == settings.maxthreads:
            time.sleep(0.05)
        gt.start()
    to_convert = []
    to_copy = []
    already_exists = []
    while not q.empty(): # Would only work if a thread is fast enough to fill the queue, hence prefilling it with a pseudo element
        result = q.get()
        if result[0] == "to_convert":
            to_convert.append(result[1])
        elif result[0] == "to_copy":
            to_copy.append(result[1])
        elif result[0] == "already_exists":
            already_exists.append(result[1])
    for gt in gather_threads:
        gt.join()
    # Delete remnant files
    for f in output_array:
        new_files = to_convert + to_copy + already_exists
        if not (f.name [:-12] + settings.filetype) in [nf[1] for nf in new_files]:
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
        while getActiveThreadCount(threads) == settings.maxthreads:
            time.sleep(0.05)
        t.start()
    for t in threads:
        t.join()
