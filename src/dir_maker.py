import os


# The directory used to store (within-db)
# type table of the provided json file
# which can be located in any location.
# The output will be a path within system path.
# system-path/..
def get_dt_dir(json_dir, system_path, data_path):
    # Directory the json file without data path
    local_json_dir = json_dir.replace(data_path, '')
    # Parent directory of the above json file
    local_json_parent_dir = '/'.join(local_json_dir.split("/")[:-1])
    # The path to the parent of new type table
    result_folder_dir = system_path + '/type' + local_json_parent_dir

    os.makedirs(result_folder_dir, exist_ok=True)

    json_name = local_json_dir.split("/")[-1]
    # The path to the new table info
    return result_folder_dir + '/' + json_name.replace('.json', '-dt.json')


def get_json_dir_by_di(di_dir, system_path, data_path):
    local_di_dir = '/'.join(di_dir.replace(system_path, '').split("/")[2:])
    local_di_file_name = local_di_dir.split("/")[-1]
    local_json_file_name = '-'.join(local_di_file_name.split("-")[:-2]) + '.json'
    return data_path + '/'.join(local_di_dir.split("/")[:-2]) + '/' + local_json_file_name


def get_di_dir(type_dir, system_path, info_key):
    """
    | Returns the directory of the new info table file
    :return: str
    """
    local_type_json_dir = type_dir.replace(system_path, '')
    local_json_dir = '/'.join(local_type_json_dir.split("/")[2:])
    local_json_parent_dir = '/'.join(local_json_dir.split("/")[:-1])
    json_name = local_json_dir.split("/")[-1]
    result_folder_dir = (system_path + '/info/' + local_json_parent_dir + '/' +
                         json_name.replace('-dt.json', '') + '/')

    os.makedirs(result_folder_dir, exist_ok=True)

    return (result_folder_dir + '/' +
            json_name.replace('-dt.json', f'-{info_key}-di.json'))
