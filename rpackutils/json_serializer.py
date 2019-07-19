#######################################
# Copyright 2019 PMP SA.              #
# SPDX-License-Identifier: Apache-2.0 #
#######################################

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
