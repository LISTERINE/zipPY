"""Zip cracker

Usage:
    zipPY.py <zipname> [-a -A -n -s -w --min=len --max=len --alerter=info]

Options:
    -h --help   Show this screen.
    -a          Use lowercase
    -A          Use uppercase
    -n          Use number
    -s          Use symbols
    -w          Use whitespace
    --min=len   Minimum password length [default: 3]
    --max=len   Maximum password length [default: 10]
    --alerter=info  Get text updates. rcpt@dom.com:sender@dom.com:sender_pass

"""
from docopt import docopt
import zipfile
from zipfile import _ZipDecrypter
from itertools import product
import string
from pdb import set_trace
from os import stat, mkdir, path
from shutil import copy2, move
from sys import stdout, exit
from multiprocessing import cpu_count, Process, Array
from ctypes import c_char_p
from time import sleep
from smtplib import SMTP

def crack(zip_name, pw_len, char_str, correct_pass_var):
    bytes = open(zip_name, 'rb').read(45+12)[-12:]
    z_file = zipfile.ZipFile(zip_name)
    extract_dir = path.split(zip_name)[0]
    test_target_name = z_file.namelist()[0]
    test_target_size = z_file.getinfo(test_target_name).file_size
    found = False
    for passwd in product(char_str, repeat=pw_len):
        passwd = "".join(passwd)
        try:
            z_file.extractall(path=extract_dir, pwd=passwd)
            extracted_file = path.join(extract_dir, test_target_name)
            if stat(extracted_file).st_size == test_target_size:
                print "\nPassword found:",passwd
                print "Extracted in",extract_dir
                z_file.close()
                correct_pass_var.value=passwd
                return
        except Exception:
            pass
        if correct_pass_var.value != "":
            return
    print "quitting",pw_len
    z_file.close()

class Messenger:
    #TODO Email duden wuuk sumtimes
    def __init__(self, phone, gmail, password):
        self.rcpt = phone # Number to text
        self.fromAddr = gmail # Address to send with
        self.emailPass = password # Email password

    def send_text(self, message):
	# SMTP connection times out, so login at send time
        self.server = SMTP("smtp.gmail.com:587")
        self.server.starttls()
        self.server.login(self.fromAddr, self.emailPass)
        self.server.sendmail(self.fromAddr, self.rcpt, message)
        self.server.quit()
        print "Message sent"


if __name__ == "__main__":
    # Set up parameters
    arguments = docopt(__doc__, version='1b')
    min_pwd = int(arguments["--min"])
    max_pwd = int(arguments["--max"])
    char_str = ""
    if arguments["-a"]:
        char_str += string.ascii_lowercase
    if arguments["-A"]:
        char_str += string.ascii_uppercase
    if arguments["-n"]:
        char_str += string.digits
    if arguments["-s"]:
        char_str += string.punctuation
    if arguments["-w"]:
        char_str += string.whitespace
    zip_name = arguments["<zipname>"]
    if arguments["--alerter"]:
        alerter = True
        rcpt, sndr, mail_pass = arguments["--alerter"].split(":")
        msg = Messenger(rcpt, sndr, mail_pass)
    else:
        alerter = False
    correct_pass = Array("c", 100)

    file_name = path.splitext(path.split(zip_name)[-1])[0]


    print "\nReticulating splines"
    num_cpus = cpu_count()
    zips = []
    for x in range(num_cpus):
        dir_name = file_name+str(x)
        mkdir(dir_name)
        copy2(zip_name, dir_name)
        zips.append(path.join(dir_name, zip_name))


    print "\n Beginning crack\n"
    running_procs = []
    for count, pw_len in enumerate(range(min_pwd, max_pwd)):
        proc = Process(target = crack, args = (zips[count%num_cpus], pw_len, char_str, correct_pass))
        running_procs.append(proc)
        proc.start()
        print "current password length:",pw_len
        print "possible passwords:", "{:,}".format(len(char_str)**pw_len)
        while len(running_procs) == num_cpus:
            sleep(5)
            for p_count, p in enumerate(running_procs):
                if not p.is_alive():
                    running_procs.pop(p_count)
            if correct_pass.value != "":
                break
        if correct_pass.value != "" and alerter:
            msg_text = "pw found: "+str(correct_pass.value)
            msg.send_text(msg_text)
            break
