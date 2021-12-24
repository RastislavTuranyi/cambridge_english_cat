from abc import ABC, abstractmethod
import csv
import os
import random

import numpy as np


class TestEndError(Exception):
    """An error class used to signal that the exam has come to an end."""
    pass


class LowCertaintyError(Exception):
    """
    An error class used to signal that not enough questions have been asked at the difficulty determined to be
    the result or its adjacent difficulties.
    """
    def __init__(self, result: str, difficulty, extra_questions=5, *args):
        self.difficulty = difficulty
        self.extra_questions = extra_questions
        if result == difficulty:
            self.blurb = f'We have got an idea of which level your English language skills are at ({result}), but ' \
                         'because we have not given you enough questions of this level, we are not very certain that ' \
                         'we are correct. If you want to proceed to view your results nevertheless, you can do so, ' \
                         'or you can take a couple more questions to increase our certainty.'
        else:
            self.blurb = f'We have got an idea of which level your English language skills are at ({result}) from ' \
                         f'the questions of this difficulty you have answered. However, we try to give you questions ' \
                         f'of various difficulties to increase our accuracy and improve our feedback. Unfortunately, ' \
                         f'we failed to give you enough questions of the {difficulty.name} level. You don\'t need to' \
                         f' do these questions and can directly proceed to see the results, but you can continue the ' \
                         f'exam if you want better feedback.'
        super().__init__(args)


class InconsistentResultsError(Exception):
    """
    An error class used to signal that the results of questions of different difficulties are not consistent with
    each other.
    """
    blurb = 'This software uses questions of different difficulties to determine the level of your English language ' \
            'skills. Unfortunately, this failed to happen, because you were not able to answer easier questions but ' \
            'were able to answer more difficult questions. To make our assessment more accurate, you can answer a few' \
            ' more questions. Otherwise, you can proceed to view your results.'

    def __init__(self, difficulty, extra_questions=5, *args):
        self.difficulty = difficulty
        self.extra_questions = extra_questions
        super().__init__(args)


