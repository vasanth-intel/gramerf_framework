__author__ = 'Evan McDonough'
__copyright__ = 'Copyright 2018, Intel Restricted Secret'
__license__ = 'Intel Restricted Secret'
__maintainer__ = 'Evan McDonough'
__email__ = 'evanx.mcdonough@intel.com'
__date__ = '20180409'

#
#
#--------------------------------------------------------------------
# PQT.py
#   a PQT object starts a process (on creation of the object), funneling
#   the stdout and stderr into a queue that can be read line by line.
#
#   For convenience, PQT.Create_PQT() allows one to set a working directory
#   to start the command in, and allows specifying the output filename
#
#   Note that the output filename is not required (output can be flushed
#   without use).   If stdout/stderr is desired, it must be flushed
#   ( PQT.flushOutput() ) before the PQT object is destroyed.
#
#   Note also that destroying the PQT does not automatically destroy
#   the created process(es).
#
#--------------------------------------------------------------------
#
#


#
# Imports
#
import os
from threading import Thread
from Queue import Queue, Empty
from subprocess import PIPE, Popen, check_output
import time
import platform


# class to represent a pqt object without really having one, to act as a dummy workload
class dummy_PQT:
    def __init__(self):
        self.returncode = None
        self.command = None
        self.outputFilename = None
        self.process = None
        self.queue = None
        self.thread = None
        self.error_thread = None
        self.isrunning = True

    def isRunning(self):
        return self.isrunning

    def flushOutput(self, path = None, filePath = None ):
        pass


# A PQT object opens a pipe with a given command, and opens a thread to enqueue the output from that pipe
# This reads in a non-blocking way and
class PQT:
    def __init__( self, command, commandName=None, use_shell=True, sleep_time=None):
        """
            IN: command - the command line statement to run
            IN: commandName - the name as seen in the task list (to allow the process to be killed)
                if commandName is not specified, it will be intuited from the command.
            """
        self.returncode = None
        self.command = command
        if ( self.command==None or self.command == "" ) :
            print "PQT currently does not accept 'no command' as valid"
            print "You're doing it wrong."
            raise ValueError("null or empty command initializing a PQT object")

        if ( commandName == None ) :
            self.parseCommandName() # TODO: Looks like there may have been an issue with this command sometimes
        else :
            self.commandName = commandName

        self.outputFilename = None

        self.process       = Popen(command, shell=use_shell, stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=1)
        self.pid           = self.process.pid # this is supposed to get the PID of the child process
        self.queue         = Queue()
        self.thread        = Thread(target=PQT.enqueue_output, args=(self.process.stdout, self.queue))
        self.error_thread  = Thread(target=PQT.enqueue_output, args=(self.process.stderr, self.queue))
        self.thread.daemon = True
        self.error_thread.daemon = True
        self.thread.start()
        self.error_thread.start()
        if sleep_time is not None:
            time.sleep(sleep_time)

    def print_output(self):
        line = self.readline()
        while (line != None):
            print line
            line = self.readline()

    def parseCommandName(self):
        """ assigns self.commandName either 'None' or a string parsed from
            the command line.

            No return value.
            """

        self.commandName = None
        if ( self.command == None or self.command == "" ) :
            return # no command set!

        commandPath = self.command.split(' ')[0]
        if ( commandPath ) :
            return  # could not find a command
                    # this is seriously twisted, but who knows?
        # trade out dos path separators for linux ones, just to be sure.
        normalizedCommandPath = commandPath.replace('\\', '/')
        # and find the path...
        pathList = normalizedCommandPath.rsplit('/',1)
        pathListSize = len(pathList)
        if ( pathListSize == 0 ) :
            self.commandName = "Unknown"
        elif ( pathListSize == 1 ) :
            # was just the raw command name, no path
            self.commandName = pathList[0]
        else :
            # 0 = path, 1 = command name
            self.commandName = pathList[1]
        return

    def flushOutput(self, path = None, filePath = None ):
        """
        Empty the output/error queue  (to someplace)

        Drops output on the floor if none of path, filePath, or
        PQT.outputFilename is specified.

        IN: filePath - overrides PQT.outputFilename if specified
        IN: path -   prepends to outputFileName if specified

        USE: specify PQT.outputFilename if filename known on creation
             use 'path' to specify a directory
             use filePath to specify both directory and filename
        """
        #print "Flushing output for " + str(self.commandName) + " PQT Object"

        # set active filename
        if ( filePath == None and self.outputFilename != None ) :
            filePath = self.outputFilename

        if ( filePath == None ):
            print "WARNING: no path specified for output from " + self.command
            # exhaust the queue and return
            while ( self.readline() != None ) :
                pass
            return

        # filepath is something
        if ( path != None ) :
            filePath = os.path.join( path, filePath )

        if os.path.isfile(filePath):
            o_file = open( filePath, 'a' )
        else:
            o_file = open( filePath, 'w' )
        print "Sending output to " + filePath

        line = self.readline()
        while ( line  != None ) :
            try:
                word = line.split("\n")[0]
                word = word.split("\r")[0]
                o_file.write(word + "\n")
            except:
                o_file.write( line )
            line = self.readline()
        o_file.flush()
        #end PQT.flushOutput()

    # defines an output filename, and opens it.   Once specified, all output
    # is sent to that file (in addition to being returned, if applicable).
    def setOutputFile(self, filepath):
        self.outputFilename = filepath

    def isRunning(self):
        # if the process has already exited, return
        if (self.returncode != None) :
            return False
        # poll sets (and returns) returncode of the process object
        #    None == still RUNNING
        #    otherwise:
        #        UNIX:  -N  where N is the signal terminating the process
        #        Windows:  the value of GetExitCodeProcess()  (google GetExitCodeProcess MSDN)
        self.returncode = self.process.poll()
        return (self.returncode == None)
        # we've saved the code for your convenience, but we don't care beyond "is it running"

    def readline(self):
        try:
            line = self.queue.get_nowait()
        except Empty:
            return None
        else:
            return line

    # a function to be run over and over in the thread to enqueue lines from the process
    @staticmethod
    def enqueue_output(out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    # a function returning the performance data in a dictionary{string, string} format
    def performance_data(self, app_name):
        performance_data_dict = {}
        if platform.system() == "Linux":
            pid = check_output(["pidof", app_name])
            print pid
            print "Reading Performance Data"
            path_to_file = "/proc/" + str(pid).strip() + "/status"
            with open(path_to_file) as read_file:
                for content in read_file:
                    content_list = content.split(":")
                    performance_data_dict[content_list[0].strip()] = content_list[1].strip()
            return performance_data_dict


# create a new PQT object, and provide it some values
# This specifically helps when the command MUST Be launched from a sub directory
def create_PQT( base_dir, command, outputfilename=None, commandName=None, use_shell=True, sleep_time=None) :

    cwd = os.getcwd()
    try:
        if ( base_dir != None and base_dir != "" ) :
            os.chdir( base_dir )    # if there IS a base dir...
            #print "Using Base Dir: " + str(base_dir)
    except Exception as e:
        print "Exception: " + str(e)
        print "Couldn't find working directory, command will execute with cwd: " + str(cwd)
    print "Current Directory:" + os.getcwd()
    pqt = PQT(command, commandName, use_shell, sleep_time)
    pqt.outputFilename = outputfilename
    os.chdir(cwd)
    return pqt


def main() :
    print "No default functionality for PQT class script."


if __name__ == "__main__":
    main()
