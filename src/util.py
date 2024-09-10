import os


def get_jsons_under(directory):
    result = []

    def rec(root):
        if os.path.isdir(root):
            subdirs = os.listdir(root)
            for subdir in subdirs:
                rec(os.path.join(root, subdir.lstrip("/\\")))
        else:
            if not root.endswith('.json'):
                return
            result.append(root)

    rec(directory)

    return result
