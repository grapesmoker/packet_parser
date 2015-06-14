import unittest
from Bonus import Bonus

class BonusTests(unittest.TestCase):

    def test_bonusLeadin(self):

        bonus = Bonus(leadin = "1. This is a leadin.")
        self.assertEqual("This is a leadin.", bonus.leadin, "Number should be removed from leadin.")

        bonus = Bonus(leadin = "TB. This is a tiebreaker.")
        self.assertEqual("This is a tiebreaker.", bonus.leadin, "TB. should be removed from leadin.")

        bonus = Bonus(leadin = "<strong>7.</strong> This person did something.")
        self.assertEqual("This person did something.", bonus.leadin, "<strong>Number</strong> should be removed from leadin.")

        bonus = Bonus(leadin = "6. <strong>This leadin is bold</strong>, for 10 points each.")
        self.assertEqual("<strong>This leadin is bold</strong>, for 10 points each.", bonus.leadin, "<strong> should be preserved in leadin text.")

        bonus = Bonus(leadin = " 6. Spaces should be removed.")
        self.assertEqual("Spaces should be removed.", bonus.leadin, "Spaces and numbers should have been removed.")


def assertEqual(testClass, expected, actual, message):
    testClass.assertEqual(expected, actual, "Expected: <" + expected + ">, Actual: <" + actual + ">. " + message)

if __name__ == '__main__':
    unittest.main()
