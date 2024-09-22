import json
import re

import db_path
import util
import dir_maker


def python_to_sql_type(py_type):
    type_mapping = {
        str: 'VARCHAR',
        int: 'INT',
        float: 'FLOAT',
        list: 'ARRAY',
        dict: 'JSON',
        bool: 'BOOLEAN',
        type(None): 'NULL'
    }
    return type_mapping.get(py_type, 'UNKNOWN')


def get_node_type(node):
    if isinstance(node, (dict, list)):
        return 0 if isinstance(node, dict) else 1
    return 2


def structure_check(json_dir, system_dir, data_dir):
    with open(json_dir) as file:
        if file == '':
            return
        else:
            json_obj = json.loads(file.read())

    """ Search for scope """
    # Keys must be from data / an empty string (if unnamed)
    # Names can be assigned by program

    # List<List<(Key, Type, Parent_Name, Parent_Type)>>
    scope = []

    # initialize name for dict under outermost list
    # List<(Node, Level, Node_Name)>
    pq = [(e, 0, f'n{i}') for i, e in enumerate(json_obj)]

    temp_name_idx = len(json_obj) - 1
    while len(pq) > 0:
        curr_node, node_level, node_name = pq.pop(0)
        curr_type = get_node_type(curr_node)

        if len(scope) < node_level + 1:
            scope.append([])

        if curr_type == 0:  # dict
            for k, v in curr_node.items():
                pq.append((v, node_level + 1, k))
                scope[node_level].append((k, python_to_sql_type(type(v)), node_name, curr_type))
        elif curr_type == 1:  # list
            for idx, item in enumerate(curr_node):
                item_type = get_node_type(item)
                if item_type == 0:  # item is a dict
                    temp_name_idx += 1

                pq.append((item, node_level + 1, f'n{temp_name_idx}'))
                scope[node_level].append((f'n{temp_name_idx}', python_to_sql_type(type(item)), node_name, curr_type))

    # print(scope)

    """ Group records to the same scope """
    same_scope = []
    for level in scope:
        group = {}
        # Notice that parent type is 0, 1, 2
        # while type is SQL type
        for key, tp, parent_key, parent_tp in level:
            if key not in group:
                group[key] = []
            group[key].append((tp, parent_key, parent_tp))
        if len(group) > 0:
            same_scope.append(group)

    for line in same_scope:
        print(line)
    print()
    """ Determine validness of structure """


    # for field_dict in same_scope:
    #     field_dict_vals = field_dict.values()
    #     # 0 (dict), 1 (list), 2 (val) type
    #     print(list(field_dict_vals))
    #     instance_parent_type = list(field_dict_vals)[0][2]
    #
    #     # type, parent_name, parent_type (0, 1, 2)
    #     # ex. instance_list >> [('VARCHAR', '', 0), ('INT', '', 0)]
    #     for instance_list in field_dict_vals:
    #         # To be in the same scope:
    #         # If parent is Dict, parent_name must be different
    #         # except for unnamed parent: ''.
    #         # If parent is List, parent_name must be same.
    #
    #         if instance_parent_type == 0:  # dict
    #             if instance_list[1] == '':  # unnamed dict
    #                 pass
    #             else:  # named dict
    #                 pass
    #         else:  # list
    #             if instance_list[1] == '':  # unnamed list
    #                 pass
    #             else:  # named list
    #                 pass


if __name__ == "__main__":
    jsons = util.get_jsons_under(db_path.data_dir)
    for j in jsons:
        structure_check(j, db_path.system_dir, db_path.data_dir)
