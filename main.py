#!/usr/bin/env python

import sys, requests, json, time

key = "api-key"
server_url = 'https://api.jakka.su/'


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

            filename = response.json()["message"]

            response = requests.get(server_url + "file", headers={'api-key': key}, json={'url': filename})
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
            else:
                print(response.json()['message'])
    else:
        print(response)
