'''
python questions:

### Logic & Basic Operations

1. **The FizzBuzz Classic:** Write a program that prints numbers from 1 to 50. For multiples of 3, print "Fizz" instead of the number. For multiples of 5, print "Buzz". For numbers which are multiples of both, print "FizzBuzz".
2. **Temperature Converter:** Create a function that takes a temperature in Celsius and converts it to Fahrenheit.
3. **Find the Largest:** Given a list of 5 numbers (e.g., `[12, 45, 2, 89, 34]`), write a script to find the largest number without using the built-in `max()` function.
4. **Reverse a String:** Write a function that takes a string (e.g., "Python") and returns it reversed ("nohtyP") without using the `[::-1]` slicing trick.

### Data Structures & Patterns

5. **Remove Duplicates:** Given a list `[1, 2, 2, 3, 4, 4, 4, 5]`, write a script to create a new list with all duplicates removed.
6. **Vowel Counter:** Create a function that takes a string and counts how many vowels (a, e, i, o, u) are in it.
7. **Odd or Even List:** Take a list of integers and return two separate lists: one containing all the even numbers and one containing all the odd numbers.
8. **Dictionary Lookup:** Create a dictionary of 5 items and their prices. Write a script that allows a user to input an item name and returns the price, or a "Not Found" message if it doesn't exist.

### AI-Adjacent Logic

9. **List Normalization:** Given a list of numbers, write a function that "normalizes" them—meaning it divides every number in the list by the sum of all numbers in that list.
10. **Factorial Calculation:** Write a function to calculate the factorial of a number (e.g., ) using a `while` loop.


SOLUTIONS:

# 1. The FizzBuzz Classic: Write a program that prints numbers from 1 to 50. For multiples of 3, print "Fizz" instead
# of the number. For multiples of 5, print "Buzz". For numbers which are multiples of both, print "FizzBuzz".

while True:

    x = int(input('enter the number bw 1 and 50: '))
    if 1 <= x <=50:
        break
    else:
        print('enter valid number')

if x%3==0 and x%5==0:
    print('fizzbuzz')
elif x%5==0:
    print('buzz')
elif x%3==0:
    print('fizz')
else:
    print(x)

'''