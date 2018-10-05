###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import signal
import logging
import subprocess
import threading

logger = logging.getLogger(__name__)


class Command(object):
    """
    Create subprocess with timeout support.
    """
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.stdout = None
        self.stderr = None
        self.returncode = None

    def kill(self, signal=signal.SIGINT):
        """
        Kill the runnin process
        :param signal: os.signal, default=os.signal.SIGINT
        """
        os.kill(self.process.pid, signal.SIGINT)

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False)
            logger.info('Waiting for process {} to complete...'
                        .format(self.process.pid))
            for stdout_line in iter(self.process.stdout.readline, ""):
                print(stdout_line)
            self.process.stdout.close()
            (self.stdout, self.stderr) = self.process.communicate()
            # decode stdout and stderr
            if(self.stdout):
                self.stdout = self.stdout.decode()
            if(self.stderr):
                self.stderr = self.stderr.decode()
            self.returncode = self.process.returncode
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            logger.error('The process {} is taking too long, '
                         'terminating it'
                         .format(self.process.pid))
            self.kill()
            thread.join()
            self.returncode = -1
            self.stderr = 'The process is taking too long, ' \
                          'RPackUtils killed it!'
        return (self.returncode, self.stdout, self.stderr)
