###################################################################
# This program is distributed in the hope that it will be useful, #
# but WITHOUT ANY WARRANTY; without even the implied warranty of  #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the    #
# GNU General Public License for more details.                    #
###################################################################

import json


class JSONSerializer:

    @staticmethod
    def deserialize(s):
        return json.load(s)

    @staticmethod
    def deserializefromfile(filepath):
        obj = None
        with open(filepath, "r") as f:
            obj = json.load(f)
        return obj

    @staticmethod
    def serialize(obj):
        return json.dumps(obj)

    @staticmethod
    def serialize2file(obj, filepath):
        jsonstr = JSONSerializer.serialize(obj)
        with open(filepath, "w") as f:
            f.write(jsonstr)
