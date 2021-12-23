from abc import abstractmethod

import wx
import wx.richtext as rt

from tester import Tester, TestEndError, LowCertaintyError, InconsistentResultsError, MultipleChoiceQuestion


class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, size=(1000, 600),  title='Cambridge English placement test')
        self.main_panel = wx.Panel(self)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        # TODO: play with boxsizers and gridsizers to perfect the layout
        # Create first question
        self.tester = Tester()
        self.tester.get_question()

        self.build_panel()

        self.main_panel.SetSizer(self.main_sizer)

        self.Centre()
        self.Show()

    def build_panel(self):
        # Create sizer for the panel
        self.sizer = wx.FlexGridSizer(cols=1, rows=2, vgap=5, hgap=5)

        print(self.tester.difficulty.name, self.tester.qno % 5, self.tester.scores)

        if isinstance(self.tester.question, MultipleChoiceQuestion):
            if len(self.tester.question.options) > 4:
                self.button_sizer = wx.FlexGridSizer(cols=3, rows=4, vgap=5, hgap=5)
            else:
                self.button_sizer = wx.FlexGridSizer(cols=2, rows=4, vgap=5, hgap=5)
        else:
            self.button_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create an instance of a panel class depending on question type
        self.panel = panel_classes[self.tester.question.name](self.main_panel, self)

        self.main_sizer.Add(self.panel, 0, wx.EXPAND|wx.ALL)

        # Add button to submit question
        self.submit = wx.Button(self.panel, label='Submit')
        self.submit.Bind(wx.EVT_BUTTON, self.on_next)

        # Allow ENTER key to be able to be used to submit questions
        if self.panel.hook == 'multiple':
            self.Bind(wx.EVT_CHAR_HOOK, self.on_next_enter)
        elif self.panel.hook == 'open':
            self.Bind(wx.EVT_TEXT_ENTER, self.on_next)

        self.button_sizer.Add(self.submit, 0, wx.ALIGN_RIGHT)
        self.sizer.Add(self.button_sizer, 1, wx.EXPAND)

        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableRow(0, 1)

        self.panel.SetSizer(self.sizer)
        self.panel.Layout()
        self.main_panel.Layout()

    def new_question(self):
        self.destroy_panel()

        if self.panel.hook == 'multiple':
            self.Unbind(wx.EVT_CHAR_HOOK)
        elif self.panel.hook == 'open':
            self.Unbind(wx.EVT_TEXT_ENTER)

        # Build a new panel
        self.build_panel()

    def destroy_panel(self):
        # Destroy the panel containing the old question
        for child in self.panel.GetChildren():
            child.Destroy()

        try:
            self.panel.Destroy()
        except RuntimeError:  # Ignore if the panel has been destroyed already
            pass

    def on_next(self, event):
        self.tester.submitted_answers.append(self.panel.get_answer())
        self.tester.check_answer()
        #print(self.tester.submitted_answers[:5])
        # Normally, get new question and display it
        try:
            self.tester.get_question()
            self.new_question()

        # If the test should end, evaluate the results and try to show them
        except TestEndError:
            try:
                self.tester.evaluate()
                self.on_show_results(event)
            except InconsistentResultsError as e:
                popup = ConfirmationPopupWindow(self, 'End exam despite inconsistent results?', self.tester,
                                                e.blurb, e.extra_questions, e.difficulty)
            except LowCertaintyError as e:
                popup = ConfirmationPopupWindow(self, 'End exam despite the result having low certainty?', self.tester,
                                                e.blurb, e.extra_questions, e.difficulty)

    def on_next_enter(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.on_next(event)

    def on_continue_test(self, extra_questions, difficulty):
        self.tester.extra_questions += extra_questions
        self.tester.difficulty = difficulty
        self.tester.difficulties.append(difficulty.index)
        self.tester.skip_evaluate = True

        self.tester.get_question()
        self.new_question()

    def on_show_results(self, event):
        self.destroy_panel()

        self.sizer = wx.FlexGridSizer(cols=1, rows=2, vgap=5, hgap=5)
        self.panel = ResultsPanel(self.main_panel, self)
        self.main_sizer.Add(self.panel, 0, wx.EXPAND | wx.ALL)

        self.panel.SetSizerAndFit(self.sizer)
        self.panel.Layout()
        self.main_panel.Layout()


class TemplatePanel(wx.Panel):
    hook = ''

    def __init__(self, parent, frame):
        super().__init__(parent)
        self.frame = frame
        self.question = rt.RichTextCtrl(self, style=rt.RE_MULTILINE | rt.RE_READONLY | wx.BORDER_NONE)

        self.question.Freeze()
        self.add_instruction()
        self.question.Thaw()

        frame.sizer.Add(self.question, 1, wx.ALL | wx.EXPAND)

    def add_instruction(self):
        """
        Writes the instructions for a given question. Uses <b> tags inside the question.instruction attribute to
        highlight specific words.

        :return: None
        """
        instructions = '. '.join([str(self.frame.tester.qno), self.frame.tester.question.instruction]).split('<b>')

        # Alternating, write with normal and bold fonts since that is how the instruction is split up at <b>
        self.write_alternating_bold(instructions, wx.FONTWEIGHT_SEMIBOLD)

        self.question.Newline()
        self.question.Newline()
        self.question.Newline()

    def write_alternating_bold(self, divided_text: list, default_bold_level):
        for index, part in enumerate(divided_text):
            if index % 2 == 0:
                self.question.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, default_bold_level))
            else:
                self.question.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            self.question.WriteText(part)
            self.question.EndFont()

    def write_section(self, font: wx.Font, text: str):
        self.question.BeginFont(font)
        self.question.WriteText(text)
        self.question.EndFont()
        self.question.Newline()

    def add_image(self):
        """
        Add an image to the richtext field that holds the question. Should only be used for questions wich implement
        images.
        :return:  None
        """
        self.question.WriteImage(self.frame.tester.question.image, wx.BITMAP_TYPE_PNG)

    def add_options(self):
        """
        Add options into the richtext field that holds the question. These consist of multiple texts, each with a
        title. If a titles do not come with the texts, capital alphabet should be used - ie. A, B, C, etc.
        :return: None
        """
        for title, option in zip(self.frame.tester.question.titles, self.frame.tester.question.options):
            self.question.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            self.question.WriteText(title)
            self.question.EndFont()
            self.question.Newline()

            self.question.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            self.question.WriteText(option)
            self.question.EndFont()
            self.add_newlines()

    def add_question(self):
        self.write_section(wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD),
                           self.frame.tester.question.question)

    def add_text(self):
        # If there is a title, show it
        if self.frame.tester.question.title:

            self.question.BeginAlignment(wx.TEXT_ALIGNMENT_CENTRE)
            self.write_section(wx.Font(16, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
                               self.frame.tester.question.title)
            self.question.EndAlignment()
            self.question.Newline()

        # If there is a subtitle, show it
        if self.frame.tester.question.subtitle:
            self.question.BeginAlignment(wx.TEXT_ALIGNMENT_CENTRE)
            self.write_section(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL),
                               self.frame.tester.question.subtitle)
            self.question.EndAlignment()
            self.question.Newline()

        # Show the text
        self.question.BeginAlignment(wx.TEXT_ALIGNMENT_JUSTIFIED)
        self.question.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        first = True
        for paragraph in self.frame.tester.question.text.split(r'\n'):
            if first:
                first = False
            else:
                self.question.Newline()

            if '<b>' in paragraph:
                parts = paragraph.split('<b>')
                self.write_alternating_bold(parts, wx.FONTWEIGHT_NORMAL)
            else:
                self.question.WriteText(paragraph)
        self.question.EndFont()
        self.question.EndAlignment()

    def add_newlines(self):
        """
        Adds 2 new lines, equivalent to 2 <br>s or 2 /n s. Effectively creates a line of space between paragraphs.
        :return: None
        """
        self.question.Newline()
        self.question.Newline()


