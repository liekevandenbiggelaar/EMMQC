# Code base for: Itemset Refinements for Exceptional Model Mining (2027)


This repository contains the implementation of the methods introduced in the paper "Efficient Mining of Collection-Based Attributes in Strongly Hierarchical Mixed-Type Data: Itemset Refinements for Exceptional Model Mining", to appear at KDD 2027.
**Formal citation:** Lieke van den Biggelaar, Rianne M. Schouten, Ivo van Heck, Martijn Slob, and Wouter Duivesteijn. 2027. Efficient Mining of Collection-Based Attributes in Strongly Hierarchical Mixed-Type Data: Itemset Refinements for Exceptional Model Mining. In Proceedings of the 33rd ACM SIGKDD Conference on Knowledge Discovery and Data Mining V.1 (KDD ’27), August 01–05, 2027, San Jose, CA, USA. ACM, New York, NY, USA, 12 pages. https://doi.org/10.1145/3862868.3871315

There are three folders:
- data: contains the .csv file with the data made available by Algebrakit (Eindhoven, the Netherlands), our collaborating company.
- eqc: contains the actual code, all in python.
- synthetic: contains the code for the synthetic experiments in Section 6.

There are four files:
- real-world experiment : contains the experimental setup used for the real-world experiment mentioned in the paper.
- synthetic experiment: contains the experimental setup used for the synthetic experiments in the paper.
- non-hierarchical study: contains an execution of the real-world experiment with the alternative to our proposed itemset refinement: one-hot encoding all collection-based attributes into binary attributes.
- figures: recreate the figures from the synthetic experiments from the results.

The reposity can be downloaded using:
```
$ git clone https://github.com/yourusername/EMMQC.git
$ cd EMMQC
```

## Synthetic Experiments
To reproduce the synthetic data experiments, clone the reposity and run the following line in the terminal:
```
python syntheticexperiments.py
```
Two experiments can be executed by (un)commenting relevant selections in the __main__ file. 

## Real-world Experiment
To reproduce the results from the real-world experiment, clone the reposity and run the following line in the terminal:
```
python casestudy.py
```
The experimental setup can be altered within this file by simply adjusting the values in the lists and dictionaries as desired.

Feel free to contact me if things are unclear or if you have any questions.

Kind regards,

Lieke van den Biggelaar

