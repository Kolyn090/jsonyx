import os
import json

import db_path
import util
import dir_maker

'''
    Check for info files validness

    1. Info must have the exact same structure as its Table

    For reference tables:
        2. Ensure that every referencing field in Table contains a value
        that exists in the Referenced Table's referenced field
    For unique tables:
        3. Ensure every field marked true in -uni-di.json is unique
        within its own scope
    
    Tip: Check data_info_reference_example.png for visualization
    Tip: di stands for 'data-info'
'''


def compare_json_structures_ignore_type(json1, json2):
    """
    | Returns True if the two given JSON objects have the same
    | field structure. The type of each value is insensitive.
    :param json1: JSON
    :param json2: JSON
    :return: boolean
    """

    # Check if both are dictionaries
    if isinstance(json1, dict) and isinstance(json2, dict):
        # Check if both have the same keys
        if set(json1.keys()) != set(json2.keys()):
            return False
        # Recursively check the structure of each key
        for key in json1:
            if not compare_json_structures_ignore_type(json1[key], json2[key]):
                return False
        return True
    # Check if both are lists
    elif isinstance(json1, list) and isinstance(json2, list):
        # Compare length of lists
        if len(json1) != len(json2):
            return False
        # Recursively check the structure of each item
        for item1, item2 in zip(json1, json2):
            if not compare_json_structures_ignore_type(item1, item2):
                return False
        return True
    # There is no need to compare types in this case
    else:
        return True


def replace_object_with_null(json_obj, target_fields):
    """
    | Replace all objects that exactly contains the given fields
    | with null for the given JSON object
    | Example:
    | {
    |   data: {
    |       "one": 1
    |       "two": 2
    |   }
    | }
    | replace_object_with_null(data, ["one", "two"])
    | >>
    | {
    |   data: null
    | }
    :param json_obj: JSON
    :param target_fields: List(str)
    :return: boolean
    """

    if isinstance(json_obj, dict):
        # Check if all required fields are present in the current dictionary
        if all(field in json_obj for field in target_fields):
            return None  # Replace the entire object with None if all required fields are found
        else:
            # Recursively apply the function to each value in the dictionary
            for key, value in json_obj.items():
                json_obj[key] = replace_object_with_null(value, target_fields)
    elif isinstance(json_obj, list):
        # If the current item is a list, recursively apply the function to each element
        json_obj = [replace_object_with_null(item, target_fields) for item in json_obj]

    return json_obj


def get_relative_dir(base_dir, relative_dir):
    """
    | Return a new dir from dir that is relative to the
    | base dir
    | Example:
    | base_dir = "./Farm"
    | relative_dir = "../items.json"
    | >> "items.json"
    :param base_dir: str
    :param relative_dir: str
    :return: str
    """

    # Join the base dir with the relative dir
    full_dir = os.path.join(base_dir, relative_dir)
    # Normalize the dir to remove any redundant components like '..' or '.'
    normalized_dir = os.path.normpath(full_dir)
    return normalized_dir


def get_nested_value(data, fields):
    for field in fields:
        if isinstance(data, dict):
            # Access the dictionary value by the key
            data = data.get(field)
        elif isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict) or isinstance(item, list):
                    result.append(get_nested_value(item, [field]))
                else:  # Primitive type
                    result.append(item)
            data = result
        else:
            return None  # Return None if the structure is not as expected
    return data


def confirm_reference(di_obj, di_dir, json_dir, parent_keys=None):
    """
    | Confirm that each value in Table (that is referencing field from
    | another table) actually also exists in the Referenced Table's values.
    | Example:
    |
    | Referenced Table
    | {
    |   "key": 0
    | }
    |
    | Table
    | {
    |   "field" references "key" in Referenced Table
    | }
    |
    | The goal will be to check whether all "fields" contain values
    | only appeared in Reference Table "key" field values (in this
    | example, only 0 is possible).
    |
    :param di_obj: JSON
    :param di_dir: str
    :param json_dir: str
    :param parent_keys: str[]
    :return: void
    """

    if parent_keys is None:
        parent_keys = []

    # Referenced Table (in relative dir)
    stored_references_dir = ''
    if isinstance(di_obj, dict):
        for key, value in di_obj.items():
            if key == 'REFERENCES':
                # Store the dir, the next key must be REFERENCES-FIELD
                stored_references_dir = value
            elif key == 'REFERENCES-FIELD':
                # Goal: Open Referenced Table
                # 'Table' is guaranteed to be in the parent directory
                # The field is storing a relative dir based on the above dir
                # Combine them to get the dir to Referenced Table (which can be opened)

                referenced_table_dir = get_relative_dir(json_dir, os.path.join('..', stored_references_dir))
                assert referenced_table_dir.endswith('.json')
                with open(referenced_table_dir, 'r') as referenced_table_file:
                    referenced_table = json.loads(referenced_table_file.read())

                    # Goal: Open Table
                    with open(json_dir, 'r') as table_file:
                        table = json.loads(table_file.read())

                        def flatten_list(lst):
                            flattened = []
                            for sublist in lst:
                                if isinstance(sublist, list):  # Check if the element is a list or tuple
                                    flattened.extend(flatten_list(sublist))  # Flatten only lists or tuples
                                else:
                                    flattened.append(sublist)  # Append the element directly if it's not a list/tuple
                            return flattened

                        # 'parent_key' can lead to the referencing field in Table
                        # 'value' can lead to the referenced field in Referenced Table
                        table_values = flatten_list(list(map(lambda x: get_nested_value(x, parent_keys), table)))
                        ref_table_values = \
                            flatten_list(list(map(lambda x: get_nested_value(x, [value]), referenced_table)))

                        for a in table_values:
                            result = False
                            for b in ref_table_values:
                                if a == b:
                                    result = True
                                if a is None:
                                    result = True

                            assert result, f'{a} in {json_dir} is invalid.'
            else:
                confirm_reference(value, di_dir, json_dir, parent_keys + [key])  # Recursively read the value

    elif isinstance(di_obj, list):
        for index, item in enumerate(di_obj):
            confirm_reference(item, di_dir, json_dir, parent_keys)  # Recursively read each item in the list


