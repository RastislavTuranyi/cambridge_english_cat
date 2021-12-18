from abc import ABC, abstractmethod
import csv
import os
import random

import numpy as np


class Tester:
    def __init__(self):
        self.difficulty = B1
        self.qno = -1
        self.difficulties = ['B1']
        self.qtypes = np.zeros(30, dtype=object)
        self.used_qs = {}
        self.answers = np.zeros((30, 3), dtype=object)

    def get_question(self):
        qclass = self.get_question_class()
        self.qno += 1
        self.question = qclass(self.difficulty.name, self.used_qs, self.qno)
        # Save the correct answers
        self.answers[self.qno, 1] = '/'.join(self.question.answers)

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

        self.change_difficulty()

    def change_difficulty(self):
        if self.qno < 4:
            level_names = list(levels.keys())
            previous_level_index = level_names.index(self.difficulties[self.qno])

            if self.answers[self.qno, 2] == 0:
                new_level_index = previous_level_index - 1
            else:
                new_level_index = previous_level_index + 1

            self.difficulty = levels[level_names[new_level_index]]

        if self.qno == 4:


        self.difficulties.append(self.difficulty.name)


    def get_question_class(self):
        randnum = random.randint(0, len(self.difficulty)-1)
        keys = list(self.difficulty.keys())

        # Keep choosing random question type until it is different from the previous question
        while keys[randnum] == self.qtypes[self.qno]:
            randnum = random.randint(0, len(self.difficulty) - 1)

        self.qtypes[self.qno+1] = keys[randnum]
        return self.difficulty[keys[randnum]]

    def check_answer(self):
        self.answers[self.qno, 2] = self.question.check_answer(self.answers[self.qno, 0])


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
                    self.title = csv_file[self.block * self.block_length][0]
                    self.subtitle = csv_file[self.block * self.block_length][1]
                    self.text = csv_file[self.block * self.block_length][2].replace(f'({self.qnumber + 1}) ..........',
                                                                                    f'<b>[{kwargs["qno"] + 1}] '
                                                                                    f'..........<b>')
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
                print(csv_file[block * self.block_length + 1], qnumber)
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
    instruction = 'Several sentences/paragraphs have been removed from the text below. Choose which sentence/parahraph' \
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
        for answer_number, correct_answer in enumerate(self.answers.lower()):
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


class MultipleMatch(MultipleChoiceQuestion, BlockQuestion):
    name = 'multiple match'
    block_length = 4
    question_location = 1

    def select_question(self, csv_file, file_length, used_qs, **kwargs):
        super().select_question(csv_file, file_length, used_qs, **kwargs)

        self.instruction = csv_file[self.block*4][0]
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
        print(self.answers)
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

        self.answers = csv_file[self.lineno][0]
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


class NamedDict(dict):
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super().__init__(*args, **kwargs)


A0 = NamedDict('A0', [('gapped text A', GappedTextA), ('questions', Questions), ('read picture', ReadPicture),
                      ('reading comprehension', ReadingComprehension), ('spelling', Spelling)])

A1 = NamedDict('A1', [('gapped text A', GappedTextA), ('matching', Matching), ('multiple choice', MultipleChoiceA1),
                      ('multiple-choice cloze', MultipleChoiceCloze), ('reading', Reading)])

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

C1 = NamedDict('C1', [('gapped text', GappedText), ('key word transformations', KeyWordTransformations),
                      ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                      ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                      ('word formation', WordFormation)])

C2 = NamedDict('C2', [('gapped text', GappedText), ('key word transformations', KeyWordTransformations),
                      ('multiple choice', MultipleChoice), ('multiple match', MultipleMatch),
                      ('multiple-choice cloze', MultipleChoiceCloze), ('open cloze', OpenCloze),
                      ('word formation', WordFormation)])

#levels = {'A0': A0, 'A1': A1, 'A2': A2, 'B1': B1, 'B2': B2, 'C1': C1, 'C2': C2}
