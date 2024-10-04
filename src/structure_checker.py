import json
from collections import defaultdict

import db_path
import util


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

"""
tree
level
lsts
lst
node
"""


class Node:
    def __init__(self, key='', value_type=SQL_null, parent=None, child_count=0):
        self.key = key
        self.value_type = value_type
        self.parent = parent
        self.child_count = child_count

    def __str__(self):
        return f'@k={self.key}, v={self.value_type}, c={self.child_count}'


class ScopeNode:
    def __init__(self, key='', value_type=None, parent=None):
        self.key = key
        self.value_type = value_type
        if self.value_type is None:
            self.value_type = []
        self.parent = parent

    def __str__(self):
        return f'@k={self.key}, v={self.value_type}'


def group_enemies(pairs):
    """
    Groups people such that no two enemies are in the same group.

    :param pairs: List of tuples where each tuple represents two people who are enemies.
    :return: List of groups, where each group contains people who do not hate each other.
    """
    # Step 1: Build the graph as an adjacency list
    graph = defaultdict(list)

    for person1, person2 in pairs:
        graph[person1].append(person2)
        graph[person2].append(person1)

    # Step 2: Initialize a dictionary to store the group (color) of each person
    group_assignment = {}

    def get_available_group(person):
        """Return the smallest available group number for a person"""
        # Set to store groups of all adjacent enemies (neighbors)
        enemy_groups = {group_assignment.get(enemy) for enemy in graph[person] if enemy in group_assignment}

        # Assign the smallest group number that's not used by enemies
        group = 0
        while group in enemy_groups:
            group += 1
        return group

    # Step 3: Assign groups to each person using a greedy approach
    for person in graph:
        if person not in group_assignment:
            group_assignment[person] = get_available_group(person)

    # Step 4: Organize people by their group assignments
    groups = defaultdict(list)
    for person, group in group_assignment.items():
        groups[group].append(person)

    # Step 5: Return the groups as a list of lists
    return list(groups.values())


def get_same_scope_tree(json_dir):
    with open(json_dir) as file:
        if file == '':
            return
        else:
            json_obj = json.loads(file.read())

    """ Search for scope_tree """

    def get_node_type_of(n):
        if isinstance(n, (dict, list)):
            return 0 if isinstance(n, dict) else 1
        return 2

    # Keys must be from data / an empty string (if unnamed)
    # Names can be assigned by program

    # List<List<(Key, Type, Parent_Name, Parent_Type)>>
    scope_tree = []

    # initialize name for dict under outermost list
    # List<(Node, Level)>
    root = Node('ROOT', SQL_list, None, len(json_obj))
    pq = [(e, 0, Node(value_type=SQL_dict, parent=root)) for i, e in enumerate(json_obj)]

    while len(pq) > 0:
        obj, node_level, curr_node = pq.pop(0)
        obj_type = get_node_type_of(obj)

        if len(scope_tree) < node_level + 1:
            scope_tree.append([])
        scope_tree[node_level].append(curr_node)

        if obj_type == 0:  # dict
            curr_node.child_count = len(obj.items())
            for k, v in obj.items():
                new_node = Node(k, python_to_sql_type(type(v)), curr_node)
                pq.append((v, node_level + 1, new_node))
        elif obj_type == 1:  # list
            curr_node.child_count = len(obj)
            for idx, item in enumerate(obj):
                item_type = python_to_sql_type(type(item))
                new_node = Node('', item_type, curr_node)
                pq.append((item, node_level + 1, new_node))
        elif obj_type == 2:  # value (not null)
            if curr_node.parent.value_type == SQL_list:
                new_node = Node(curr_node.key, python_to_sql_type(type(obj)), curr_node)
                pq.append((None, node_level + 1, new_node))

    scope_tree.insert(0, [root])

    # for idx, row in enumerate(scope_tree):
    #     print(f'{idx} -------------------({len(row)})')
    #     print_list_of_nodes(row)

    """ Group records to the same scope_tree """

    def are_from_same_source(n, m):
        # Assuming tree level >= 2
        temp_n = n
        temp_m = m
        while temp_n is not temp_m and temp_n is not None and temp_m is not None:
            if temp_n.key != temp_m.key:
                return False

            temp_n = temp_n.parent
            temp_m = temp_m.parent

        if temp_n.value_type == SQL_dict:
            return False

        return True

    same_scope_tree = [[] for _ in range(len(scope_tree))]
    for level in range(2, len(scope_tree)):
        row = scope_tree[level]
        # Contain a pair of nodes that are in a different scope_tree in this level
        diff_scope_pairs = []
        if len(row) > 2:
            for idx1 in range(len(row) - 1):
                for idx2 in range(idx1 + 1, len(row)):
                    # if common ancestor is a dict, should be in different scope_tree
                    # if common ancestor is a list, should be in the same scope_tree
                    if not are_from_same_source(row[idx1], row[idx2]):
                        diff_scope_pairs.append((row[idx1], row[idx2]))
            # Next, organize diff scope_tree pairs into enemies
            # These enemies will have nodes in the same scope_tree
            enemies = group_enemies(diff_scope_pairs)
            same_scope_tree[level].append(enemies)
        elif len(row) == 1:
            same_scope_tree[level].append([[row[0]]])
        elif len(row) == 2:
            same_scope_tree[level].append([[row[0], row[1]]])

    same_scope_tree[0] = [[[root]]]
    same_scope_tree[1] = [[[n for n in scope_tree[1]]]]

    # for level in range(len(scope_tree)):
    #     row = scope_tree[level]
    #     print_list_of_nodes(row)

    return same_scope_tree


