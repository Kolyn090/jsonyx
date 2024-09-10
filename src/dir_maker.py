import os


def remove_last_n_items(directory, n):
    for _ in range(n):
        directory = os.path.dirname(directory)
    return directory


def remove_first_n_items(directory, n):
    new_dir = directory
    for _ in range(n):
        dir_parts = new_dir.split(os.sep)
        dir_parts = dir_parts[1:]
        new_dir = os.sep.join(dir_parts)
    return new_dir


# The directory used to store (within-db)
# type table of the provided json file
# which can be located in any location.
# The output will be a dir within system dir.
# system-dir/..
def get_dt_dir(json_dir, system_dir, data_dir):
    # Directory the json file without data dir
    local_json_dir = json_dir.replace(data_dir, '')
    # Parent directory of the above json file
    local_json_parent_dir = os.path.split(local_json_dir)[0]
    # The dir to the parent of new type table
    result_folder_dir = os.path.join(system_dir, 'type', local_json_parent_dir.lstrip('/\\'))

    os.makedirs(result_folder_dir, exist_ok=True)

    json_name = os.path.split(local_json_dir)[1]
    # The dir to the new table info
    return os.path.join(result_folder_dir, json_name.replace('.json', '-dt.json'))


def get_json_dir_by_di(di_dir, system_dir, data_dir):
    local_di_dir = os.sep + remove_first_n_items(os.path.relpath(di_dir, system_dir), 1)
    local_di_file_name = os.path.split(local_di_dir)[1]
    local_json_file_name = '-'.join(local_di_file_name.split("-")[:-2]) + '.json'
    parent_dir = remove_last_n_items(local_di_dir, 2)
    return os.path.join(data_dir, parent_dir.lstrip('/\\'), local_json_file_name.lstrip('/\\'))


def get_di_dir(type_dir, system_dir, info_key):
    """
    | Returns the directory of the new info table file
    :return: str
    """
    local_type_json_dir = type_dir.replace(system_dir, '')
    local_json_dir = remove_first_n_items(local_type_json_dir, 2)
    local_json_parent_dir = os.path.split(local_json_dir)[0]
    json_name = os.path.split(local_json_dir)[1]
    result_folder_dir = os.path.join(system_dir, 'info/',
                                     local_json_parent_dir.lstrip('/\\'),
                                     json_name.replace('-dt.json', '').lstrip('/\\'))
    result_file_dir = os.path.join(result_folder_dir,
                                   json_name.replace('-dt.json', f'-{info_key}-di.json'))
    return result_file_dir