class Tester:
    """
    The main class of the tester module, Tester manages the whole test.

    :ivar difficulty: the Difficulty of the current question
    :ivar difficulties: a list keeping track of all past Difficulty -ies
    :ivar qno: the 0-based index of the current question
    :ivar qtypes: keeps track of the Question class of all past questions
    :ivar used_qs: keeps track of which questions from which file and which difficulty have been used in the past
    :ivar correct_answers: logs the correct answers to all past questions
    :ivar submitted_answers: logs the answers inputted by the user
    :ivar scores: logs the points assigned for each answered question

    :ivar grades: stores the grade (A-E) assigned to the user for each question difficulty (A0-C2)
    :ivar certainty: stores the certainty with which each grade has been assigned based on the number of questions
                     administered for a particular difficulty
    :ivar result: the CEFR level assigned to the user
    :ivar evaluation: a flavour text written based on the various results
    :ivar shields: the number of shields assigned for A0 and A1 levels. Essentially replaces grades in these cases.
    """
    def __init__(self):
        self.default_questions = 30
        # Dynamically altered during the test
        self.difficulty = B1
        self.difficulties = []
        self.qno = 0
        self.extra_questions = 0
        self.skip_evaluate = False
        # Variables keeping track of questions
        self.qtypes = []
        self.used_qs = {}
        # Variable keeping track of answers
        self.correct_answers = []
        self.submitted_answers = []
        self.scores = []

        # Filled at the test end by evaluate() method
        self.grades = [None for __ in range(7)]
        self.certainty = [(0, '') for __ in range(7)]
        self.result = ''
        self.evaluation = ''
        self.shields = [0, 0]
        self.final = np.zeros(7, dtype=float)
        self.asked_questions = np.zeros(7, dtype=float)

    def get_question(self):
        """
        Sets up a new question by selecting an appropriate difficulty and class and logging important information.
        :return: None
        """
        if not self.skip_evaluate:  # Keep the difficulty if the flag is True
            self.change_difficulty()
        else:
            self.skip_evaluate = False

        qclass = self.get_question_class()
        self.question = qclass(self.difficulty.name, self.used_qs, self.qno)
        # Save the correct answers
        self.correct_answers.append('/'.join(self.question.answers))

        # Save which question has been given to prevent repetition
        if isinstance(self.question, LineQuestion):
            if self.used_qs.get(self.question.csv_path, None) is not None:
                self.used_qs[self.question.csv_path].append(self.question.lineno)
            else:
                self.used_qs[self.question.csv_path] = [self.question.lineno]
        else:
            if self.used_qs.get(self.question.csv_path, None) is not None:
                self.used_qs[self.question.csv_path].append((self.question.block, self.question.qnumber))
            else:
                self.used_qs[self.question.csv_path] = [(self.question.block, self.question.qnumber)]

        self.qno += 1

    def change_difficulty(self):
        """Determines the difficulty of the new question."""
        if self.qno == 0:
            new_level_index = self.difficulty.index

        # At the beginning, immediately adjust difficulty up or down depending on if the answer was correct
        elif self.qno < 5:
            previous_level_index = levels.index(levels[self.difficulties[-1]])

            if self.scores[self.qno-1] == 0 or self.difficulty.name == 'C2':  # If answer is incorrect or highest diff
                if previous_level_index == 0:  # Don't adjust pre-A1 → C2
                    new_level_index = previous_level_index
                else:
                    new_level_index = previous_level_index - 1
            else:
                new_level_index = previous_level_index + 1

        # After first 5 qs, give questions of the highest difficulty which has been answered correctly
        elif self.qno == 5:
            new_level_index = 0
            for difficulty, score in zip(self.difficulties[:5], self.scores[:5]):
                if score and difficulty > new_level_index:
                    new_level_index = difficulty

        # Use blocks of 5 questions
        elif ((self.qno) % 5) != 0:
            new_level_index = self.difficulty.index

        # Adjust difficulty on every 5th question
        else:
            total_score = sum(self.scores[(self.qno-5):(self.qno+1)])  # score of the previous block

            if total_score >= 5 and self.difficulty.name != 'C2':  # Move up if score > 85%
                new_level_index = self.difficulty.index + 1
            elif (total_score >= 3 or (self.difficulty.name == 'C2' and total_score >= 3)
                  or self.difficulty.name == 'A0'):  # Keep the current difficulty above 60%
                new_level_index = self.difficulty.index
            else:
                new_level_index = self.difficulty.index - 1

            if (all(elem == self.difficulties[-1] for elem in self.difficulties[(self.qno-15):(self.qno+1)]) and
                    self.qno > 15 and new_level_index == self.difficulty.index):
                self.default_questions = self.qno
                raise TestEndError()
            elif self.qno == (self.default_questions + self.extra_questions):
                raise TestEndError()

        self.difficulty = levels[new_level_index]
        self.difficulties.append(self.difficulty.index)

    def get_question_class(self):
        if self.qno <= 4:
            if 'open cloze' in self.difficulty:
                next_type = 'open cloze'
            elif 'reading' in self.difficulty:
                next_type = 'reading'
            else:
                next_type = 'spelling'
        # TODO: make key word transformation sure to appear
        else:
            randnum = random.randint(0, len(self.difficulty)-1)
            keys = list(self.difficulty.keys())

            # Keep choosing random question type until it is different from the previous question
            while keys[randnum] == self.qtypes[self.qno-1]:
                randnum = random.randint(0, len(self.difficulty) - 1)
            next_type = keys[randnum]

        self.qtypes.append(next_type)
        return self.difficulty[next_type]

    def check_answer(self):
        self.scores.append(self.question.check_answer(self.submitted_answers[self.qno-1]))

    def evaluate(self):
        self.evaluation = ''

        for index, (difficulty, score) in enumerate(zip(self.difficulties, self.scores)):
            self.final[difficulty] += score
            self.asked_questions[difficulty] += 1 if self.qtypes[index] != 'key word transformations' else 2

        # Divide such that 0/0 = 0
        accuracies = np.divide(self.final, self.asked_questions,
                               out=np.zeros_like(self.final), where=self.asked_questions!=0)

        for difficulty, (score, questions, accuracy) in enumerate(zip(self.final, self.asked_questions, accuracies)):
            if questions > 15:
                self.certainty[difficulty] = (5, 'very high accuracy')
            elif questions > 10:
                self.certainty[difficulty] = (4, 'high accuracy')
            elif questions == 10:
                self.certainty[difficulty] = (3, 'fairly high accuracy')
            elif questions > 5:
                self.certainty[difficulty] = (2, 'considerable accuracy')
            elif questions > 2:
                self.certainty[difficulty] = (1, 'low accuracy')
            else:
                self.certainty[difficulty] = (0, 'too few questions')
                self.grades[difficulty] = None
                continue

            if difficulty in [0, 1]:
                if accuracy >= 0.65:
                    self.grades[difficulty] = 'C'
                else:
                    self.grades[difficulty] = 'D'
            elif accuracy >= levels[difficulty].grade_a:
                self.grades[difficulty] = 'A'
            elif accuracy >= levels[difficulty].grade_b:
                self.grades[difficulty] = 'B'
            elif accuracy >= levels[difficulty].grade_c:
                self.grades[difficulty] = 'C'
            elif accuracy >= levels[difficulty].lower_level:
                self.grades[difficulty] = 'D'
            else:
                self.grades[difficulty] = 'E'

        # Find the highest difficulty that has achieved at least a passing grade
        highest_passed_difficulty = -1
        for difficulty, grade in enumerate(self.grades):
            if difficulty > highest_passed_difficulty and grade is not None and grade < 'D':
                highest_passed_difficulty = difficulty

        # Set shorthands for the highest passed level and its neighbours
        if highest_passed_difficulty > 0:
            previous_level = levels[highest_passed_difficulty - 1].name
        achieved_level = levels[highest_passed_difficulty].name
        if highest_passed_difficulty < 6:
            higher_level = levels[highest_passed_difficulty + 1].name

        # Grade the pre-A1 and A1 exams regardless of if they have been passed
        if highest_passed_difficulty in [0, 1] or (highest_passed_difficulty == -1 and
                                                   (self.asked_questions[0] >= 5 or self.asked_questions[1] >= 5)):
            # Assign A1 grade if 4+ shields have been achieved in A1 test, otherwise assign pre-A1
            if self.grades[1] == 'C':
                self.result = 'A1'
            else:
                self.result = 'pre-A1'

            # Determine the number of shields
            for difficulty, accuracy in enumerate(accuracies[:2]):
                if accuracy >= 0.85:
                    self.shields[difficulty] = 5
                elif accuracy >= 0.65:
                    self.shields[difficulty] = 4
                elif accuracy >= 0.45:
                    self.shields[difficulty] = 3
                elif accuracy >= 0.25:
                    self.shields[difficulty] = 2
                else:
                    if self.certainty[difficulty][0] == 0:
                        self.shields[difficulty] = 0
                    else:
                        self.shields[difficulty] = 1

            self.evaluation = ' '.join([self.evaluation, f'You have achieved {self.result} level. You have obtained '
                                                         f'{self.shields[0]} out of 5 shields on the pre-A1 exam and '
                                                         f'{self.shields[1]} out of 5 shields on the A1 exam.'])
            return  # Skip everything else
        else:
            if highest_passed_difficulty == -1:
                self.result = 'None'
                self.evaluation = ' '.join([self.evaluation, 'Your level could not be determined because you have not '
                                                             'passed any difficulty level.'])

                # Find the lowest difficulty in which D grade has been achieved, and set that as potential continue
                for difficulty, grade in enumerate(self.grades):
                    if grade is not None and grade == 'D':
                        raise InconsistentResultsError(grade, 15)
                else:
                    raise InconsistentResultsError(A0, 15)
            else:
                self.result = levels[highest_passed_difficulty].name
                self.evaluation = ' '.join([self.evaluation, f'You have passed the {achieved_level} exam and obtained a'
                                                             f' {self.grades[highest_passed_difficulty]} grade in it.'])
                if self.grades[highest_passed_difficulty] == 'A':
                    try:
                        self.evaluation += f' This indicates that your skills are of the higher level, ' \
                                           f'{higher_level} instead.'
                    except NameError:
                        self.evaluation += ' This shows you have almost mastered the English language.'
                elif self.grades[highest_passed_difficulty] == 'B':
                    try:
                        self.evaluation += f' This shows you have very good grasp of this level of English. It ' \
                                           f'indicates that you are approaching the higher level, {higher_level}, ' \
                                           f'though you are not quite there yet.'
                    except NameError:
                        self.evaluation += ' This means you are close to mastering the English language, but there ' \
                                           'is still a little way remaining before you have completely mastered it.'
                elif self.grades[highest_passed_difficulty] == 'C':
                    try:
                        self.evaluation += f' This shows you have a solid grasp of this level, but there is still a ' \
                                           f'room to improve before you can start thinking of progressing to the ' \
                                           f'next level, {higher_level}.'
                    except NameError:
                        self.evaluation += ' This shows you have a solid grasp of this level, but there is still room' \
                                           ' for improvement before you can say you have mastered the English language.'
                else:
                    raise NotImplementedError('This should never happen.')

                if self.certainty[highest_passed_difficulty][0] < 3:
                    raise LowCertaintyError(self.result, levels[highest_passed_difficulty])

        # Show confusion if a lower difficulty than the highest passed has been failed
        for index, grade in enumerate(self.grades[:highest_passed_difficulty]):
            if grade is not None and grade >= 'D':
                self.evaluation = ''.join([self.evaluation, ''])
                raise InconsistentResultsError(levels[index])

        # Add flavour text based on the lower level than the highest passed one
        if self.grades[highest_passed_difficulty - 1] is None:
            self.evaluation = ' '.join([self.evaluation, f'Not enough information has been gathered from '
                                                         f'{previous_level}-level questions to evaluate if they agree'
                                                         f'or disagree with the evaluation above of {achieved_level}.'])
            raise LowCertaintyError(self.result, levels[highest_passed_difficulty - 1], 10)
        elif self.grades[highest_passed_difficulty - 1] == 'A':
            self.evaluation = ' '.join([self.evaluation, f'You have also achieved an A grade in the level below,'
                                                         f'{previous_level}, which is equivalent to the '
                                                         f'{achieved_level}, further proving that your skill is at the '
                                                         f'{achieved_level} level.'])
        else:
            self.evaluation = ' '.join([self.evaluation, f'However, you have achieved only a '
                                                         f'{self.grades[highest_passed_difficulty - 1]} grade in the '
                                                         f'level below, {previous_level}, which indicates that your '
                                                         f'skills are limited to this level and that you have not '
                                                         f'achieved the {achieved_level} level.'])
            raise InconsistentResultsError(levels[highest_passed_difficulty - 1])

        # Add flavour text based on the level higher than the highest passed one
        if highest_passed_difficulty == 6:
            pass
        elif self.grades[highest_passed_difficulty + 1] is None:
            self.evaluation = ' '.join([self.evaluation, f'Not enough information has been gathered from '
                                                         f'{higher_level}-level questions to evaluate if they agree'
                                                         f'or disagree with the evaluation above of {achieved_level}.'])
            raise LowCertaintyError(self.result, levels[highest_passed_difficulty + 1])
        elif self.grades[highest_passed_difficulty + 1] == 'D':
            self.evaluation = ' '.join([self.evaluation, f'Furthermore, you have achieved a D grade in the higher-level'
                                                         f'{higher_level} exam, which further indicates that your '
                                                         f'skills are at the {achieved_level} level.'])
            if self.grades[highest_passed_difficulty] == 'A':
                raise InconsistentResultsError(levels[highest_passed_difficulty + 1])
        elif self.grades[highest_passed_difficulty + 1] == 'E':
            self.evaluation = ' '.join([self.evaluation, f'Unfortunately, despite your success in the '
                                                         f'{achieved_level} exam, you have failed the higher-level one,'
                                                         f' {higher_level} terribly, which puts the {achieved_level} '
                                                         f'evaluation to question.'])
            raise InconsistentResultsError(levels[highest_passed_difficulty + 1])