def print_list_of_nodes(lst):
    result = []
    for node in lst:
        result.append(str(node))
    print(result)


def get_scope_node_tree(json_dir):
    def search_parent_scope(parent_node, parent_level):
        for scope_node_with_lst in parent_level:
            scope_node = scope_node_with_lst[0]
            lst = scope_node_with_lst[1]
            for node in lst:
                if node == parent_node:
                    return scope_node
        return None

    def merge_same_scope(same_scope_lst):
        if not all(n.key == same_scope_lst[0].key for n in same_scope_lst):
            print("Warning: Different keys in same scope list.\n" +
                  "Implementation for same scope tree is incorrect.")
        key = same_scope_lst[0].key
        value_types = list({n.value_type for n in same_scope_lst})
        return ScopeNode(key, value_types)

    def convert_to_scope_node_with_tree(tree):
        # Each lst in tree now should be [ScopeNode, lst]
        new_tree = []
        for level in tree:
            for lsts in level:
                inner1 = []
                for lst in lsts:
                    inner2 = []
                    for node in lst:
                        inner2.append(node)
                        # print_list_of_nodes(inner2)
                    inner1.append([merge_same_scope(inner2), lst])
                new_tree.append(inner1)
        return new_tree

    same_scope_tree = get_same_scope_tree(json_dir)
    scope_node_with_tree = convert_to_scope_node_with_tree(same_scope_tree)

    result = []
    for i in range(len(scope_node_with_tree)-1, 0, -1):
        level = scope_node_with_tree[i]
        parent_level = scope_node_with_tree[i-1]
        inner = []
        for scope_node_with_lst in level:
            scope_node = scope_node_with_lst[0]
            lst = scope_node_with_lst[1]
            # search for parent of scope node from parent level
            # Take the first node of lst to search for parent (their parent should be the same)
            scope_node.parent = search_parent_scope(lst[0].parent, parent_level)
            # print(scope_node, '--parent--', scope_node.parent, lst)
            # print(scope_node.parent)
            inner.append(scope_node)
        result.append(inner)
    return result


def save_to_scope_node_JSON(scope_node_tree):
    def convert_to_scope_node_JSON():
        def pretty_print(scope_node_value_type):
            return '/'.join(scope_node_value_type)

        dicts = []
        for i in range(len(scope_node_tree)):
            grouped_scope_nodes = defaultdict(list)
            for j in range(len(scope_node_tree[i])):
                # Group scope nodes with the same parent together
                grouped_scope_nodes[scope_node_tree[i][j].parent].append(scope_node_tree[i][j])
            grouped_scope_nodes_dict = dict(grouped_scope_nodes)
            dicts.append(grouped_scope_nodes_dict)

        result = []
        for d in dicts:
            for parent_scope_node in d.keys():
                children = d[parent_scope_node]
                for child in children:
                    if child.value_type[0] == SQL_dict:
                        result.append((parent_scope_node, child, {}))
                    elif child.value_type[0] == SQL_list:
                        result.append((parent_scope_node, child, []))
                    else:
                        result.append((parent_scope_node, child, pretty_print(child.value_type)))
        return result

    def get_JSON_dict(scope_node_JSON):
        def search_parent_obj(parent_scope_node):
            for tu in scope_node_JSON:
                if tu[1] == parent_scope_node:
                    return tu[2]
            return None

        result = None
        for tu in scope_node_JSON:
            parent_scope_node = tu[0]
            scope_node = tu[1]
            obj = tu[2]
            parent_obj = search_parent_obj(parent_scope_node)
            if parent_obj is None:
                result = [obj]
            else:
                if isinstance(parent_obj, dict):
                    parent_obj[scope_node.key] = obj
                elif isinstance(parent_obj, list):
                    parent_obj.append(obj)
        return result

    scope_node_JSON = convert_to_scope_node_JSON()
    JSON_dict = get_JSON_dict(scope_node_JSON)

    with open('something.json', 'w') as json_file:
        json.dump(JSON_dict, json_file, indent=4)


def structure_check(json_dir):
    scope_node_tree = get_scope_node_tree(json_dir)
    save_to_scope_node_JSON(scope_node_tree)
    return True


if __name__ == "__main__":
    jsons = util.get_jsons_under(db_path.data_dir)
    for j in jsons:
        print(j)
        print(structure_check(j))
        print('-------')
