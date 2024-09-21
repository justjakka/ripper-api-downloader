#!/usr/bin/env python

import sys, requests, json, time, subprocess, os

from mutagen.mp4 import MP4
from mutagen.flac import FLAC
from subprocess import call

key = "api-key"
server_url = 'https://api.jakka.su/'

def convert_m4a():
    m4as = []
    metadata = {}
    for subdir, dirs, files in os.walk('./'):
        for file in files:
            if file.endswith(".m4a"):
                m4as.append(file)
                flac = file[:-4] + ".flac"
                metadata[file] = flac
                call(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", file, flac])
                call(["flac", "-8", "-f", flac])


    for m4a in m4as:
        m4a_a = MP4(m4a)
        flac_a = FLAC(metadata[m4a])
        flac_a.delete()
        flac_a["TITLE"] = m4a_a["\xa9nam"]
        flac_a["ALBUM"] = m4a_a["\xa9alb"]
        flac_a["ARTIST"] = m4a_a["\xa9ART"]
        flac_a["ALBUMARTIST"] = m4a_a["aART"]
        flac_a["DATE"] = '.'.join(m4a_a["\xa9day"][0].split('-'))
        try:
            flac_a["DISCNUMBER"] = str(m4a_a["disk"][0][0])
        except Exception:
            pass
        try:
            if str(m4a_a["disk"][0][1]) == '' or str(m4a_a["disk"][0][1]) == '0':
                flac_a["DISCTOTAL"] = "1"
            else:
                flac_a["DISCTOTAL"] = str(m4a_a["disk"][0][1])
        except Exception:
            pass
        flac_a["TRACKNUMBER"] = str(m4a_a["trkn"][0][0])
        flac_a["TRACKTOTAL"] = str(m4a_a["trkn"][0][1])
        flac_a.save()
        os.remove(m4a)

if __name__ == '__main__':
    response = requests.post(server_url, headers={'api-key': key}, json={'url': sys.argv[1]})

    if response.headers['Content-Type'] == 'application/json':
        if response.status_code != 202:
            print(response.json()['message'])
        else:
            jobid = response.json()['message']
            time.sleep(0.5)
            response = requests.get(server_url + "job", headers={'api-key': key}, json={'jobid': str(jobid)})
            msg = response.json()['message']
            print()
            while msg != 'completed':
                if msg == "retry" or msg == "archived":
                    sys.stdout.write("Error: " + response.json()['message'])
                    sys.stdout.flush()
                    exit(1)
                elif msg == "active":
                    print ("\033[A                             \033[A")
                    sys.stdout.write("Processing")
                    sys.stdout.flush()
                    time.sleep(0.5)
                    for _ in range(3):
                        sys.stdout.write(".")
                        sys.stdout.flush()
                        time.sleep(0.5)
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    response = requests.get(server_url + "job", headers={'api-key': key}, json={'jobid': str(jobid)})
                    msg = response.json()['message']
                elif msg == "aggregating" or msg == "scheduled" or msg == "pending":
                    print ("\033[A                             \033[A")
                    sys.stdout.write("In queue")
                    sys.stdout.flush()
                    time.sleep(0.5)
                    for _ in range(3):
                        sys.stdout.write(".")
                        sys.stdout.flush()
                        time.sleep(0.5)
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    response = requests.get(server_url + "job", headers={'api-key': key}, json={'jobid': str(jobid)})
                    msg = response.json()['message']
                else:
                    if response.status_code == 200:
                        break
                    else:
                        sys.stdout.write("Error: " + response.json()['message'])
                        sys.stdout.flush()
                        exit(1)

            server_filename = response.json()["message"]
            filename = server_filename.split('/')[-1]

            response = requests.get(server_url + "file", headers={'api-key': key}, json={'url': server_filename})
            print ("\033[A                             \033[A")
            if response.headers.get('Content-Type') == 'application/zip':
                with open(filename, 'wb') as f:
                    print("Downloading ", filename.split('.zip')[0])
                    total_length = int(response.headers.get('content-length'))
                    dl = 0
                    for data in response.iter_content(chunk_size=4096):
                        dl += len(data)
                        f.write(data)
                        done = int(50 * dl / total_length)
                        sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )
                        sys.stdout.flush()
                print()

                subprocess.call(['7z', 'x', '-o' + filename.split('.zip')[0], filename])
                os.remove(filename)
                os.chdir("./" + filename.split('.zip')[0])
                convert_m4a()
            else:
                print(response.json()['message'])
    else:
        print(response)
