import concurrent.futures

# Object class
from collections import Counter


class obj:
    def __init__(self, tup):
        self.tup = tup


# Dictionary full of instances of obj above
dic = {'a': obj(1),
       'b': obj(2),
       'c': obj(3),
       'd': obj(4),
       'e': obj(5),
       'f': obj(6),
       }


def get_new_value(dictionary_item):
    key, value = dictionary_item
    return key, 'work_' + str(value.tup)

def go():
    x = Counter()
  with concurrent.futures.ProcessPoolExecutor() as executor:
    for key, new_value in executor.map(get_new_value, dic.items()):
        dic[key].new = new_value
  # Make sure it really worked!
  for key, value in dic.items():
      print(key, value.new)


if __name__ == '__main__':
    go()
