# -*- coding: utf-8 -*-

from tests.functional_tests import isolate
from tuttle.project_parser import *


class TestLineStreamer():

    @isolate(['test_project_parser.py'])
    def test_read_lines(self):
        """FileStreamer should provide a lines from a file"""
        streamer = LinesStreamer()
        streamer.add_file('test_project_parser.py')
        (line, file, num, eos) = streamer.read_line()
        assert line == '# -*- coding: utf-8 -*-', line
        assert num == 1, num
        (line, file, num, eos) = streamer.read_line()
        assert line == '', line
        assert num == 2, num

    @isolate(['utf8_file.txt'])
    def test_read_utf8_lines(self):
        """FileStreamer should provide a lines from a file"""
        streamer = LinesStreamer()
        streamer.add_file('utf8_file.txt')
        (line, file, num, eos) = streamer.read_line()
        assert line == u'une ligne accentuée', line
        assert num == 1, num

    @isolate(['utf8_file.txt'])
    def test_end_of_stream(self):
        """FileStreamer should return eos==True when there is nothing to read after"""
        streamer = LinesStreamer()
        streamer.add_file('utf8_file.txt')
        (line, file, num, eos) = streamer.read_line()
        assert num == 1, num
        (line, file, num, eos) = streamer.read_line()
        assert num == 2, num
        (line, file, num, eos) = streamer.read_line()
        assert eos, "Should have reached end of stream"

    @isolate(['utf8_file.txt',])
    def test_streamer_should_work_on_several_files(self):
        """FileStreamer should stream lines from several files"""
        streamer = LinesStreamer()
        streamer.add_file('utf8_file.txt')
        (line, file, num, eos) = streamer.read_line()
        assert num == 1, num
        streamer.add_file('utf8_file.txt')
        (line, file, num, eos) = streamer.read_line()
        assert num == 2, num
        (line, file, num, eos) = streamer.read_line()
        assert num == 1, num
        (line, file, num, eos) = streamer.read_line()
        assert num == 2, num
        (line, file, num, eos) = streamer.read_line()
        assert eos, "Should have reached end of stream"

    def test_streamer_should_stream_lines_from_text(self):
        """FileStreamer should stream lines from initial_text"""
        streamer = LinesStreamer("""Line 1
        Line 2""")
        (line, file, num, eos) = streamer.read_line()
        assert num == 1, num
        assert not eos, eos
        (line, file, num, eos) = streamer.read_line()
        assert num == 2, num
        assert not eos, eos
        (line, file, num, eos) = streamer.read_line()
        assert eos, eos