def check_uniqueness(di_obj, di_dir, json_dir, parent_keys=None):
    """
    | Confirm that each field marked 'unique' is unique in 
    | the Referenced Table within its own scope.
    | Example:
    |
    | -uni-di.josn
    | {
    |   "key": true
    | }
    | 
    | Referenced Table 1
    |  [
    |   {
    |    "key": "apple"
    |   }
    |   {
    |    "key": "banana"
    |   }
    | ]
    | >> True
    |
    | Referenced Table 2
    |  [
    |   {
    |    "key": "apple"
    |   }
    |   {
    |    "key": "apple"
    |   }
    | ]
    | >> False
    | 
    | Referenced Table 3
    | {
    |   key: [
    |       "apple"
    |       "banana"
    |   ]
    | }
    | >> True
    | 
    | Referenced Table 4
    | {
    |   key: [
    |       "apple"
    |       "apple"
    |   ]
    | }
    | >> False
    |
    | Referenced Table 5
    | {
    |   key: [
    |       "apple"
    |       "apple"
    |   ]
    | }
    | >> False
    :param di_obj: JSON
    :param di_dir: str
    :param json_dir: str
    :param parent_keys: str[]
    :return: void
    """

    if parent_keys is None:
        parent_keys = []

    def test_uniqueness_of_bottom_level_lists(lst, actual_Table_dir):
        if isinstance(lst, list):
            if len(lst) == 0:
                return

            if not isinstance(lst[0], list):
                assert len(lst) == len(set(lst)), f'{lst} of {actual_Table_dir} is not unique'
            for element in lst:
                test_uniqueness_of_bottom_level_lists(element, actual_Table_dir)

    if isinstance(di_obj, dict):
        for key, value in di_obj.items():
            if isinstance(value, list) or isinstance(value, dict):
                check_uniqueness(value, di_dir, json_dir, parent_keys + [key])
            else:
                if value:
                    with open(json_dir) as actual_file:
                        actual_json = json.loads(actual_file.read())
                        nested_value = get_nested_value(actual_json, parent_keys + [key])
                        test_uniqueness_of_bottom_level_lists(nested_value, json_dir)

    elif isinstance(di_obj, list):
        for index, item in enumerate(di_obj):
            if isinstance(item, dict):
                check_uniqueness(item, di_dir, json_dir, parent_keys)


def test_info(di_dir, system_dir, data_dir):
    with open(di_dir) as file:
        if file == '':
            return
        else:
            di_obj = json.loads(file.read())

    with open(di_dir) as file:
        if file == '':
            return
        else:
            di_obj_copy = json.loads(file.read())

    # 1. Info must have the exact same structure as its type table
    """
    Replace all
    {
        "REFERENCES": xxx,
        "REFERENCES-FIELD": xxx
    }
    in -ref.json with null
    """
    if di_dir.endswith('-ref-di.json'):
        di_obj = replace_object_with_null(di_obj,
                                          ['REFERENCES', 'REFERENCES-FIELD'])
    json_dir = dir_maker.get_json_dir_by_di(di_dir, system_dir, data_dir)
    dt_dir = dir_maker.get_dt_dir(json_dir, system_dir, data_dir)
    # Open Table
    with open(dt_dir) as dt_file:
        dt_obj = json.loads(dt_file.read())
        # Check if Data Info and Table have the same structure
        # note: type is not important, only the fields are
        assert compare_json_structures_ignore_type(di_obj, dt_obj), "Table structures are different!"

    # 2. Ensure that every referencing field in Table contains a value
    #    that exists in the Referenced Table's referenced field
    if di_dir.endswith('-ref-di.json'):
        confirm_reference(di_obj_copy, di_dir, json_dir)

    # # 3. Ensure every field marked true in -uni-di.json is unique
    # # within its own scope
    if di_dir.endswith('-uni-di.json'):
        check_uniqueness(di_obj_copy, di_dir, json_dir)


if __name__ == "__main__":
    system_info_dir = os.path.join(db_path.system_dir, 'info/')
    jsons = util.get_jsons_under(system_info_dir)
    for j in jsons:
        test_info(j, db_path.system_dir, db_path.data_dir)
