# EMMQC


This repository contains the implementation of the methods introduced in the paper "Efficient Mining of Collection-Based Attributes in Strongly Hierarchical Mixed-Type Data: Itemset Refinements for Exceptional Model Mining", currently under review at KDD2027 - Research Track - First Cycle. 

There are two folders:
- data: contains the .csv file with the data made available by the collaborating company.
- eqc: contains the actual code, all in python.

There are two files:
- casestudy: contains the experimental setup used for the case study mentioned in the paper.
- synthetic: contains the experimental setup used for the synthetic experiments in the paper.

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

## Case Study
To reproduce the results from the case study, clone the reposity and run the following line in the terminal:
```
python casestudy.py
```
The experimental setup can be altered within this file by simply adjusting the values in the lists and dictionaries as desired.

Feel free to contact me if things are unclear or if you have any questions.

Kind regards,


