import tarfile


def rename_file(filename, postfix, files_list):
    if filename + postfix in files_list:
        i = 0
        newname = filename + '_%d%s' % (i, postfix)
        while newname in files_list:
            i += 1
            newname = filename + '_%d%s' % (i, postfix)
        filename = newname
    else:
        filename = filename + postfix
    return filename

