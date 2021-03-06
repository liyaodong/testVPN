#!/usr/bin/env python2.7
import os
import argparse
import subprocess
from Queue import Queue
from threading import Thread
import time
import re

num_threads = 100
queue = Queue()
stat = []

best = {}
best['host'] = 'test.com'
best['speed'] = 500

def ping():
    global best
    while True:
        try:
            ip = queue.get()
        except Queue.Empty:
            return

        try:
            output = subprocess.check_output("ping -c 5 %s" % ip, shell=True, stderr=subprocess.STDOUT)
            line = output.rstrip().split("\n").pop()
            pattern = re.compile("round-trip min/avg/max/stddev = [0-9\.]+/([0-9\.]+)/[0-9\.]+/[0-9\.]+ ms")
            m = pattern.match(line)
            if m is not None:
                avgtime = m.group(1)
                print "%s: %s" % (ip, avgtime)
                if float(avgtime) < float(best['speed']):
                    best['host'] = ip
                    best['speed'] = avgtime
                stat.append((ip, avgtime))
        except subprocess.CalledProcessError:
            pass
        finally:
            time.sleep(3)
            queue.task_done()

def main():
    global best
    parser = argparse.ArgumentParser(description="ping multiple hosts")
    parser.add_argument("-f", "--file", help="a file contain host list, one line one host")
    parser.add_argument("hosts", nargs="*", metavar="HOST", help="host to ping")
    args = parser.parse_args()

    if args.file is not None:
        try:
            for line in open(args.file).readlines():
                line = line.strip()
                if line == "" or line[0] == "#":
                    continue
                args.hosts.append(line)
        except IOError:
            pass

    for ip in args.hosts:
        queue.put(ip.strip())

    for i in range(num_threads):
        worker = Thread(target=ping)
        worker.setDaemon(True)
        worker.start()

    queue.join()
    print "The best host is \033[92m %s : %s" % (best['host'], best['speed'])

if __name__ == "__main__":
    main()
