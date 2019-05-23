from os import path
import json


def parse_json_file(filename):
    try:
        # open json
        with open(path.join(path.dirname(__file__), filename)) as f:
            file=json.load(f)
        #print(file)
        return file
    except Exception as e:
        print("Exception --> "+str(e))

if __name__ == '__main__':
    filename="UserRequest.json"
    parse_json_file(filename)