class Question(ABC):
    name = ''

    def __init__(self, difficulty: str, used_qs: dict, qno: int):
        self.lineno = 0
        self.qnumber = 0

        self.answers = []
        self.image = ''
        self.keyword = ''
        self.options = []
        self.question = ''
        self.text = ''
        self.title = ''
        self.titles = []
        self.subtitle = ''

        pwd = os.path.dirname(os.path.realpath(__file__))
        self.csv_path = os.path.join(pwd, 'Data', difficulty, ''.join([self.name, '.csv']))

        with open(self.csv_path, encoding='utf-8') as file:
            csv_file = [i for i in csv.reader(file, delimiter=';') if i]
            file_length = len(csv_file)

        self.select_question(csv_file, file_length, used_qs, difficulty=difficulty, qno=qno)

    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        pass


class LineQuestion(Question, ABC):
    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        for __ in range(file_length * 5):
            self.lineno = random.randint(0, file_length - 1)
            if self.lineno not in used_qs.get(self.csv_path, []):
                break


class BlockQuestion(Question, ABC):
    block_length = 0
    question_location = 0

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        if file_length % self.block_length != 0:
            raise Exception(file_length)
        else:
            blocks = int(file_length / self.block_length)

        for __ in range(blocks*5):
            self.block = random.randint(0, blocks - 1)
            self.questions = csv_file[self.block * self.block_length + self.question_location]

            for ___ in range(len(self.questions)*5):
                self.qnumber = random.randint(0, len(self.questions) - 1)

                if (self.block, self.qnumber) not in used_qs.get(self.csv_path, []):
                    # Save title, subtitle, and text from the first line of the block
                    try:
                        self.title = csv_file[self.block * self.block_length][0]
                        self.subtitle = csv_file[self.block * self.block_length][1]
                        self.text = csv_file[self.block * self.block_length][2].replace(f'({self.qnumber + 1}) '
                                                                                        f'..........',
                                                                                        f'<b>[{kwargs["qno"] + 1}] '
                                                                                        f'..........<b>')
                    except IndexError:
                        print('Title, subtitle, and text could not be loaded',
                              self.name, csv_file[self.block * self.block_length])
                    return  # break

    @abstractmethod
    def overwrite_text(self, csv_file, used_qs):
        # Remove the numbers in brackets from gaps
        for i, __ in enumerate(csv_file[self.block * self.block_length + 1]):
            self.text = self.text.replace(f'({i + 1})', '')


