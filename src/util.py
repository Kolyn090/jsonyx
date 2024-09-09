import os


def get_jsons_under(directory):
    result = []

    def rec(root):
        if os.path.isdir(root):
            subdirs = os.listdir(root)
            for subdir in subdirs:
                rec(f"{root}/{subdir}")
        else:
            if not root.endswith('.json'):
                return
            result.append(root)

    rec(directory)

    return result
