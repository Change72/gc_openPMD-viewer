import pandas as pd
import random
import uuid

# select_set = {"x", "y", "z", "ux", "uy", "uz"}
# for i in range(100):
#     expand_set = random.sample(select_set, random.randint(1, len(select_set)))
#     print(expand_set)


csv_file_name = "results/10g_iteration_500/benchmark_result_00001_to_01.csv"


df = pd.read_csv(csv_file_name, header=None, index_col=False,
                names=["target_percentage", "current_percentage", "iteration", "species", "select_set", "expand_set", "envelope"])

df["select_set"] = df["select_set"].apply(lambda x: sorted(list(eval(x))))
# Convert sets to tuples
df["select_set"] = df["select_set"].apply(tuple)

# Group by "target_percentage" and "select_set", then print length of each group
grouped_df = df.groupby(["target_percentage", "select_set"]).size().reset_index(name="group_length")
print(grouped_df)




# we can use the column "envelope" to check if there are duplicated rows
df['is_duplicate'] = df.duplicated(subset=["envelope"], keep=False)
# Filter the DataFrame to show only the duplicated rows
duplicated_rows = df[df['is_duplicate']]

# Print the duplicated rows
print("Duplicated Rows:")
print(duplicated_rows)

print()