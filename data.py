from os import walk

f = []
for (dirpath, dirnames, filenames) in walk('./tracks/'):
    f.extend(filenames)

print(len(f))