class MultipleChoiceQuestion(Question, ABC):
    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

    def check_answer(self, submitted_answer):
        if submitted_answer == self.answers[0]:
            return 1
        else:
            return 0


class OpenAnswerQuestion(Question, ABC):
    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

    def check_answer(self, submitted_answer):
        for correct_answer in self.answers:
            if submitted_answer.strip().lower() == correct_answer.strip().lower():
                return 1
        else:
            return 0


class BlockMultipleChoiceQuestion(BlockQuestion, MultipleChoiceQuestion, ABC):
    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

    def overwrite_text(self, csv_file, used_qs):
        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        # Replace the gaps that have been answered previously with the correct answer
        for (block, qnumber) in used_qs.get(self.csv_path, []):
            if block == self.block:
                correct_answer = letters.find(csv_file[block * self.block_length + self.question_location][qnumber])
                answer_text = self.get_correct_answer_text(block, correct_answer, csv_file, qnumber)
                self.text = self.text.replace(''.join(['(', str(qnumber + 1), ') ..........']), answer_text)

        super().overwrite_text(csv_file, used_qs)

    @abstractmethod
    def get_correct_answer_text(self, block, correct_answer, csv_file, qnumber):
        pass


class BlockOpenAnswerQuestion(BlockQuestion, OpenAnswerQuestion, ABC):
    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

    def overwrite_text(self, csv_file, used_qs):
        for (block, qnumber) in used_qs.get(self.csv_path, []):
            if block == self.block:
                correct_answer = csv_file[block * self.block_length + self.question_location][qnumber].split(',')[0]
                self.text = self.text.replace(''.join(['(', str(qnumber + 1), ') ..........']), correct_answer)

        super().overwrite_text(csv_file, used_qs)


