import secrets
import string

# Define the character set: uppercase letters, lowercase letters, and digits
alphabet = string.ascii_letters + string.digits

# Generate a 10-character random string
random_string = ''.join(secrets.choice(alphabet) for _ in range(10))

print(random_string)