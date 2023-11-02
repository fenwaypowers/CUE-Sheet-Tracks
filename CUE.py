import os
import sys
import subprocess
import argparse

# Dictionary to hold metadata information
metadata = {
    b"TITLE": [],
    b"PERFORMER": [],
    b"INDEX": [],
    b"REM COMPOSER": []
}

# Function to calculate time difference between two indexes
def timedif(i1, i2):
    i1, i2 = i1.split(":"), i2.split(":")
    a = (int(i1[0]) * 60) + int(i1[1])
    b = (int(i2[0]) * 60) + int(i2[1])
    return b - a

# Function to read CUE data
def cuedata(pth):
    try:
        with open(pth, "r", encoding="utf-8") as ff:
            f = ff.read()
    except UnicodeDecodeError:
        with open(pth, "r", encoding="iso-8859-1") as ff:
            f = ff.read()

    k = f.encode('utf-8')
    ff = k.split(b"TRACK")
    ff.pop(0)
    for i in ff:
        for spi in i.split(b"\n"):
            for ky in metadata:
                if ky in spi:
                    if ky == b"INDEX":
                        spi = spi.split(ky)[1].strip().split(b" ")[1]
                    else:
                        spi = spi.split(ky)[1].strip().strip(b'""')
                    metadata[ky].append(spi)
                    break
    return metadata

# Function to validate and correct the track title
def validtitle(name):
    for inva in ['/','\\','?','%','*',':', '|', '”', '<','>']:
        if inva in name:
            name = name.replace(inva, '')
    return name

# Main function for script execution
def main():
    # Create the parser
    parser = argparse.ArgumentParser(description='Extract tracks from a CUE file and add cover image to them.')
    
    # Add arguments
    parser.add_argument('-c', '--cover', help='Cover image file path', default=None)
    parser.add_argument('-q', '--cue', help='Directory containing CUE files', default=None)
    parser.add_argument('-e', '--extract', help='Directory to extract the tracks to', default=None)
    
    args = parser.parse_args()
    
    asmodeus = args.cover
    repm = args.cue
    dspth = args.extract
    
    # If the CUE directory was not specified, ask for it
    while not repm:
        repm = input("Location of CUE directory: ")
        if repm.lower() == "break":
            exit()
        if not os.path.exists(repm):
            print('Location not valid. Try again or use "break" to exit.')
        else:
            break
    
    # If the extract location was not specified, ask for it
    while not dspth:
        dspth = input("\nExtract Location (leave blank for current directory): ")
        if dspth.lower() == "break":
            exit()
        if dspth == "":
            break
        if not os.path.exists(dspth):
            print("Location not valid. Try again or use 'break' to exit.")
            dspth = None

    # Processing all CUE files in the given directory
    reps = os.listdir(repm)
    treatgm = 0
    for rep in reps:
        if rep.lower().endswith('.cue'):
            treatgm = 1
            chk = 0
            rep = repm + "\\" + rep
            for i in ['flac', 'm4a', 'mp3', 'aac', 'wav', 'ogg']:
                loc = rep[:-3] + i
                if os.path.exists(loc):
                    chk = 1
                    break
            if chk:
                datacu = cuedata(rep)
                mfile = loc
                ext = loc[loc.rindex('.'):]
                if not args.cover:
                    cimg = ["ffmpeg", "-hide_banner", "-y", "-i", mfile, "-an", "-vcodec", "copy", "cover.png"]
                    aimg = subprocess.run(cimg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    asmodeus = 'cover.png'

                a = 0
                b = 0
                wolfe = 0
                print("\n", "—"*55)
                for i in datacu[b'TITLE']:
                    i = i.decode('utf-8')
                    ior = validtitle(i)
                    track_number = str(a + 1)
                    otfl = f'{track_number}. {ior}_tmp{ext}'
                    otfl_fn = f'{track_number}. {ior}{ext}'
                    if dspth:
                        otfl = os.path.join(dspth, otfl)
                        otfl_fn = os.path.join(dspth, otfl_fn)
                    tit = f'title={i}'
                    artt = 'artist=' + datacu[b'PERFORMER'][a].decode('utf-8')
                    atime = datacu[b'INDEX'][b:b+2]
                    if len(atime) == 1:
                        wolfe = 1
                        stime = atime[0].decode('utf-8')
                    else:
                        stime, etime = atime[0].decode('utf-8').strip(), atime[1].decode('utf-8').strip()
                        diff = str(timedif(stime, etime))
                    stime = stime.rsplit(":", 1)[0]
                    a += 1
                    b += 2
                    trno = f'track={a}'
                    print(f"TRACK {a}: {i}")

                    # Building and executing the FFMPEG command
                    if wolfe:
                        if ext != '.flac':
                            cmd = ["ffmpeg", "-hide_banner", "-ss", stime, "-y", "-i", mfile, "-avoid_negative_ts", "make_zero", "-c", "copy", "-metadata", tit, "-metadata", artt, "-metadata", trno, otfl]
                        else:
                            cmd = ["ffmpeg", "-hide_banner", "-ss", stime, "-y", "-i", mfile, "-avoid_negative_ts", "make_zero", "-map", "0", "-metadata", tit, "-metadata", artt, "-metadata", trno, otfl]
                    else:
                        if ext != '.flac':
                            cmd = ["ffmpeg", "-hide_banner", "-ss", stime, "-y", "-i", mfile, "-t", diff, "-avoid_negative_ts", "make_zero", "-c", "copy", "-metadata", tit, "-metadata", artt, "-metadata", trno, otfl]
                        else:
                            cmd = ["ffmpeg", "-hide_banner", "-ss", stime, "-y", "-i", mfile, "-t", diff, "-map", "0", "-metadata", tit, "-metadata", artt, "-metadata", trno, otfl]
                    aa = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    # Adding album cover
                    cimgad = ['ffmpeg', '-hide_banner', '-y', '-i', otfl, '-i', asmodeus, '-map', '0:a', '-map', '1', '-codec', 'copy', '-metadata:s:v', 'title="Album cover"', '-metadata:s:v', 'comment="Cover (front)"', '-disposition:v', 'attached_pic', otfl_fn]
                    aimgad = subprocess.run(cimgad, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    os.remove(otfl)
                if not args.cover:
                    os.remove(asmodeus)
            else:
                print("\nAudio file not found.")
        else:
            print("\nNo CUE file found.")

# Entry point for the script
if __name__ == '__main__':
    main()