class GappedText(BlockMultipleChoiceQuestion):
    name = 'gapped text'
    instruction = 'Several sentences/paragraphs have been removed from the text below. Choose which sentence/paragraph' \
                  ' has been removed from the highlighted gap.'
    block_length = 3
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.answers = [csv_file[self.block * self.block_length + 1][self.qnumber]]
        self.options = csv_file[self.block * self.block_length + 2]

        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.titles = [letters[i] for i, __ in enumerate(csv_file[self.block * self.block_length + 2])]

        self.overwrite_text(csv_file, used_qs)

    def get_correct_answer_text(self, block, correct_answer, csv_file, qnumber):
        return csv_file[block * self.block_length + 2][correct_answer]


class GappedTextA(GappedText):
    name =  'gapped text A'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.instruction = f'Read this. Choose a word from the box to answer question {kwargs["qno"] + 1}'
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(self.block), '.png']))


class KeyWordTransformations(LineQuestion):
    name = 'key word transformations'
    instruction = 'Complete the second sentence so that it has a similar meaning to the first sentence, using the ' \
                  'word given. <b>Do not change the word given<b>. You must use between <b>two<b> and <b>five<b> ' \
                  'words, including the word given.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.difficulty = kwargs['difficulty']
        if self.difficulty == 'C1':
            self.instruction = self.instruction.replace('two','three').replace('five', 'six')
        elif self.difficulty == 'C2':
            self.instruction = self.instruction.replace('two', 'three').replace('five', 'eight')

        line = csv_file[self.lineno]
        self.text = line[0]
        self.keyword = line[1]
        self.question = line[2]
        self.answers = line[3:]

    def check_answer(self, submitted_answer):
        scores = np.zeros(len(self.answers), dtype=int)
        submitted_words = submitted_answer.lower().replace(',', '').replace('.', '').replace(';', '').split()

        if ((self.difficulty == 'B2' and not (2 <= len(submitted_words) <= 5)) or
                (self.difficulty == 'C1' and not (3 <= len(submitted_words) <= 6)) or
                (self.difficulty == 'C2' and not (3 <= len(submitted_words) <= 8))):
            return 0

        # Score the submitted answer against each possible correct answer
        for answer_number, correct_answer in enumerate(self.answers):
            halves = correct_answer.lower().split('|')
            offset = [0]

            # Score the two halves (separated by |) separately
            for half_number, half in enumerate(halves):
                words = half.split()

                # For the second half, search where it may be beginning by searching for the first word
                if half_number == 1:
                    offset = [j for j, answer in enumerate(submitted_words) if answer == words[0]]
                    if not offset:
                        break

                # Go through all the occurrences of the first word of the second half, and increase the score only if
                # all the words after that also match
                for off in offset:
                    for i, word in enumerate(words):
                        try:
                            if word != submitted_words[i + off]:
                                break
                        except IndexError:
                            break
                    else:
                        scores[answer_number] += 1
                        break

        return max(scores)


