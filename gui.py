from abc import abstractmethod

import wx
import wx.richtext as rt

from tester import Tester


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
        self.Show()

    def build_panel(self):
        # Create sizer for the panel
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        # Create an instance of a panel class depending on question type
        self.panel = panel_classes[self.tester.question.name](self.main_panel, self)
        self.main_sizer.Add(self.panel, 0, wx.EXPAND|wx.ALL)

        # Add button to submit question
        self.submit = wx.Button(self.panel, label='Submit')
        self.submit.Bind(wx.EVT_BUTTON, self.on_next)
        if self.panel.hook == 'multiple':
            self.Bind(wx.EVT_CHAR_HOOK, self.on_next_enter)
        elif self.panel.hook == 'open':
            self.Bind(wx.EVT_TEXT_ENTER, self.on_next)
        self.sizer.Add(self.submit, 0, wx.ALIGN_RIGHT)

        self.panel.SetSizer(self.sizer)
        self.panel.Layout()
        self.main_panel.Layout()

    def new_question(self):
        # Destroy the panel containing the old question
        for child in self.panel.GetChildren():
            child.Destroy()
        self.panel.Destroy()

        if self.panel.hook == 'multiple':
            self.Unbind(wx.EVT_CHAR_HOOK)
        elif self.panel.hook == 'open':
            self.Unbind(wx.EVT_TEXT_ENTER)

        # Build a new panel
        self.build_panel()

    def on_next(self, event):
        self.tester.answers[self.tester.qno, 0] = self.panel.get_answer()
        self.tester.check_answer()
        print(self.tester.answers[:5])
        self.tester.get_question()
        self.new_question()

    def on_next_enter(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.on_next(event)


class TemplatePanel(wx.Panel):
    hook = ''

    def __init__(self, parent, frame):
        super().__init__(parent)
        self.frame = frame
        self.question = rt.RichTextCtrl(self, size=(-1, 350), style=rt.RE_MULTILINE | rt.RE_READONLY | wx.BORDER_NONE)

        self.question.Freeze()
        self.add_instruction()
        self.question.Thaw()

        frame.sizer.Add(self.question, 0, wx.ALL | wx.EXPAND)

    def add_instruction(self):
        """
        Writes the instructions for a given question. Uses <b> tags inside the question.instruction attribute to
        highlight specific words.

        :return: None
        """
        instructions = '. '.join([str(self.frame.tester.qno + 1), self.frame.tester.question.instruction]).split('<b>')

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
        self.write_section(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL),
                           self.frame.tester.question.question)

    def add_text(self):
        # If there is a title, show it
        if self.frame.tester.question.title:

            self.question.BeginAlignment(wx.TEXT_ALIGNMENT_CENTRE)
            self.write_section(wx.Font(16, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD),
                               self.frame.tester.question.title)
            self.question.EndAlignment()
            self.add_newlines()

        # If there is a subtitle, show it
        if self.frame.tester.question.subtitle:
            self.question.BeginAlignment(wx.TEXT_ALIGNMENT_CENTRE)
            self.write_section(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL),
                               self.frame.tester.question.subtitle)
            self.question.EndAlignment()
            self.add_newlines()

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
        frame.sizer.Add(self.answer, 0, wx.ALL | wx.EXPAND)

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
        frame.sizer.Add(self.radiobuttons[0], 0, wx.LEFT)
        # Create the rest of the buttons
        for label in labels[1:]:
            temp = wx.RadioButton(self, label=label)
            self.radiobuttons.append(temp)
            frame.sizer.Add(temp, 0, wx.LEFT)

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
        self.add_text()
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


if __name__ == '__main__':
    import wx.lib.inspection

    app = wx.App()
    #wx.lib.inspection.InspectionTool().Show()

    frame = MainWindow()
    app.MainLoop()
