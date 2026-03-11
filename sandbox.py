string_input = "237,537,717,580,674,100,194,442,743,1086,991,31,305,648,1017,786,511,331,1060,400,811,923,606,168,57,854,468,262,880,374,948,125"

# sort the numbers in the string
def sort_numbers(input_string):
    numbers = list(map(int, input_string.split(',')))
    numbers.sort()
    return ','.join(map(str, numbers))

# create strings that are copies of the original string but add or subtract n from each number
def modify_numbers(input_string, n):
    offset = 0
    numbers = list(map(int, input_string.split(',')))
    modified_numbers = []
    for num in numbers:
        modified_number = num + n + offset
        modified_numbers.append(str(modified_number))
        offset += 0  # increment offset for each number
    return ','.join(modified_numbers)

string_input = sort_numbers(string_input)
start_frames = modify_numbers(string_input, 0)
transition_frames = modify_numbers(string_input, 5)
end_frames = modify_numbers(string_input, 10)
print("Start Frames:", start_frames)
print("Transition Frames:", transition_frames)
print("End Frames:", end_frames)