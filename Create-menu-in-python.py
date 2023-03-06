# Create menu in python

balance = 0
amount = 0
choice = ""

while True:
    print("1) Deposit")
    print("2) Withdraw")
    print("3) Print Balance")
    print("4) Quit")

choice = input ("Enter Choice: ")

# Strip will remove any white spaces before and after the choice selection.
choice = choice.strip()

if (choice == "1"):
    amount = float(input("Enter Amount: "))
    balance += amount
elif (choice == "2"):
    amount = float (input("Enter Amount: "))
    balance -= amount
elif (choice == "3"):
    print("Balance:", balance)
elif (choice == "4"):
    break
else:
    print("Invalid Option. Please Try Again. ")