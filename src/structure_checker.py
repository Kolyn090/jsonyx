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


SQL_list = python_to_sql_type(list)
SQL_dict = python_to_sql_type(dict)
SQL_null = python_to_sql_type(None)


class Node:
    def __init__(self, key='', value_type=SQL_null, parent=None, child_count=0):
        self.key = key
        self.value_type = value_type
        self.parent = parent
        self.child_count = child_count

    def __str__(self):
        return f'key={self.key}, val_type={self.value_type}, child_count={self.child_count}, isParentNone={self.parent is None}'


def structure_check(json_dir, system_dir, data_dir):
    with open(json_dir) as file:
        if file == '':
            return
        else:
            json_obj = json.loads(file.read())

    """ Search for scope """
    def get_node_type_of(n):
        if isinstance(n, (dict, list)):
            return 0 if isinstance(n, dict) else 1
        return 2

    # Keys must be from data / an empty string (if unnamed)
    # Names can be assigned by program

    # List<List<(Key, Type, Parent_Name, Parent_Type)>>
    scope = []

    # initialize name for dict under outermost list
    # List<(Node, Level)>
    root = Node('ROOT', SQL_list, None, len(json_obj))
    pq = [(e, 0, Node(parent=root)) for i, e in enumerate(json_obj)]

    while len(pq) > 0:
        obj, node_level, curr_node = pq.pop(0)
        obj_type = get_node_type_of(obj)

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
            # TODO
            # Same parent cannot be in the same scope
            group[node.key].append(node)
        if len(group) > 0:
            fake_same_scope.append(group)
    for idx, group in enumerate(fake_same_scope):
        print(f'{idx} -------------------')
        for k, nodes in group.items():
            print(k)
            for node in nodes:
                print(node)
    print()
'''
    """ Determine validness of structure """
    def find_closest_list_ancestor_of(n):
        temp = n.parent
        if temp is None:
            return n
        prev = temp
        while temp.value_type != SQL_list:
            temp = temp.parent
            if temp is None:
                return prev
            prev = temp
        return temp

    for group in fake_same_scope:

        for nodes in group.values():
            if len(nodes) <= 1:
                continue

            # TODO:
            # Compare e1, e2:
            # 1. If parent is a Dict, its parent must be different from the rest of nodes in scope
            # 2. Must match siblings count = list scope count * closest ancestor list child count
            #    Scope siblings count = list ancestor count of list ancestor
            #    (need to carefully handle 'fake')
            # 3. Parent of list cannot be list

            # Rule 1
            for idx1 in range(len(nodes)-1):
                e1 = nodes[idx1]
                e1_parent = e1.parent
                is_parent_dict = e1_parent.value_type == SQL_dict
                for idx2 in range(idx1+1, len(nodes)):
                    e2 = nodes[idx2]
                    e2_parent = e2.parent
                    if is_parent_dict:
                        if e1_parent is e2_parent:
                            print('Violation of rule 1')
                            return False
            # Rule 2
            for idx1 in range(len(nodes)):
                e1 = nodes[idx1]
                e1_closest_list_ancestor = find_closest_list_ancestor_of(e1)
                if e1_closest_list_ancestor is None:  # The Root
                    continue
                e1_common_ancestor = find_closest_list_ancestor_of(e1_closest_list_ancestor)
                scope_siblings_count = e1_common_ancestor.child_count
                print(e1)
                print(e1_closest_list_ancestor)
                print(e1_common_ancestor)
                print(scope_siblings_count)
                counter = 0
                for idx2 in range(len(nodes)):
                    e2 = nodes[idx2]
                    e2_closest_list_ancestor = find_closest_list_ancestor_of(e2)
                    if e1_closest_list_ancestor is e2_closest_list_ancestor:
                        counter += 1
                if counter != scope_siblings_count:
                    print(counter)
                    print('Violation of rule 2')
                    return False
            # Rule 3
            for node in nodes:
                if node.value_type == SQL_list:
                    if node.parent is not None:
                        if node.parent.value_type == SQL_list:
                            print('Violation of rule 3')
                            return False
    return True
'''


if __name__ == "__main__":
    jsons = util.get_jsons_under(db_path.data_dir)
    for j in jsons:
        print(structure_check(j, db_path.system_dir, db_path.data_dir))