class Matching(LineQuestion, OpenAnswerQuestion):
    name = 'matching'
    instruction = 'Look and read. Choose the correct word from the pictures.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        line = csv_file[self.lineno]
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(line[0]), '.png']))
        self.answers = [line[1]]
        self.question = line[2]


class MultipleChoice(LineQuestion, MultipleChoiceQuestion):
    name = 'multiple choice'
    instruction = 'Read the text below, then answer the question about the text.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        line = csv_file[self.lineno]
        self.title = line[0]
        self.subtitle = line[1]
        self.text = line[2]
        self.answers = [line[3]]
        self.question = line[4]
        self.options = line[5:]


class MultipleChoiceA1(MultipleChoice):
    instruction = 'Read the text and choose the best answer.'


class MultipleMatch(BlockMultipleChoiceQuestion):
    name = 'multiple match'
    block_length = 4
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.instruction = csv_file[self.block * self.block_length][0]
        self.question = self.questions[self.qnumber]
        self.answers = [csv_file[self.block*4+3][self.qnumber]]
        self.options = csv_file[self.block*4+2][1::2]

        if csv_file[self.block*4+2][4]:
            self.titles = csv_file[self.block*4+2][::2]
        else:
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            self.titles = [letters[i] for i, __ in enumerate(csv_file[self.block*4+2][::2])]

            if csv_file[self.block*4+2][0]:
                self.title = csv_file[self.block*4+2][0]
            if csv_file[self.block*4+2][2]:
                self.subtitle = csv_file[self.block*4+2][2]

    def get_correct_answer_text(self, block, correct_answer, csv_file, qnumber):
        return csv_file[block * self.block_length + 2][correct_answer * 2]


