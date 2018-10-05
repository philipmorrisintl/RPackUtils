###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import os
import shutil
import shlex
from subprocess import Popen, PIPE


class Utils:

    @staticmethod
    def concatpaths(path1, path2, sep='/'):
        if sep is None:
            return os.path.join(path1, *path2.split(os.sep))
        else:
            return os.path.join(path1, *path2.split("/"))

    @staticmethod
    def concaturls(path1, path2):
        return Utils.concatpaths(path1, path2, sep='/')

    @staticmethod
    def cleanCRLFTAB(str):
        return str.replace('\r', '').replace('\n', '').replace('\t', '')

    @staticmethod
    def rmtree_under(path):
        """
        Same as shutil.rmtree() but keeps the root folder.
        """
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    @staticmethod
    def subprocesscall(cmd):
        """
        Execute the external command and get its
        exitcode, stdout and stderr.
        """
        args = shlex.split(cmd)
        proc = Popen(args, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate()
        exitcode = proc.returncode
        return exitcode, out, err