class OpenAnswerPanel(TemplatePanel):
    hook = 'open'

    def __init__(self, parent, frame):
        super().__init__(parent, frame)

        self.build_question()
        self.question.Caret.Hide()

        # Add answer options
        self.answer = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        frame.button_sizer.Add(self.answer, 0, wx.ALL | wx.EXPAND)

    @abstractmethod
    def build_question(self):
        pass

    def get_answer(self):
        return self.answer.GetValue()


class KeyWordTransformationsPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_text()
        self.add_newlines()

        self.write_section(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
                           self.frame.tester.question.keyword)

        self.add_newlines()
        self.add_question()


class MatchingPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_image()
        self.add_newlines()
        self.add_question()


class OpenClozePanel(OpenAnswerPanel):
    def build_question(self):
        self.add_text()


class QuestionsPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_image()
        self.add_newlines()
        self.add_question()
        self.question.Newline()
        self.write_section(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
                           self.frame.tester.question.text)


class ReadingComprehensionPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_image()
        self.add_newlines()
        self.add_question()


class ReadingPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_text()
        self.add_newlines()
        self.add_question()


class SpellingPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_image()


class WordFormationPanel(OpenAnswerPanel):
    def build_question(self):
        self.add_text()
        self.add_newlines()
        self.write_section(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
                           self.frame.tester.question.keyword)