class MultipleChoiceCloze(BlockMultipleChoiceQuestion):
    name = 'multiple-choice cloze'
    block_length = 3
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        if kwargs['difficulty'] == 'A1':
            self.instruction = f'Read the text. Choose the right word for gap number {kwargs["qno"] + 1}.'
        else:
            self.instruction = f'Select which word fits best into the gap number {kwargs["qno"] + 1}. There is' \
                               f' exactly 1 correct answer.'

        self.answers = [csv_file[self.block * self.block_length + self.question_location][self.qnumber]]
        self.options = csv_file[self.block * self.block_length + 2][self.qnumber].split(',')

        self.overwrite_text(csv_file, used_qs)

    def get_correct_answer_text(self, block, correct_answer, csv_file, qnumber):
        return csv_file[block * self.block_length + 2][qnumber].split(',')[correct_answer]


class OpenCloze(BlockOpenAnswerQuestion):
    name = 'open cloze'
    instruction = 'Write <b>one<b> missing word into the highlighted gap. Take care with spelling. There' \
                  ' may be multiple correct answers, but only enter one.'
    block_length = 2
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)
        self.answers = csv_file[self.block * self.block_length + self.question_location][self.qnumber].split(',')
        self.overwrite_text(csv_file, used_qs)


class Questions(LineQuestion, OpenAnswerQuestion):
    name = 'questions'
    instruction = 'Look at the picture and read the question. Write a <b>one-word<b> answer.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        line = csv_file[self.lineno]
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(line[0]), '.png']))
        self.question = line[1]
        self.text = line[2]
        self.answers = line[3:]


class Reading(LineQuestion):
    name = 'reading'
    instruction = 'Read the story. Write some words to complete the sentences about the story. ' \
                  'You can use <b>1, 2 or 3 words<b>.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        line = csv_file[self.lineno]
        self.title = line[0]
        self.subtitle = line[1]
        self.text = line[2]

        self.question = line[3]
        self.answers = line[4:]

    def check_answer(self, submitted_answer):
        submitted_words = submitted_answer.lower().replace(',', '').replace('.', '').replace(';', '').split()

        if not (1 <= len(submitted_words) <= 3):
            return 0

        for correct_answer in self.answers:
            correct_words = correct_answer.lower().split()
            for word, correct_word in zip(submitted_words, correct_words):
                if word != correct_word:
                    break
            else:
                return 1
        else:
            return 0



