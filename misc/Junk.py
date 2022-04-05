import sys

class Classmate:
    def __init__(self, name):
        self.name = name

    def hello(self):
        print(f'My name is {self.name} and I am a', end = '')

classmate1 = Classmate(sys.argv[1])
classmate1.hello()
print(classmate1.__class__)