class MultiplePanel(TemplatePanel):
    hook = 'multiple'

    def __init__(self, parent, frame):
        super().__init__(parent, frame)

        labels = self.build_question()
        self.question.Caret.Hide()

        # Create the first radio button, so that they are a group
        self.radiobuttons = []
        self.radiobuttons.append(wx.RadioButton(self, label=labels[0], style=wx.RB_GROUP))
        frame.button_sizer.Add(self.radiobuttons[0], 0, wx.LEFT)
        # Create the rest of the buttons
        for label in labels[1:]:
            temp = wx.RadioButton(self, label=label)
            self.radiobuttons.append(temp)
            frame.button_sizer.Add(temp, 0, wx.LEFT)

        if len(labels) < 8:
            for i in range(8 - len(labels)):
                frame.button_sizer.Add(wx.StaticText(), 0)

    @abstractmethod
    def build_question(self):
        pass

    def get_answer(self):
        letters = 'ABCDEFGHJKILMNOPQRSTUVWXYZ'
        for i, button in enumerate(self.radiobuttons):
            if button.GetValue():
                return letters[i]


class GappedTextPanel(MultiplePanel):
    def build_question(self):
        self.add_text()
        self.add_newlines()
        self.add_options()
        return self.frame.tester.question.titles


class GappedTextAPanel(MultiplePanel):
    def build_question(self):
        self.add_text()
        self.add_newlines()
        self.add_image()
        return self.frame.tester.question.options


class MultipleChoiceClozePanel(MultiplePanel):
    def build_question(self):
        self.add_text()
        return self.frame.tester.question.options


class MultipleMatchPanel(MultiplePanel):
    def build_question(self):
        self.add_question()
        self.add_newlines()
        self.add_options()
        return self.frame.tester.question.titles


class MultipleChoicePanel(MultiplePanel):
    def build_question(self):
        self.add_text()
        self.add_newlines()
        self.add_question()
        return self.frame.tester.question.options


class ReadPicturePanel(MultiplePanel):
    def build_question(self):
        self.add_image()

        if self.frame.tester.question.question:
            self.add_newlines()
            self.add_question()

        return self.frame.tester.question.options


panel_classes = {'open cloze': OpenClozePanel, 'multiple-choice cloze': MultipleChoiceClozePanel,
                 'multiple choice': MultipleChoicePanel, 'multiple match': MultipleMatchPanel,
                 'read picture': ReadPicturePanel, 'word formation': WordFormationPanel, 'gapped text': GappedTextPanel,
                 'key word transformations': KeyWordTransformationsPanel,
                 'gapped text A': GappedTextAPanel, 'questions': QuestionsPanel,
                 'reading comprehension': ReadingComprehensionPanel, 'spelling': SpellingPanel,
                 'reading': ReadingPanel, 'matching': MatchingPanel}


