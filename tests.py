import unittest
from Bonus import Bonus, InvalidBonus

class BonusTests(unittest.TestCase):

    def test_bonusLeadin(self):

        bonus = Bonus(leadin = "1. This is a leadin.")
        assertEqual(self, "This is a leadin.", bonus.leadin, "Number should be removed from leadin.")

        bonus = Bonus(leadin = "TB. This is a tiebreaker.")
        assertEqual(self, "This is a tiebreaker.", bonus.leadin, "TB. should be removed from leadin.")

        bonus = Bonus(leadin = "<strong>7.</strong> This person did something.")
        assertEqual(self, "This person did something.", bonus.leadin, "<strong>Number</strong> should be removed from leadin.")

        bonus = Bonus(leadin = "6. <strong>This leadin is bold</strong>, for 10 points each.")
        assertEqual(self, "<strong>This leadin is bold</strong>, for 10 points each.", bonus.leadin, "<strong> should be preserved in leadin text.")

        bonus = Bonus(leadin = " 6. Spaces should be removed.")
        assertEqual(self, "Spaces should be removed.", bonus.leadin, "Spaces and numbers should have been removed.")

    def test_bonusIsValid(self):

        normalLeadin = "1. Bonus"
        normalParts = [ "First part", "Second part" ]
        manyParts = normalParts + [ "Third part" ]
        normalAnswers = [ "First answer", "Second answer" ]
        manyAnswers = normalAnswers + [ "Third answer" ]
        normalValues = [ 10, 10 ]
        manyValues = normalValues + [ 10 ]

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = normalAnswers, values = normalValues)
        self.assertTrue(bonus.is_valid(), "Good bonus should return true for is_valid")
        self.assertTrue(bonus.valid, "Good bonus should set valid field to true")

        bonus = Bonus(parts = normalParts, answers = normalAnswers, values = normalValues)
        self.isValidThrows(bonus, "Bonus with no leadin should not be valid.")

        bonus = Bonus(leadin = normalLeadin, answers = normalAnswers, values = normalValues)
        self.isValidThrows(bonus, "Bonus with no parts should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, values = normalValues)
        self.isValidThrows(bonus, "Bonus with no answers should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = normalAnswers)
        self.isValidThrows(bonus, "Bonus with no values should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = ["", "A"], answers = normalAnswers, values = normalValues)
        self.isValidThrows(bonus, "Bonus with an empty part should not be valid.")

        # Valid for now. We should consider making this invalid.
        #bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = ["", "A"], values = normalValues)
        #self.isValidThrows(bonus, "Bonus with an empty answer should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = normalAnswers, values = [ '10', '10' ])
        self.assertTrue(bonus.is_valid(), "Bonus with numeric string values should be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = normalAnswers, values = [ 'X', 1] )
        self.isValidThrows(bonus, "Bonus with a non-numeric value should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = normalAnswers, values = [ '', 10 ])
        self.isValidThrows(bonus, "Bonus with an empty value should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = manyParts, answers = normalAnswers, values = normalValues)
        self.isValidThrows(bonus, "Bonus with too many parts should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = manyAnswers, values = normalValues)
        self.isValidThrows(bonus, "Bonus with too many answers should not be valid.")

        bonus = Bonus(leadin = normalLeadin, parts = normalParts, answers = normalAnswers, values = manyValues)
        self.isValidThrows(bonus, "Bonus with too many values should not be valid.")

    def test_bonusAnswer(self):

        parts = [ "First part", "Second part" ]
        bonus = Bonus(parts = parts, answers = [ "<strong><em>Strong</strong></em> first", "<em><strong>Em</em></strong> first" ])
        assertEqual(self, "<req>Strong</req> first", bonus.answers[0], "<strong><em> pair not escaped properly")
        assertEqual(self, "<req>Em</req> first", bonus.answers[1], "<em><strong> pair not escaped properly")

        # Make sure we escape mixed end tags
        bonus = Bonus(parts = parts, answers = [ "<strong><em>Strong</em></strong> first", "<em><strong>Em</strong></em> first" ])
        assertEqual(self, "<req>Strong</req> first", bonus.answers[0], "<strong><em></em></strong> not escaped properly")
        assertEqual(self, "<req>Em</req> first", bonus.answers[1], "<em><strong></strong></em> not escaped properly")

    def test_bonusSanitization(self):
        parts = [ "He wrote <i>Long Day's Journey Into Night</i>" ]
        answers = [ "Eugene <strong><em>O'Neill</strong></em>" ]
        bonus = Bonus(leadin = "He wrote <em>The Emperor Jones</em>.", parts = parts, answers = answers)

        assertEqual(self, "He wrote The Emperor Jones.", bonus.leadin_sanitized, "Leadin not sanitized.")
        assertEqual(self, "He wrote Long Day's Journey Into Night", bonus.parts_sanitized[0], "Parts not sanitized.")
        assertEqual(self, "Eugene O'Neill", bonus.answers_sanitized[0], "Answers not sanitized.")
        
    def isValidThrows(self, bonus, message):
        try:
            bonus.is_valid()
            self.fail(message)
        except InvalidBonus:
            pass

# TODO: Make this part of a base test class that other tests inherit from?
def assertEqual(testClass, expected, actual, message):

    testClass.assertEqual(expected, actual, "Expected: <" + expected + ">, Actual: <" + actual + ">. " + message)

if __name__ == '__main__':

    unittest.main()