class TestProjectParser():

    def test_is_blank_if_empty(self):
        """Empty line should be considered blank"""
        pp = ProjectParser()
        line = "\n"
        assert pp.is_blank(line) is True

    def test_is_blank_if_blank_cars(self):
        """Line with blank characters should be blank"""
        pp = ProjectParser()
        line = "  \t \n"
        assert pp.is_blank(line) is True

    def test_is_blank_if_comment(self):
        """Line with comment should be blank"""
        pp = ProjectParser()
        line = "# un commentaire accentu�\n"
        assert pp.is_blank(line) is True

    def test_indented_line_should_not_be_blank(self):
        """Indented line should not be blank"""
        pp = ProjectParser()
        line = "\ttest"
        assert pp.is_blank(line) is False

    def test_simple_read_section(self):
        """Simple dependency line should return dependencies"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 1
        assert process._inputs[0].url == 'file:///source1'
        assert len(process._outputs) == 1
        assert process._outputs[0].url == 'file:///result1'
        assert process._outputs[0].creator_process == process
        # TODO : get back to shell processors by default
        # assert process._processor.name == "shell"
        assert process._code == "Some code\n"

    def test_read_section_with_blank_line(self):
        """A blank line between dependency definition an process code should be ignored"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1

        Some code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 1
        assert process._inputs[0].url == 'file:///source1'
        assert len(process._outputs) == 1
        assert process._outputs[0].url == 'file:///result1'
        print process._code
        assert process._code == "Some code\n"

    def test_quoted_resources_can_contain_spaces(self):
        pp = ProjectParser()
        project = """'file:///result1 1'  file:///result2 <- file:///source1 'file:///source2 2'
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 2
        assert len(process._outputs) == 2

    def test_read_section_multiple_inputs_and_outputs(self):
        """Read a sections with multiple inputs and outputs"""
        pp = ProjectParser()
        project = """file:///result1,  file:///result2,  file:///result3 <- file:///source1, file:///source2
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 2
        assert process._inputs[0].url == 'file:///source1'
        assert process._inputs[1].url == 'file:///source2'
        assert len(process._outputs) == 3
        assert process._outputs[0].url == 'file:///result1'
        assert process._outputs[1].url == 'file:///result2'
        assert process._outputs[2].url == 'file:///result3'
        assert process._code == "Some code\n"

    def test_read_section_with_invalid_input(self):
        """A section with an invalid / unrecognised input url should raise an Exception"""
        pp = ProjectParser()
        project = """file:///result1 <- source1.csv
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        try:
            process = pp.parse_section()
            assert False
        except ParseError:
            assert True

    def test_read_section_with_invalid_output(self):
        """A section with an invalid / unrecognised input url should raise an Exception"""
        pp = ProjectParser()
        project = """result1.csv <- file:///source1.csv
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        try:
            process = pp.parse_section()
            assert False
        except ParseError:
            assert True

    def test_read_section_without_process_code(self):
        """Read a sections without process code"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 1
        assert process._inputs[0].url == 'file:///source1'
        assert len(process._outputs) == 1
        assert process._outputs[0].url == 'file:///result1'
        assert process._code == ""

    def test_read_last_line_of_a_section(self):
        """Read a sections without process code"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
        bla
"""
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        print "'{}'".format(process._code)
        assert process._code == "bla\n"

    def test_read_last_unfinished_line_of_a_section(self):
        """Read a sections without process code"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
        bla"""
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        print "'{}'".format(process._code)
        assert process._code == "bla\n"

    def test_read_section_with_indentation_error_in_process_code(self):
        """Read a section with an indentation error in process code"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
          Some code
        More code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 1
        assert process._inputs[0].url == 'file:///source1'
        assert len(process._outputs) == 1
        assert process._outputs[0].url == 'file:///result1'
        assert process._code == "Some code\n"

    def test_pasrse_simple_workflow(self):
        """Read project with a blank line with blank characters which match exactly the indentation of the code of the process"""
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
        Some code""" + "\n        \n" + """file:///resource2 <- file:///resource3
        Some code
        More code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 2

    def test_workflow_without_new_line_in_the_end(self):
        """The last line of a process should not be forgotten"""
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
        Some code"""
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        assert workflow._processes[0]._code == "Some code\n"

    def test_pasrse_workflow_with_blank_lines(self):
        """Read project with a blank line with any number of blank characters"""
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
        Some code""" + "\n  \n" + """file:///resource2 <- file:///resource3
        Some code
        More code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 2

    def test_pasrse_workflow_with_0_char_blank_lines(self):
        """Read a simple project where lines separating two processes are empty"""
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
        Some code""" + "\n \n" + """file:///resource2 <- file:///resource3
        Some code
        More code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 2

    def test_pasrse_workflow_with_indentation_error(self):
        """Read a project with indentation error on first process"""
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
          Some code
        More code

file:///resource2 <- file:///resource3
        Some code2
        """
        pp.set_project(project)
        try:
            workflow = pp.parse_project()
            assert False
        except ParseError:
            assert True

    def test_output_can_come_from_only_one_process(self):
        """A section extracted from the parser should build a process"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
        Some code

file:///result1 <- file:///source1
        other code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        try:
            process = pp.parse_section()
            assert False
        except WorkflowError:
            assert True

    def test_resources_should_be_equals_across_processes(self):
        """Two processes using the same url should use the same resource object"""
        pp = ProjectParser()
        project = """file:///result1 <- file:///source1
        Some code

