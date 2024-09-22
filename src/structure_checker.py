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


def structure_check(json_dir, system_dir, data_dir):
    def get_node_type(node):
        if isinstance(node, (dict, list)):
            return 0 if isinstance(node, dict) else 1
        return 2

    with open(json_dir) as file:
        if file == '':
            return
        else:
            json_obj = json.loads(file.read())

    """ Search for scope """
    # List<List<(Name, Type, Parent_Name, Parent_Type)>>
    scope = [[]]

    # initialize name for dict under outermost list
    # List<(Node, Level, Node_Name)>
    pq = [(e, 0, f'n{i}') for i, e in enumerate(json_obj)]

    temp_name_idx = len(pq) - 1
    while len(pq) > 0:
        curr_node, node_level, node_name = pq.pop(0)
        curr_type = get_node_type(curr_node)

        if len(scope) < node_level + 2:
            scope.append([])

        if curr_type == 0:  # dict
            for k, v in curr_node.items():
                pq.append((v, node_level + 1, k))
                scope[node_level + 1].append((k, python_to_sql_type(type(v)), node_name, curr_type))
        elif curr_type == 1:  # list
            for idx, item in enumerate(curr_node):
                item_type = get_node_type(item)
                if item_type == 0:  # item is a dict
                    temp_name_idx += 1

                pq.append((item, node_level + 1, f'n{temp_name_idx}'))
                scope[node_level + 1].append(('', python_to_sql_type(type(item)), node_name, curr_type))

    # print(scope)
    """ Search for same scope elements """
    same_scope = []
    for level in scope:
        grouped_scope = {}

        # Notice that parent type is 0, 1, 2
        # while type is SQL type
        for name, tp, parent_name, parent_tp in level:
            if name not in grouped_scope:
                grouped_scope[name] = []
            grouped_scope[name].append((tp, parent_name, parent_tp))
        same_scope.append(grouped_scope)

    for line in same_scope:
        print(line)
    print()
    # for field_dict in same_scope:
    #     field_dict_vals = field_dict.values()
    #     # 0 (dict), 1 (list), 2 (val) type
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
