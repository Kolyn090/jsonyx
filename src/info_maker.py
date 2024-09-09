import os
import json

import db_path
import util
import dir_maker

'''
    Creates Data Info for all valid json files under the given
    directory. A valid json file is:
    1. Name not ending with '-dt.json' or '-di.json'
    2. Must have an associated '-dt.json'

    Example:
    armors.json is a valid json file because:
    1. Its name is valid
    2. Its table is table/armors-dt.json
'''

print("!!!WARNING: Info maker will override existing files, " +
      "please be certain you know what you are doing!!!\n")
print("↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑\n")
target_table_dir = input("Enter the table's directory you want to create. \n" +
                         "It will be replacing 'xxx' in the next step. \n" +
                         "Example: armors.json, Weapons\n")
info_key = input("Enter the info key you want the info to be named before with. \n" +
                 "Example: enter 'ref' will create a new info file named " +
                 "xxx-ref-di.json \n")


def replace_json_leaves_with_null(json_obj):
    """
    | Replace all leaves of the given JSON object with null.
    :param json_obj: JSON
    :return: JSON
    """
    if isinstance(json_obj, dict):
        return {k: replace_json_leaves_with_null(v) for k, v in json_obj.items()}
    elif isinstance(json_obj, list):
        return [replace_json_leaves_with_null(item) for item in json_obj]
    else:
        # Replace the leaf value with null
        return None


def make_info_for_json(type_dir, system_path):
    """
    | Make info table for the given type table
    | according to the provided info key.
    :param type_dir: str
    :param system_path: str
    :return: Void
    """

    with open(type_dir) as file:
        if file == '':
            return
        else:
            json_obj = json.loads(file.read())

    with open(dir_maker.get_di_dir(type_dir, system_path, info_key), 'w') as json_file:
        json.dump(replace_json_leaves_with_null(json_obj), json_file, indent=4)


if __name__ == "__main__":
    system_type_dir = db_path.system_path + '/type/' + target_table_dir

    if os.path.isdir(system_type_dir) or os.path.isfile(system_type_dir):
        jsons = util.get_jsons_under(system_type_dir)
        for j in jsons:
            make_info_for_json(j, db_path.system_path)