file:///result2 <- file:///source1
        other code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert workflow._processes[0]._inputs[0] == workflow._processes[1]._inputs[0]

    def test_project_should_begin_by_resources(self):
        """A project beginning by an invalid resource definition should raise an error"""
        pp = ProjectParser()
        project = """Bla
file:///result1 <- file:///source1
        Some code
        """
        pp.set_project(project)
        try:
            process = pp.parse_project()
            assert False
        except ParseError:
            assert True

    def test_a_project_can_have_one_unfinished_line(self):
        """Test the project can have only one line and even no carriage return at the end"""
        pp = ProjectParser()
        project = "file://result <- file://source"
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        assert len(workflow._processes[0]._inputs) == 1
        assert len(workflow._processes[0]._outputs) == 1

    def test_a_project_can_have_one_line(self):
        """Test the project can have only one line"""
        pp = ProjectParser()
        project = "file://result <- file://source\n"
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        assert len(workflow._processes[0]._inputs) == 1
        assert len(workflow._processes[0]._outputs) == 1

    def test_section_can_have_no_inputs(self):
        """
        Read project with a blank line with blank characters which match exactly the indentation
        of the code of the process
        """
        pp = ProjectParser()
        section = """file:///resource1 <-
        """
        pp.set_project(section)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 0

    def test_section_can_have_no_outputs(self):
        """
        Read project with a process with inputs but without outputs
        """
        pp = ProjectParser()
        section = """ <- file:///resource
        """
        pp.set_project(section)
        pp.read_line()
        process= pp.parse_section()
        assert len(process._outputs) == 0

    def test_a_project_can_begin_by_a_blank_line(self):
        """Test the project can begin by a blank line"""
        pp = ProjectParser()
        project = "\nfile://result <- file://source"
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        assert len(workflow._processes[0]._inputs) == 1
        assert len(workflow._processes[0]._outputs) == 1

    def test_a_project_can_have_no_blank_lines(self):
        """Test the project can begin by a blank line"""
        pp = ProjectParser()
        project = """
file://file2 <- file://file1
file://file3 <- file://file2
"""
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 2
        assert len(workflow._processes[0]._inputs) == 1
        assert len(workflow._processes[0]._outputs) == 1
        assert len(workflow._processes[1]._inputs) == 1
        assert len(workflow._processes[1]._outputs) == 1

    def test_read_last_unfinished_line_of_a_project(self):
        """Test the project can begin by a blank line"""
        pp = ProjectParser()
        project = """file://result <- file://source
        Some code"""
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        assert workflow._processes[0]._code == "Some code\n"

    def test_read_last_line_of_a_project(self):
        """Test the project can begin by a blank line"""
        pp = ProjectParser()
        project = """file://result <- file://source
        Some code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        assert workflow._processes[0]._code == "Some code\n"

    def test_read_extra_line_of_a_project(self):
        """Test the project have extra blank lines at the end"""
        pp = ProjectParser()
        project = """file://result <- file://source
        Some code

