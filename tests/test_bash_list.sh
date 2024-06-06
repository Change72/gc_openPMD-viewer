# Check if a command-line argument is provided
if [ $# -eq 0 ]; then
    test_type="1,2,3,4,5,6,7,8,9,10,11"
else
    test_type=$1
fi

# Convert the comma-separated string to an array
IFS=',' read -ra test_type_array <<< "$test_type"

# Loop through each element of the test_type array
for j in "${test_type_array[@]}"; do
    echo "$j"
done