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


class Node:
    def __init__(self, key='', value_type=python_to_sql_type(None), parent=None, child_count=0):
        self.key = key
        self.value_type = value_type
        self.parent = parent
        self.child_count = child_count

    def __str__(self):
        return f'key={self.key}, val_type={self.value_type}, child_count={self.child_count}'


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
    # List<(Node, Level)>
    root = Node('ROOT', python_to_sql_type(list), None, len(json_obj))
    pq = [(e, 0, root) for i, e in enumerate(json_obj)]

    temp_name_idx = len(json_obj) - 1
    while len(pq) > 0:
        obj, node_level, curr_node = pq.pop(0)
        obj_type = get_node_type(obj)

        if len(scope) < node_level + 1:
            scope.append([])

        if obj_type == 0:  # dict
            curr_node.child_count = len(obj.items())
            for k, v in obj.items():
                new_node = Node(k, python_to_sql_type(type(v)), curr_node)
                pq.append((v, node_level + 1, new_node))
                scope[node_level].append(new_node)
        elif obj_type == 1:  # list
            curr_node.child_count = len(obj)
            for idx, item in enumerate(obj):
                item_type = get_node_type(item)
                if item_type == 0:  # item is a dict
                    temp_name_idx += 1
                new_node = Node('', python_to_sql_type(type(item)), curr_node)
                pq.append((item, node_level + 1, new_node))
                scope[node_level].append(new_node)

    scope.insert(0, [root])
    scope.pop(-1)
    # for idx, row in enumerate(scope):
    #     print(f'{idx} -------------------')
    #     for node in row:
    #         print(node)

    """ Group records to the same scope """
    # It's fake because it doesn't handle the case of keys
    # in list with keys in dict located at the same level.
    fake_same_scope = []
    for row in scope:
        group = {}
        # Notice that parent type is 0, 1, 2
        # while type is SQL type
        for node in row:
            if node.key not in group:
                group[node.key] = []
            group[node.key].append(node)
        if len(group) > 0:
            fake_same_scope.append(group)
    # for idx, group in enumerate(fake_same_scope):
    #     print(f'{idx} -------------------')
    #     for k, nodes in group.items():
    #         print(k)
    #         for node in nodes:
    #             print(node)
    # print()

    """ Determine validness of structure """
    for group in fake_same_scope:
        for nodes in group.values():
            # TODO:
            # Compare e1, e2:
            # 1. If parent is a Dict, its parent must be different from the rest of nodes in scope
            # 2. Must match siblings count = closest ancestor list child count (need to carefully handle 'fake')
            # 3. Parent of list cannot be list

            pass


if __name__ == "__main__":
    jsons = util.get_jsons_under(db_path.data_dir)
    for j in jsons:
        structure_check(j, db_path.system_dir, db_path.data_dir)
