from abc import ABC, abstractmethod
import csv
import os
import random

import numpy as np


class Tester:

    def __init__(self):
        self.difficulty = temp
        self.qno = -1
        self.qtypes = np.zeros(30, dtype=object)
        self.used_qs = {}
        self.answers = np.zeros((30, 3), dtype=object)

    def get_question(self):
        qclass = self.get_question_class()
        self.qno += 1
        self.question = qclass(self.difficulty.name, self.used_qs)
        # Save the correct answers
        self.answers[self.qno, 1] = '/'.join(self.question.answers)

        # Save which question has been given to prevent repetition
        if self.question.name not in ['gapped text', 'multiple match']:
            if self.used_qs.get(self.question.csv_path, None) is not None:
                self.used_qs[self.question.csv_path].append(self.question.lineno)
            else:
                self.used_qs[self.question.csv_path] = [self.question.lineno]
        else:
            if self.used_qs.get(self.question.csv_path, None) is not None:
                self.used_qs[self.question.csv_path].append((self.question.block, self.question.qnumber))
            else:
                self.used_qs[self.question.csv_path] = [(self.question.block, self.question.qnumber)]

    def get_difficulty(self):
        return None

    def get_question_class(self):
        randnum = random.randint(0, len(self.difficulty)-1)
        keys = list(self.difficulty.keys())

        while keys[randnum] == self.qtypes[self.qno]:
            randnum = random.randint(0, len(self.difficulty) - 1)

        self.qtypes[self.qno+1] = keys[randnum]
        return self.difficulty[keys[randnum]]

    def check_answer(self):
        self.answers[self.qno, 2] = self.question.check_answer(self.answers[self.qno, 0])


class Question(ABC):
    name = ''

    def __init__(self, difficulty: str, used_qs):
        self.lineno = 0

        self.answers = []
        self.image = ''
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

        self.select_question(csv_file, file_length, used_qs, difficulty)

    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, *args):
        pass

    @abstractmethod
    def check_answer(self, submitted_answer):
        pass


class LineQuestion(Question, ABC):
    def select_question(self, csv_file, file_length, used_qs, *args):
        for __ in range(file_length * 5):
            self.lineno = random.randint(0, file_length - 1)
            if self.lineno not in used_qs.get(self.csv_path, []):
                break

    @abstractmethod
    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class BlockQuestion(Question, ABC):
    block_length = 0
    question_location = 0

    def select_question(self, csv_file, file_length, used_qs, *args):
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
                    return

    @abstractmethod
    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class MultipleChoiceQuestion(Question, ABC):
    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

    def check_answer(self, submitted_answer):
        if submitted_answer == self.answers[0]:
            return 1
        else:
            return 0


class OpenAnswerQuestion(Question, ABC):
    @abstractmethod
    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

    def check_answer(self, submitted_answer):
        for correct_answer in self.answers:
            if submitted_answer.strip().lower() == correct_answer.strip().lower():
                return 1
        else:
            return 0


class GappedText(MultipleChoiceQuestion, BlockQuestion):
    name = 'gapped text'
    instruction = 'Several sentences/paragraphs have been removed from the text below. Choose the option that has been' \
                  ' removed from gap number <b>'
    block_length = 3
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

        self.title = csv_file[self.block * self.block_length][0]
        self.subtitle = csv_file[self.block * self.block_length][1]
        self.text = csv_file[self.block * self.block_length][2]

        self.answers = list(csv_file[self.block * self.block_length + 1][self.qnumber])
        self.options = csv_file[self.block * self.block_length + 2]

        letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.titles = [letters[i] for i, __ in enumerate(csv_file[self.block * self.block_length + 2])]

        # Add the number of the gap that should be filled into instructions
        self.instruction = ''.join([self.instruction, str(self.qnumber + 1)])

        # Replace the gaps that have been answered previously with the correct answer
        for (block, qnumber) in used_qs.get(self.csv_path, []):
            correct_answer = letters.find(csv_file[block * self.block_length + 1][qnumber])
            answer_text = self.options[correct_answer]
            self.text = self.text.replace(''.join(['(', str(correct_answer), ') ..........']), answer_text)

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class KeyWordTransformations(LineQuestion):
    name = 'key word transformations'
    instruction = 'Complete the second sentence so that it has a similar meaning to the first sentence, using the ' \
                  'word given. <b>Do not change the word given<b>. You must use between <b>two<b> and <b>five<b> ' \
                  'words, including the word given.'

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

        self.difficulty = args[0]
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

        # Score the submitted answer against each possibple correct answer
        for answer_number, correct_answer in enumerate(self.answers):
            halves = correct_answer.split('|')
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


