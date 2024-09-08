import os
import json

import db_path

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


def make_di_for_json(filedir, file):
    """
    | Make Data Info table for the given valid json file
    | according to the provided info key.
    :param filedir: str
    :param file: str
    :return: void
    """

    def get_info_dir():
        """
        | Returns the directory of the new Data Info file
        :return: str
        """

        split = filedir.split('/')
        split.remove('table')
        split.insert(4, 'info')
        newdir = '/'.join(split[:-1])
        if newdir != '':
            newdir += '/'
        newdir += split[len(split) - 1].replace('-dt.json', '')
        newdir += '/'

        os.makedirs(newdir, exist_ok=True)
        return newdir + split[len(split) - 1].replace('-dt.json', f'-{info_key}-di.json')

    if file == "":
        return

    json_obj = json.loads(file)

    with open(get_info_dir(), 'w') as json_file:
        json.dump(replace_json_leaves_with_null(json_obj), json_file, indent=4)


def make_di_for_all_json_files_under(root):
    """
    | Make Data Info table for the given all valid json file
    | under given root according to the provided info key.
    :param root: str
    :return: void
    """

    if os.path.isdir(root):
        subdirs = os.listdir(root)
        for subdir in subdirs:
            make_di_for_all_json_files_under(f"{root}{subdir}"
                                             if root.endswith('/')
                                             else f"{root}/{subdir}")
    else:
        if not root.endswith('.json'):
            return
        # Ignore tables
        if root.endswith('-di.json'):
            return

        filedir = root

        with open(filedir, 'r') as file:
            make_di_for_json(filedir, file.read())


def get_table_dir_for(valid_filedir):
    """
    | Returns the directory of the given valid json
    | file's directory's data table
    :param valid_filedir: str
    :return: str
    """
    split = valid_filedir.split('/')
    split = [e for e in split if e != '']
    result_dir = '/'.join(split[:4])
    result_dir += "/table/"
    result_dir += '/'.join(split[4:-1])
    result_dir += "/"

    return result_dir + split[-1].replace('.json', '-dt.json')


if __name__ == "__main__":
    mydir = f'{db_path.system_path}/{target_table_dir}'
    # If the directory is a folder
    if not mydir.endswith('.json') and not mydir.endswith('/'):
        mydir += '/'
    mydir = get_table_dir_for(mydir)

    make_di_for_all_json_files_under(mydir)
