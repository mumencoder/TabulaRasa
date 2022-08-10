
import random, string

# https://stackoverflow.com/questions/2030053/how-to-generate-random-strings-in-python
def randomword(length):
   return ''.join(random.choice(string.ascii_letters) for i in range(length))