class ReadingComprehension(LineQuestion, OpenAnswerQuestion):
    name = 'reading comprehension'
    instruction = 'Look and read. Write <b>yes<b> or <b>no<b>.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        line = csv_file[self.lineno]
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(line[0]), '.png']))
        self.answers = [line[1]]
        self.question = line[2]


class ReadPicture(LineQuestion, MultipleChoiceQuestion):
    name = 'read picture'
    instruction = 'For the question below, choose the correct answer.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs)
        line = csv_file[self.lineno]

        self.answers = [line[0]]
        self.question = line[1]
        self.options = line[2:]
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(self.lineno), '.png']))


class Spelling(LineQuestion, OpenAnswerQuestion):
    name = 'spelling'
    instruction = 'Look at the pictures. Look at the letters. Write the words.'

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.answers = [csv_file[self.lineno][0]]
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(self.lineno), '.png']))


class WordFormation(BlockOpenAnswerQuestion):
    name = 'word formation'
    block_length = 3
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        while self.qnumber == 0:
            super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.answers = csv_file[self.block * self.block_length + 1][self.qnumber].split(',')
        self.keyword = csv_file[self.block * self.block_length + 2][self.qnumber]

        self.instruction = f'Use the stem word below the text to form a word that fits into the highlighted gap. As ' \
                           f'an example, gap number 0 would have the stem word <b>' \
                           f'{csv_file[self.block * self.block_length + 1][0]}<b> which you would modify into ' \
                           f'<b>{csv_file[self.block * self.block_length + 2][0]}<b>.'

        self.overwrite_text(csv_file, used_qs)


class Difficulty(dict):
    def __init__(self, name: str, index: int, grade_a: float, grade_b: float, grade_c: float, lower_level: float,
                 *args, **kwargs):
        self.name = name
        self.index = index
        self.grade_a = grade_a
        self.grade_b = grade_b
        self.grade_c = grade_c
        self.lower_level = lower_level
        super().__init__(*args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, Difficulty):
            return self.name == other.name
        else:
            return NotImplementedError

    def __ne__(self, other):
        eq = Difficulty.__eq__(self, other)
        return NotImplementedError if eq is NotImplementedError else not eq

    def __str__(self):
        return f'({self.name}, {super().__str__()})'


A0 = Difficulty('A0', 0, None, None, None, None,
                [('gapped text A', GappedTextA), ('questions', Questions), ('read picture', ReadPicture),
                          ('reading comprehension', ReadingComprehension), ('spelling', Spelling)])

A1 = Difficulty('A1', 1,  None, None, None, None,
                [('gapped text A', GappedTextA), ('matching', Matching), ('multiple choice', MultipleChoiceA1),
                 ('multiple-choice cloze', MultipleChoiceCloze), ('reading', Reading)])

A2 = Difficulty('A2', 2, 28/30, 28/30/140*133, 2/3, 13/30,
                [('multiple choice', MultipleChoice), ('multiple-choice cloze', MultipleChoiceCloze),
                 ('open cloze', OpenCloze), ('multiple match', MultipleMatch), ('read picture', ReadPicture)])

B1 = Difficulty('B1', 3, 29/32, 29/32/160*153, 23/32, 13/32,
                [('gapped text', GappedText), ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                 ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                  ('read picture', ReadPicture)])

B2 = Difficulty('B2', 4, 37/42, 37/42/180*173, 24/42, 16/42,
                [('gapped text', GappedText), ('key word transformations', KeyWordTransformations),
                 ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                 ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                 ('word formation', WordFormation)])

C1 = Difficulty('C1', 5, 43/50, 43/50/200*193, 32/50, 23/50,
                [('gapped text', GappedText), ('key word transformations', KeyWordTransformations),
                 ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                 ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                 ('word formation', WordFormation)])

C2 = Difficulty('C2', 6, 36/44, 36/44/220*213, 28/44, 22/44,
                [('gapped text', GappedText), ('key word transformations', KeyWordTransformations),
                 ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                 ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                 ('word formation', WordFormation)])

levels = [A0, A1, A2, B1, B2, C1, C2]
