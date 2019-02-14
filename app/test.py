import os,sys
parentdir = os.getcwd().rsplit('/', 1)[0]
print(parentdir)
sys.path.insert(0,parentdir)
print(sys.path)
import engines