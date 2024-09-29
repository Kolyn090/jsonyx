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


class Node:
    def __init__(self, key='', value_type=SQL_null, parent=None, child_count=0):
        self.key = key
        self.value_type = value_type
        self.parent = parent
        self.child_count = child_count

    def __str__(self):
        return f'@k={self.key}, v={self.value_type}, c={self.child_count}'


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
        enemy_groups = set(group_assignment.get(enemy) for enemy in graph[person] if enemy in group_assignment)

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


def structure_check(json_dir):
    with open(json_dir) as file:
        if file == '':
            return
        else:
            json_obj = json.loads(file.read())

    """ Search for scope_set """
    def get_node_type_of(n):
        if isinstance(n, (dict, list)):
            return 0 if isinstance(n, dict) else 1
        return 2

    # Keys must be from data / an empty string (if unnamed)
    # Names can be assigned by program

    # List<List<(Key, Type, Parent_Name, Parent_Type)>>
    scope_set = []

    # initialize name for dict under outermost list
    # List<(Node, Level)>
    root = Node('ROOT', SQL_list, None, len(json_obj))
    pq = [(e, 0, Node(value_type=SQL_dict, parent=root)) for i, e in enumerate(json_obj)]

    while len(pq) > 0:
        obj, node_level, curr_node = pq.pop(0)
        obj_type = get_node_type_of(obj)

        if len(scope_set) < node_level + 1:
            scope_set.append([])
        scope_set[node_level].append(curr_node)

        if obj_type == 0:  # dict
            curr_node.child_count = len(obj.items())
            for k, v in obj.items():
                new_node = Node(k, python_to_sql_type(type(v)), curr_node)
                pq.append((v, node_level + 1, new_node))
                # scope_set[node_level].append(new_node)
        elif obj_type == 1:  # list
            curr_node.child_count = len(obj)
            for idx, item in enumerate(obj):
                new_node = Node('', python_to_sql_type(type(item)), curr_node)
                pq.append((item, node_level + 1, new_node))
                # scope_set[node_level].append(new_node)

    scope_set.insert(0, [root])

    # for idx, row in enumerate(scope_set):
    #     print(f'{idx} -------------------')
    #     for node in row:
    #         print(node)

    """ Group records to the same scope_set """
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

    same_scope_set = [[] for _ in range(len(scope_set))]
    for level in range(2, len(scope_set)):
        row = scope_set[level]
        # Contain a pair of nodes that are in a different scope_set in this level
        diff_scope_pairs = []
        for idx1 in range(len(row)-1):
            for idx2 in range(idx1+1, len(row)):
                # if common ancestor is a dict, should be in different scope_set
                # if common ancestor is a list, should be in the same scope_set
                if not are_from_same_source(row[idx1], row[idx2]):
                    diff_scope_pairs.append((row[idx1], row[idx2]))
        # Next, organize diff scope_set pairs into enemies
        # These enemies will have nodes in the same scope_set
        enemies = group_enemies(diff_scope_pairs)
        same_scope_set[level].append(enemies)

    same_scope_set[0] = [[[root]]]
    same_scope_set[1] = [[[n for n in scope_set[1]]]]

    for level in same_scope_set:
        row1 = []
        for enemies in level:
            row2 = []
            for nodes in enemies:
                row3 = []
                for node in nodes:
                    row3.append(str(node))
                row2.append(row3)
            row1.append(row2)
        print(row1)
        print("-----")

    return True


if __name__ == "__main__":
    jsons = util.get_jsons_under(db_path.data_dir)
    for j in jsons:
        print(j)
        print(structure_check(j))
        print('-------')
