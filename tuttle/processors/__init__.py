#!/usr/bin/env python
# -*- coding: utf8 -*-

from os import path, chmod, stat
from stat import S_IXUSR, S_IXGRP, S_IXOTH
from subprocess import Popen, PIPE


def run_and_log(prog, log_stdout, log_stderr):
    fout = open(log_stdout, 'w')
    ferr = open(log_stderr, 'w')
    osprocess = Popen([prog], stdout=fout.fileno(), stderr=ferr.fileno(), stdin=PIPE)
    osprocess.stdin.close()
    fout.close()
    ferr.close()
    rcode = osprocess.wait()
    return rcode


def print_log_if_exists(log_file, header):
    with open(log_file, "r") as f:
        content = f.read()
        if len(content) > 1:
            print "--- {} : {}".format(header, "-" * (60 - len(header) - 7))
            print content


class ShellProcessor:
    """ A processor to run *nix shell code
    """
    name = 'shell'
    header = "#!/usr/bin/env sh\n"

    def generate_executable(self, code, process_id, directory):
        """ Create an executable file
        :param directory: string
        :return: the path to the file
        """
        script_path = path.join(directory, process_id)
        with open(script_path, "w+") as f:
            f.write(self.header)
            f.write(code)
        mode = stat(script_path).st_mode
        chmod(script_path, mode | S_IXUSR | S_IXGRP | S_IXOTH)
        return script_path

    def run(self, script_path, process_id, log_stdout, log_stderr):
        script_name = path.basename(script_path)
        print "=" * 60
        print script_name
        print "=" * 60
        prog = path.abspath(script_path)
        ret_code = run_and_log(prog, log_stdout, log_stderr)
        print_log_if_exists(log_stdout, "stdout")
        print_log_if_exists(log_stderr, "stderr")
        if ret_code:
            print "-" * 60
            print("Process {} failed".format(script_name))
        return ret_code


class BatProcessor:
    """ A processor for Windows command line
    """
    name = 'bat'
    header = "@echo off\n"
    exit_if_fail = 'if %ERRORLEVEL% neq 0 exit /b 1\n'

    def generate_executable(self, code, process_id, directory):
        """ Create an executable file
        :param directory: string
        :return: the path to the file
        """
        script_name = path.join(directory, "{}.bat".format(process_id))
        with open(script_name, "w+") as f:
            f.write(self.header)
            lines = code.split("\n")
            for line in lines:
                f.write(line)
                f.write("\n")
                f.write(self.exit_if_fail)
        return script_name

    def run(self, script_path, process_id, log_stdout, log_stderr):
        print "=" * 60
        print process_id
        print "=" * 60
        prog = path.abspath(script_path)
        ret_code = run_and_log(prog, log_stdout, log_stderr)
        print_log_if_exists(log_stdout, "stdout")
        print_log_if_exists(log_stderr, "stderr")
        if ret_code:
            print "-" * 60
            print
            print("Process {} failed with return code {}".format(process_id, ret_code))
        return ret_code

