# Cambridge English CAT

This project is a software for determining a person's English language level. To achieve the best results, [Computerized Adaptive Testing](https://en.wikipedia.org/wiki/Computerized_adaptive_testing) (CAT) would be the best solution, but setting this up requires too many resources. Therefore, this software approximates the behaviour of a true CAT by altering the difficulty of questions using Cambridge English Exam questions, which shouldbe of roughly the same difficulty within one level (eg. C2).

## Structure

Currently, there are three parts to this software. 

- The Data folder contains all the questions inside CSV files so that they can be read by computer. More detail on this part is in CONTRIBUTING.txt file.
- The tester.py file contains the main class, Tester, which handles the entire exam. It also contains parsers for the various question types which read the CSV files.
- The gui.py contains the code for the Graphical User Interface (GUI), written using wxpython. It handles the user interaction, and so this file should be run to run the software (python gui.py).