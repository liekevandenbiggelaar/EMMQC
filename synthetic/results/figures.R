library(ggplot2)
library(readxl)
library(tidyverse)
library(RColorBrewer)
library(mice)
library(xtable)

setwd("C:/Users/20200059/OneDrive - TU Eindhoven/Documents/Github/EMMQC/synthetic/results/")

#### Simulation results ####

#### Experiment 1 ####
data <- read_excel("Exp1[[1000], [20], [0.3, 0.5, 0.7], [0.4, 0.6, 0.8], [0.4, 0.6, 0.8], [0], [0], [False], [False], [False], [3], [1], [0], [0], [0]].xlsx")
head(data)

?str_detect

plotdata <- data %>% 
  filter(subgroup == 1) %>%
  rename(precision_new = precision...18) %>%
  rename(precision = precision...5) %>%
  mutate(found_truth = if_else(
    grepl("A2 is 1", desc, fixed = TRUE), 
    'Found', if_else(
      grepl("A1 is 1", desc, fixed = TRUE), 
      'Found', if_else(
        grepl("A1 is 0", desc, fixed = TRUE), 
        'Found', if_else(
          grepl("A2 is 0", desc, fixed = TRUE), 
          'Found', 'Not found'))))) %>%
  mutate(F1 = round(F1,1))

plot <- plotdata %>% ggplot(aes(x=precision, y=recall)) + 
  geom_point(aes(colour=as.factor(p), 
                 shape=as.factor(pop_fail_rate),
                 alpha=as.factor(found_truth),
                 size=F1)) + 
  geom_line(aes(group=interaction(p,pop_fail_rate),
                colour=as.factor(p))) + 
  scale_alpha_manual(name="Found truth?", values=c(0.8,0.2)) + 
  scale_colour_manual(name="SG size", values=c("#1f78b4","#d95f02","#66a61e")) + 
  scale_shape_manual(name="Class fail rate", values=c(15,16,17)) + 
  guides(alpha = guide_legend(order = 1)) + 
  theme_bw(base_size=7) + 
  theme(panel.grid.major.x = element_blank(),
        panel.grid.minor.x = element_blank(),
        panel.grid.major.y = element_blank(),
        axis.text.x=element_text(size=7),
        axis.text.y=element_text(size=7),
        legend.text  = element_text(size=5))

plot
name <- paste('./exp1plot.pdf', sep = "", collapse = NULL)
ggsave(name, width = 16, height = 12, units = "cm")

#### Experiment 2 ####
data <- read_excel("Exp2.xlsx")
head(data)

plotdata <- data %>% 
  mutate(desc = str_sub(desc, start=14L)) %>%
  filter(subgroup == 1) %>%
  rename(precision_new = precision...19) %>%
  rename(precision = precision...5) %>%
  rename(apply_weighted = weighted) %>%
  arrange(include_e1,apply_averaging,apply_weighted,nr_exercises) %>%
  #filter(include_e1 == TRUE) %>%
  mutate(Aggr = if_else(apply_averaging == TRUE, 'Avg', 'Sum')) %>%
  mutate(Weight = if_else(apply_weighted == TRUE, 'Yes', 'No')) %>% 
  rename(Recall = found_recall) %>% 
  rename('F1 Scores' = found_fscore) %>% 
  rename(Quality = quality) %>% 
  rename(Description = desc) %>% 
  mutate(Incl.e1 = fct_recode(as.factor(include_e1), 'Yes' = 'TRUE', 'No' = 'FALSE')) %>%
  rename(Weights = goodness_weights) %>% 
  rename('NrFoundClasses' = exercise_count) %>% 
  rename('NrFoundRecords' = session_count) %>% 
  mutate(NrClasses = as.integer(nr_exercises))

plotdata %>%
  filter(p %in% c(0.7)) %>%
  filter(nr_exercises %in% c(5)) %>%
  select(c(Incl.e1,Aggr,Weight,NrClasses,Description,Quality,Recall)) %>%
  xtable()

# another table for appendix

#### Experiment 3 ####
data <- read_excel("Exp3.xlsx")
head(data)

plotdata <- data %>% 
  filter(subgroup == 1) %>%
  rename(precision_new = precision...19) %>%
  rename(precision = precision...5) %>%
  #mutate(nr_item_descriptors=nr_item_descriptors-1) %>%
  rename(NrCollAttr = nr_item_descriptors) %>%
  filter(!(find_itemsets == 'OneHotEncoding' & apply_closed_itemsets == TRUE)) %>%
  mutate(find_itemsets = ordered(factor(find_itemsets), 
                                 levels = c('OneHotEncoding', 'RebuildFPTree', 'OneFPTree'))) %>%
  mutate(find_itemsets = fct_recode(find_itemsets, 'OneFPTree (Ours)' = 'OneFPTree')) %>%
  #mutate(OurMethod = if_else(find_itemsets == 'OneFPTree' & apply_closed_itemsets == TRUE, 'Ours', 'Other')) %>%
  rename(Refinement = find_itemsets)

plot <- plotdata %>% filter(max_length == 5) %>%
  ggplot() + 
  geom_boxplot(aes(y=runtime,x=as.factor(NrCollAttr),
               fill=apply_closed_itemsets),
           outlier_shape=NA,
           position=position_dodge(preserve = "single")) + 
  facet_grid(. ~ Refinement, labeller = label_both) + 
  scale_fill_manual(name="Closed itemsets?", values=c("#1f78b4","#66a61e")) + 
  #scale_alpha_manual(name="", values=c(0.3,0.8)) + 
  theme_bw(base_size=7) + 
  xlab('Number of collection attributes') + 
  ylab('Runtime in seconds') +
  guides(alpha=FALSE) + 
  theme(legend.position="top",
        legend.justification="right",
        legend.box.margin = margin(0,0,0,0, "line"),
        panel.grid.major.x = element_blank(),
        panel.grid.minor.x = element_blank(),
        panel.grid.major.y = element_blank(),
        axis.text.x=element_text(size=7),
        axis.text.y=element_text(size=7),
        legend.text  = element_text(size=5))

plot
name <- paste('./exp3plot.pdf', sep = "", collapse = NULL)
ggsave(name, width = 16, height = 8, units = "cm")
