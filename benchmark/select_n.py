import pandas as pd
import random
import argparse

parser = argparse.ArgumentParser(description='Benchmark Select N Script')
parser.add_argument('--benchmark_result', type=str, help='benchmark result csv file path', default="results/10g_iteration_500/benchmark_result_00001_to_01.csv")
parser.add_argument('--select_n', type=int, help='number of queries to select from each group', default=100)
parser.add_argument('--dimension', type=int, help='dimension of the dataset', default=0)
parser.add_argument('--output_folder', type=str, help="output folder path", default="results/10g_iteration_500")

csv_file_name = parser.parse_args().benchmark_result
n = parser.parse_args().select_n
dimension = parser.parse_args().dimension
output_folder = parser.parse_args().output_folder

df = pd.read_csv(csv_file_name, header=None, index_col=False,
                names=["target_percentage", "current_percentage", "iteration", "species", "select_set", "expand_set", "envelope"])

df["select_set"] = df["select_set"].apply(lambda x: sorted(list(eval(x))))
# Convert sets to tuples
df["select_set"] = df["select_set"].apply(tuple)

# Group by "target_percentage" and "select_set", then print length of each group
grouped_df = df.groupby(["target_percentage", "select_set"]).size().reset_index(name="group_length")
print(grouped_df)

# n_final = min(n, each group length)
n_final = min(n, grouped_df["group_length"].min())
print()
print("==============================================================")
print("selecting {} queries from each group".format(n))

# random select n queries from each group
selected_df = df.groupby(["target_percentage", "select_set"]).apply(lambda x: x.sample(n=n_final)).reset_index(drop=True)

if dimension > 0:
    selected_df = selected_df[selected_df["select_set"].apply(lambda x: len(x) == dimension)]

selected_df.to_csv(f"{output_folder}/selected_{n_final}_queries.csv", index=False)

# selected_df # Group by "target_percentage" and "select_set", then print length of each group
selected_grouped_df = selected_df.groupby(["target_percentage", "select_set"]).size().reset_index(name="group_length")
print(selected_grouped_df)
print()