class ConfirmationPopupWindow(wx.Dialog):
    def __init__(self, parent, title, tester, message, extra_questions, difficulty):
        super().__init__(parent, title=title)
        self.tester = tester
        self.parent = parent
        self.extra_questions = extra_questions
        self.difficulty = difficulty

        self.panel = wx.Panel(self)
        self.sizer = wx.FlexGridSizer(cols=1, rows=2, hgap=5, vgap=5)
        self.button_sizer = wx.GridSizer(cols=2, rows=1, hgap=5, vgap=5)

        self.text = rt.RichTextCtrl(self.panel, style=rt.RE_MULTILINE | rt.RE_READONLY | wx.BORDER_NONE)
        self.text.Freeze()
        self.text.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text.WriteText(message)
        self.text.EndFont()
        self.text.Thaw()
        self.sizer.Add(self.text, 0, wx.ALL | wx.EXPAND)

        self.continue_test = wx.Button(self.panel, label='Continue exam')
        self.Bind(wx.EVT_BUTTON, self.on_continue_test)
        self.button_sizer.Add(self.continue_test, 0, wx.ALIGN_LEFT)

        self.show_results = wx.Button(self.panel, label='Show results')
        self.Bind(wx.EVT_BUTTON, self.on_show_results)
        self.button_sizer.Add(self.show_results, 0, wx.ALIGN_RIGHT)

        self.sizer.Add(self.button_sizer, 1, wx.EXPAND)
        self.sizer.AddGrowableCol(0, 1)
        self.sizer.AddGrowableRow(0, 1)

        self.panel.SetSizer(self.sizer)
        self.Show()

    def on_continue_test(self, event):
        self.parent.on_continue_test(self.extra_questions, self.difficulty)
        self.Close()

    def on_show_results(self, event):
        self.parent.on_show_results(event)
        self.Close()


class ResultsPanel(wx.Panel):
    def __init__(self, parent: wx.Panel, frame: MainWindow):
        super().__init__(parent)

        self.text = rt.RichTextCtrl(self, style=rt.RE_MULTILINE | rt.RE_READONLY | wx.BORDER_NONE)

        self.text.Freeze()
        self.text.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text.WriteText('You have achieved')
        self.text.EndFont()

        self.text.Newline()
        self.text.BeginAlignment(wx.TEXT_ALIGNMENT_CENTRE)
        self.text.BeginFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_EXTRABOLD))
        self.text.WriteText(frame.tester.result)
        self.text.EndFont()
        self.text.EndAlignment()

        self.text.Newline()
        self.text.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text.WriteText('CEFR level. ' + frame.tester.evaluation)
        self.text.EndFont()

        self.text.Newline()
        self.text.Newline()
        self.text.Newline()
        self.text.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.text.WriteText('CEFR level     Grade           Certainty')  # 5; 11
        self.text.EndFont()

        self.text.Newline()
        self.text.BeginFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.text.Newline()
        difficulties = ['pre-A1', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2']
        for (index, grade), certainty in zip(reversed(list(enumerate(frame.tester.grades))),
                                             reversed(frame.tester.certainty)):
            self.text.Newline()
            if grade is None:
                continue
            elif index > 1:
                self.text.WriteText(' '*4 + difficulties[index] + ' '*11 + grade + ' '*7 + certainty[1])
            else:
                self.text.WriteText(' '*2 + difficulties[index] + ' '*8 +
                                    frame.tester.shields[index] + '/5' + ' '*6 + certainty[1])
        self.text.EndFont()

        self.text.Thaw()

        frame.sizer.Add(self.text, 0, wx.ALL | wx.EXPAND)
        frame.sizer.AddGrowableCol(0, 1)
        frame.sizer.AddGrowableRow(0, 1)


if __name__ == '__main__':
    import wx.lib.inspection

    app = wx.App()
    # wx.lib.inspection.InspectionTool().Show()

    frame = MainWindow()
    app.MainLoop()