"""
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 1
        print "'{}'".format(workflow._processes[0]._code)
        assert workflow._processes[0]._code == "Some code\n"

    def test_parse_dependencies_and_processor(self):
        """ Ensure processor is bat when bat is required"""
        pp = ProjectParser()
        project = "file:///result1 <- file:///source1 ! bat"
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_dependencies_and_processor()
        assert process._processor.name == "bat"

    def test_parse_dependencies_and_processor2(self):
        """ Ensure processor is shell when shell is required"""
        pp = ProjectParser()
        project = "file:///result1 <- file:///source1 ! shell"
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_dependencies_and_processor()
        assert process._processor.name == "shell"

    def test_unknown_processor(self):
        """ Should raise an error when a processor with a wrong name is provided"""
        pp = ProjectParser()
        project = "file:///result1 <- file:///source1 ! unknown"
        pp.set_project(project)
        pp.read_line()
        try:
            process = pp.parse_dependencies_and_processor()
            assert False
        except InvalidProcessorError:
            assert True

    def test_recognize_inclusion(self):
        """ Parser should recognize an include statement"""
        pp = ProjectParser()
        project = "include included_project.tuttle"
        pp.set_project(project)
        pp.read_line()
        assert pp.is_inclusion(pp._line), "This line should be recognized as an include statement"
        filename = pp.parse_inclusion()
        assert filename == "included_project.tuttle", filename

    @isolate(['included_project.tuttle'])
    def test_inclusion_statement(self):
        """ A project should be a sequence of sections and inclusions
        Including a file mean loading more processes
        """
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
        Some code

include included_project.tuttle

file:///resource2 <- file:///resource3
        Some code        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._processes) == 3

    def test_inclusion_error(self):
        """ A clean error message should be displayed if the file does not exist"""
        pp = ProjectParser()
        project = """file:///resource1 <- file:///resource2
        Some code

include unknown_file

file:///resource2 <- file:///resource3
        Some code        """
        pp.set_project(project)
        try:
            workflow = pp.parse_project()
            assert False, "An error should have been raised"
        except WorkflowError:
            assert True

    def test_recognize_preprocess(self):
        """ Parser should recognize a preprocess"""
        pp = ProjectParser()
        project = """|<<
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        assert pp.is_preprocess(pp._line), "This line should be recognized as an include statement"
        preprocess = pp.parse_preprocess()
        code = preprocess.code
        assert code == "Some code\n", code
        processor = preprocess.processor
        # depends weather we are running under windows or *nix
        #assert processor.name == "bat", processor.name
        #assert processor.name == "shell", processor.name

    def test_recognize_preprocess_with_processor(self):
        """ Parser should recognize a preprocess"""
        pp = ProjectParser()
        project = """|<< ! python
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        assert pp.is_preprocess(pp._line), "This line should be recognized as an include statement"
        preprocess = pp.parse_preprocess()
        processor = preprocess.processor
        assert processor.name == "python", processor.name

    def test_preprocess_unknown_processor(self):
        """ Parser should raise an error if the procesor of the preprocess does not exist"""
        pp = ProjectParser()
        project = """|<< ! unknown
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        assert pp.is_preprocess(pp._line), "This line should be recognized as an include statement"
        try:
            preprocess = pp.parse_preprocess()
            assert False
        except InvalidProcessorError:
            assert True

    def test_preprocess_statement(self):
        """ Preprocessors should be available from the workflow
        """
        pp = ProjectParser()
        project = """|<< ! python
        Some code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._preprocesses) == 1

    def test_preprocess_statement_not_separated(self):
        """ Preprocessors should be available from the workflow... Even without separator
        """
        pp = ProjectParser()
        project = """|<< !python
        Some code
        """
        pp.set_project(project)
        workflow = pp.parse_project()
        assert len(workflow._preprocesses) == 1

    def test_parse_dependencies_and_processor_not_separated(self):
        """ Ensure we can set a processor even without a space after !"""
        pp = ProjectParser()
        project = "file:///result1 <- file:///source1 !shell"
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_dependencies_and_processor()
        assert process._processor.name == "shell"

    def test_inputs_and_outputs_separated_by_space(self):
        """Inputs and outputs can be separated only by a spaces"""
        pp = ProjectParser()
        project = """file:///result1 file:///result2 file:///result3 <- file:///source1 file:///source2
        Some code
        """
        pp.set_project(project)
        pp.read_line()
        process = pp.parse_section()
        assert len(process._inputs) == 2
        assert process._inputs[0].url == 'file:///source1'
        assert process._inputs[1].url == 'file:///source2'
        assert len(process._outputs) == 3
        assert process._outputs[0].url == 'file:///result1'
        assert process._outputs[1].url == 'file:///result2'
        assert process._outputs[2].url == 'file:///result3'
        assert process._code == "Some code\n"
