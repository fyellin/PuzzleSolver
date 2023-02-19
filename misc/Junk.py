import sys
import unittest


SETTINGS = {}
print(id(SETTINGS))

class MyTests(unittest.TestCase):
    def test_foobar(self):
        print(id(SETTINGS))
        self.assertEqual(2, 3)


if __name__ == '__main__':
    print('hello')
    unittest.main()
