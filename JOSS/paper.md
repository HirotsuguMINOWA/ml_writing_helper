---
title: 'ML Writing Helper: Tool elucidates writing performance and boosts up writing for scientist and engineer'
tags:
  - LaTeX
  - Markdown
  - HTML
  - Markup Language
  - engineering
  - Python
authors:
  - name: Hirotsugu MINOWA
    orcid: 0000-0003-4513-8989
    # equal-contrib: true
    affiliation: 1
  # - name: Author Without ORCID
  #   equal-contrib: true # (This is how you can denote equal contributions between multiple authors)
  #   affiliation: 2
  # - name: Author with no affiliation
  #   corresponding: true # (This is how to denote the corresponding author)
  #   affiliation: 3
  # - given-names: Ludwig
  #   dropping-particle: van
  #   surname: Beethoven
  #   affiliation: 3
affiliations:
 - name: Okayama Shoka University, Japan
   index: 1
date: 22 March 2024
bibliography: paper.bib

---

# Summary


Writing papers accounts for much of a researcher's work. \LaTeX is a solution as powerful writing tool in writing papers. The advantage of \LaTeX is a powerful sentence template function. The advantage of this writing template function is that it can greatly reduce the time required for layout and appearance of the paper, which is not essential in writing a paper. This advantage is the reason why \LaTeX continues to be used even now that GUI-based word processing software such as Microsoft Word (hereafter, MS-Word) has become the norm.

However, \LaTeX has a weakness that inserting and updating diagrams takes much longer than other GUI based word processors. The author has developed a tool called ML Writing Helper to solve this problem. This tool can automatically convert diagrams created by Microsoft Power Point, which is the most popular software, into .eps or .pdf files that can be inserted into markup language documents such as \LaTeX, Markdown, HTML as soon as they are saved. In addition, the tool can remove the margins (white space in outliner) of the figure by cropping with image processing.

## Main functions
1. This can convert .pptx/.ppt files created by Power Point or LibreOffice into image files such as .pdf, .png, .eps and so on.
2. This can remove outliner white space in the above conversion.
3. This can convert to gray scale image.
4. This can copy files such as .bib file exported from document manager to target folder by detecting their change or export and so on.


# Statement of need

ML Writing Helper is an support tool which is developed under engineering view for author to write paper. This is a general python package and a CUI based  tool.

However, this tool boot up at each terminal application, implemented in linux, macos and windows enables affect all writing in all word processors or editor applications because this tool monitor forlder directly without dependend on application.

I are concerned that it is difficult to explain the scientific principles of this tool in a way that everyone can understand whether or not it contains a scientific principles. This is because I are not using easy-to-understand science such as physics or mathematics. However, I believe that there is a scientific principles that is appropriate for this journal.

The software is a way to alleviate some of the burdensome problems of writing papers in \LaTeX. This is a movement that tries to elucidate the work efficiency improvement by using this software based on simulations. I believe that the software can make the problem of workload for inserting drawings easier to understand. This logic is explained step by step in the following lines.


: Comparison to word processors \label{table:word_processors} 

| Func \textbackslash Product | MS(Microsoft)-Word                              | Other(General) Word Processor                                 | Conventional LaTeX                                  | LaTeX with MLWritingHelper |
| --------------------------- | ----------------------------------------------- | ------------------------------------------------------------- | --------------------------------------------------- | -------------------------- |
| Diagram Insersion           | 4-5:Very Easy and Advanced                      | 3-4:Easy but this is not as advanced as MS-Word               | 1-2: Not easy, GUI editor is not implmented         | 5:Very Easy(Auto)          |
| Remove white space          | 4:Function "Trimming" enabled to perform easily | 1-4: Many does not have the "Trimming" function like MS-Word" | 0: Not implemented                                  | 5: Very Easy(Auto)         |
| Writing Template            | 1: exists but it is weak                        | 1: exists but it is weak                                      | 5: Exists and it is strong                          | 5: Exists and it is strong |
| Table writing function      | 5:Easy via GUI based table writing function     | 3-5: Many has the "Table writing function" like MS-Word       | 1: It is not convienient, especially to large table | 1: Same to left            |


Table \autoref{table:word_processors} shows the ease of each task in \LaTeX and each word processing software. The first value of explanation is subjective score. 5 indicates high score, 1 indicates low score.

What I want to sort out and find in the table \autoref{table:word_processors} are the problems that make \LaTeX and other word processing software inferior, in other words, the problems that make the work less efficient.

As a result, I found that the major problem that makes the score inferior to \LaTeX and other word processing software is the workload of inserting drawings, and this is a major problem. If I could solve this problem, I could improve the efficiency of work with \LaTeX (hypothesis).

Although \LaTeX still has some difficulty of table creation, if you need to write table via \LaTeX table format, there are various sites to help table creation for \LaTeX such as [Table Generatro](https://www.tablesgenerator.com/), [LaTeX Tables Editor](https://www.latex-tables.com/). So, I recognize that the load of the table creation is greatly reduced.

![Task comparison to word processors\label{fig:tasks}](fig_gen/task_comparison_en.png){width=100%}

The results of the comparison, focusing on the insertion of drawings, are shown in \autoref{fig:tasks}． Comparing the workload of Conventional \LaTeX and "\LaTeX with MLWritingHelper" in \autoref{fig:tasks}, you can see that the workload is reduced. GUI based tasks are assumed to take much more time than CUI based tasks.


The author Minowa [@IEICE2024_minowa] revealed the processing performance of each word processors processing for the tasks in \autoref{fig:tasks} when unexpected drawing insertions occur sometimes by an agent based simulation.


In addition to the above reason, the tool inside cropping is informatics-based, and the framework that can assist in the insertion of drawings in \LaTeX is in line with software engineering. It is small but this contains principles that have been developed from scientific discoveries.


# Acknowledgements

This research was funded by publicly subscribed funds from Okayama Shoka University.

# References
