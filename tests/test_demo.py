from unittest import TestCase, main
from scratchpad import test2


class TestMain(TestCase):

    def test_sub1_assert_true(self):
        self.assertTrue(test2.sub1() == "world!")
        
    def test_sub1_assert_equals(self):
        self.assertEqual(test2.sub1(), "world")
        
    def test_sub1_assert_in(self):
        self.assertIn("world",test2.sub1())


if __name__ == '__main__':
    main()
