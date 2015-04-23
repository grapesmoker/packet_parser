latex_preamble = r'''
\documentclass[10pt]{article}
\usepackage[top=1in, bottom=1in, left=1in, right=1in]{geometry}
\usepackage{parskip}
\usepackage[]{graphicx}
\usepackage[normalem]{ulem}
\usepackage{ebgaramond}
\usepackage[utf8]{inputenc}

\begin{document}

\newcommand{\ans}[1]{{\sc \uline{#1}}}

\newcommand{\tossups}{\newcounter{TossupCounter} \noindent {\sc Tossups}\\}
\newcommand{\tossup}[2]{\stepcounter{TossupCounter}
    \arabic{TossupCounter}.~#1\\ANSWER: #2\\}

\newcommand{\bonuses}{\newcounter{BonusCounter} \noindent {\sc Bonuses} \\}
% bonus part is points - text - answer
\newcommand{\bonuspart}[3]{[#1]~#2\\ANSWER: #3\\}
% bonus is leadin - parts

\newenvironment{bonus}[1]{\stepcounter{BonusCounter}
    \arabic{BonusCounter}.~#1\\}{}


%\newcommand{\bonus}[2]{\stepcounter{BonusCounter}
%  \arabic{BonusCounter}.~#1\\#2}

\begin{center}
  \includegraphics[scale=1]{acf-logo.pdf}\\
  {\sc 2014 ACF Nationals\\ Packet 1 by The Editors}
\end{center}
'''

latex_end = r'\end{document}'
