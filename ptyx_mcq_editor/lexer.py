import re

from PyQt6.Qsci import QsciLexerCustom
from PyQt6.QtGui import QColor, QFont


class MyLexer(QsciLexerCustom):
    def __init__(self, parent):
        super(MyLexer, self).__init__(parent)
        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))
        self.setDefaultFont(QFont("Consolas", 14))

        # Initialize colors per style
        # ----------------------------
        self.setColor(QColor("#ff000000"), 0)   # Style 0: black
        self.setColor(QColor("#ff7f0000"), 1)   # Style 1: red
        self.setColor(QColor("#ff0000bf"), 2)   # Style 2: blue
        self.setColor(QColor("#ff007f00"), 3)   # Style 3: green

        # Initialize paper colors per style
        # ----------------------------------
        self.setPaper(QColor("#ffffffff"), 0)   # Style 0: white
        self.setPaper(QColor("#ffffffff"), 1)   # Style 1: white
        self.setPaper(QColor("#ffffffff"), 2)   # Style 2: white
        self.setPaper(QColor("#ffffffff"), 3)   # Style 3: white

        # Initialize fonts per style
        # ---------------------------
        self.setFont(QFont("Consolas", 14, weight=QFont.Weight.Bold), 0)   # Style 0: Consolas 14pt
        self.setFont(QFont("Consolas", 14, weight=QFont.Weight.Bold), 1)   # Style 1: Consolas 14pt
        self.setFont(QFont("Consolas", 14, weight=QFont.Weight.Bold), 2)   # Style 2: Consolas 14pt
        self.setFont(QFont("Consolas", 14, weight=QFont.Weight.Bold), 3)   # Style 3: Consolas 14pt

    def language(self):
        return "SimpleLanguage"

    def description(self, style):
        if style == 0:
            return "myStyle_0"
        elif style == 1:
            return "myStyle_1"
        elif style == 2:
            return "myStyle_2"
        elif style == 3:
            return "myStyle_3"
        ###
        return ""

    def styleText(self, start, end):
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        # 2. Slice out a part from the text
        # ----------------------------------
        text = self.parent().text()[start:end]

        # 3. Tokenize the text
        # ---------------------
        p = re.compile(r"[*]\/|\/[*]|\s+|\w+|\W")

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list = [(token, len(bytearray(token, "utf-8"))) for token in p.findall(text)]

        # 4. Style the text
        # ------------------
        # 4.1 Check if multiline comment
        multiline_comm_flag = False
        editor = self.parent()
        if start > 0:
            previous_style_nr = editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1)
            if previous_style_nr == 3:
                multiline_comm_flag = True
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            if multiline_comm_flag:
                self.setStyling(token[1], 3)
                if token[0] == "*/":
                    multiline_comm_flag = False
            else:
                if token[0] in ["for", "while", "return", "int", "include"]:
                    # Red style
                    self.setStyling(token[1], 1)
                elif token[0] in ["(", ")", "{", "}", "[", "]", "#"]:
                    # Blue style
                    self.setStyling(token[1], 2)
                elif token[0] == "/*":
                    multiline_comm_flag = True
                    self.setStyling(token[1], 3)
                else:
                    # Default style
                    self.setStyling(token[1], 0)