class MultipleChoice(LineQuestion, MultipleChoiceQuestion):
    name = 'multiple choice'
    instruction = 'Read the text below, then answer the question about the text.'

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

        line = csv_file[self.lineno]
        self.title = line[0]
        self.subtitle = line[1]
        self.text = line[2]
        self.answers = list(line[3])
        self.question = line[4]
        self.options = line[5:]

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class MultipleMatch(MultipleChoiceQuestion, BlockQuestion):
    name = 'multiple match'
    block_length = 4
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

        self.instruction = csv_file[self.block*4][0]
        self.question = self.questions[self.qnumber]
        self.answers = list(csv_file[self.block*4+3][self.qnumber])
        self.options = csv_file[self.block*4+2][1::2]

        if csv_file[self.block*4+2][0]:
            self.titles = csv_file[self.block*4+2][::2]
        else:
            letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            self.titles = [letters[i] for i, __ in enumerate(csv_file[self.block*4+2][::2])]

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class MultipleChoiceCloze(LineQuestion, MultipleChoiceQuestion):
    name = 'multiple-choice cloze'
    instruction = 'Select which word fits best into the gap. There is exactly 1 correct answer.'

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

        line = csv_file[self.lineno]
        self.question = line[0]
        self.answers = list(line[1])
        self.options = line[2:]

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class OpenCloze(LineQuestion, OpenAnswerQuestion):
    name = 'open cloze'
    instruction = 'Write the missing word (only 1) into the field below. Take care with spelling. There' \
                  ' may be multiple correct answers, but only enter one.'

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)

        line = csv_file[self.lineno]
        self.question = line[0]
        self.answers = line[1:]

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class ReadPicture(LineQuestion, MultipleChoiceQuestion):
    name = 'read picture'
    instruction = 'For the question below, choose the correct answer.'

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)
        line = csv_file[self.lineno]

        self.answers = list(line[0])
        self.question = line[1]
        self.options = line[2:]
        self.image = os.path.join(os.path.split(self.csv_path)[0], ''.join([self.name, str(self.lineno), '.png']))

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class WordFormation(LineQuestion, OpenAnswerQuestion):
    name = 'word formation'
    instruction = 'Modify the given stem word so that it fits into the gap in the sentence.'

    def select_question(self, csv_file, file_length, used_qs, *args):
        super().select_question(csv_file, file_length, used_qs)
        line = csv_file[self.lineno]

        self.question = line[0]
        self.title = line[1]
        self.answers = line[2:]

    def check_answer(self, submitted_answer):
        return super().check_answer(submitted_answer)


class NamedDict(dict):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)


temp = NamedDict('B2', [('word formation', WordFormation), ('key word transformations', KeyWordTransformations)])
A2 = NamedDict('A2', [('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                      ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                      ('read picture', ReadPicture)])
B1 = NamedDict('B1', [('gapped text', GappedText), ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                      ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                      ('read picture', ReadPicture)])
B2 = NamedDict('B2', [('gapped text', GappedText), ('key word transformations', KeyWordTransformations),
                      ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                      ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                      ('word formation', WordFormation)])
