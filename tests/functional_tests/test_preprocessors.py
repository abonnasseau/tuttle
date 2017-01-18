# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE
from os.path import isfile, dirname, abspath, join

from os import path, environ
from tests.functional_tests import isolate, run_tuttle_file
import sys


class TestPreprocessors:

    @isolate
    def test_preprocessor_is_run(self):
        """ When a preprocessor is declared, it should be run after parsing """
        project = """|<<
    echo Running preprocess
    echo preprocess_has_run > preprocess_has_run
"""
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, output
        # Preprocesses should not leave anything after running
        # Kids, don't do it at home !
        assert isfile('preprocess_has_run')

    @isolate
    def test_preprocessor_is_in_report(self):
        """ Preprocessors should appear in the report """
        project = """|<<
    echo Running preprocess
"""
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, output
        report_path = join('.tuttle', 'report.html')
        assert isfile(report_path)
        report = open(report_path).read()
        # the code should appear in the html report
        code_pos = report.find("echo Running preprocess")
        assert code_pos > -1, code_pos

    @isolate(['A'])
    def test_no_preprocess_in_report(self):
        """ The report should not include a preprocess section if there are no preprocesses """
        project = """file://B <- file://A
    echo A produces B > B
"""
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, output
        report_path = join('.tuttle', 'report.html')
        assert isfile(report_path)
        report = open(report_path).read()
        code_pos = report.find("reprocess") # skip the first letter in upper case
        assert code_pos == -1, code_pos

    @isolate(['A'])
    def test_preprocess_should_not_force_invalidation(self):
        """ The existance of preprocesses should not invalidate all the resources (from bug)"""
        project = """file://B <- file://A
    echo A produces B > B

|<<
    echo Running preprocess
"""
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, output
        rcode, output = run_tuttle_file(project, threshold=0)
        assert rcode == 0, output
        pos = output.find("Nothing to do")
        assert pos >= 0, output

    def get_cmd_extend_workflow(self):
        """
        :return: A command line to call tuttle-extend-workflow even if tuttle has not been installed with pip
        """
        py_cli = sys.executable
        #if environ.has_key('VIRTUAL_ENV'):
        #    py_cli = join(environ['VIRTUAL_ENV'], 'Scripts', 'python')
        extend = abspath(join(__file__, '..', '..', '..', 'bin', 'tuttle-extend-workflow'))
        cmd_extend = '"{}" "{}"'.format(py_cli, extend)
        return cmd_extend

    @isolate(['A', 'b-produces-x.tuttle'])
    def test_call_extend(self):
        """ A preprocess should be able to call the tuttle-extend-workflow command"""
        cmd_extend = self.get_cmd_extend_workflow()
        project = """file://B <- file://A
    echo A produces B > B

|<<
    echo Expending workflow in preprocess
    echo "{cmd_extend} -h"
    {cmd_extend} -h
""".format(cmd_extend=cmd_extend)
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, "{} -> {}\n{}".format(cmd_extend, rcode, output)

    @isolate(['A', 'b-produces-x.tuttle'])
    def test_extend_workflow(self):
        """ One should be able to extend the workflow from a preprocess"""
        cmd_extend = self.get_cmd_extend_workflow()
        project = """file://B <- file://A
    echo A produces B > B

|<<
    echo Running preprocess
    {cmd_extend} b-produces-x.tuttle x="C"
""".format(cmd_extend=cmd_extend)
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, output
        report_path = join('.tuttle', 'report.html')
        assert isfile(report_path)
        report = open(report_path).read()
        pos_A = report.find("file%3A//A")
        assert pos_A > -1, output
        pos_C = report.find("file%3A//C")
        assert pos_C > -1, report[pos_A:]

    @isolate(['A'])
    def test_pre_process_fails(self):
        """ A preprocess should be able to call the tuttle-extend-workflow command"""
        cmd_extend = self.get_cmd_extend_workflow()
        project = """file://B <- file://A
    echo Should not be executed
    echo A produces B > B

|<<
    echo Failling
    Failling command
""".format(cmd_extend=cmd_extend)
        rcode, output = run_tuttle_file(project)
        assert rcode != 0, "{} -> {}\n{}".format(cmd_extend, rcode, output)
        pos = output.find("Should not be executed")
        assert pos == -1, output

    @isolate(['A', 'b-produces-x.tuttle'])
    def test_extend_workflow_from_python(self):
        """ One should be able to extend the workflow from python a preprocess"""
        cmd_extend = self.get_cmd_extend_workflow()
        project = """file://B <- file://A
    echo A produces B > B

|<< ! python
    from tuttle import extend_workflow
    print("Running a python preprocess")
    extend_workflow('b-produces-x.tuttle', x="C")
""".format(cmd_extend=cmd_extend)
        rcode, output = run_tuttle_file(project)
        assert rcode == 0, output
        report_path = join('.tuttle', 'report.html')
        assert isfile(report_path)
        report = open(report_path).read()
        pos_A = report.find("file%3A//A")
        assert pos_A > -1, output
        pos_C = report.find("file%3A//C")
        assert pos_C > -1, report[pos_A:]
