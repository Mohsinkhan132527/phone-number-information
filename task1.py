user = {}
balance = 0
logged_in = False

while True:
    def menu():
        print('1. Login Account')
        print('2. Amount Deposit')
        print('3. Withdraw')
        print('4. Check Balance')
        print('5. Exit')
        choice = input('Enter the choice: ')
        if choice == '1':
            LoginAccount()
        elif choice == '2':
            AmountDeposit()
        elif choice == '3':
            Withdraw()
        elif choice == '4':
            CheckBalance()
           
        else:
            print('Invalid option ')    

    def LoginAccount():
        global user,logged_in
        username = input("Enter the username: ")
        password = input('Enter the passwaord: ')
        user[username] = password
        logged_in = True
        print ('Is Logged In')
        menu()
    def AmountDeposit():
        global balance
        if not logged_in:
            print('pehle log in karo')
            return
        
        amount = int(input('Enter the Amount to add account: '))
        balance += amount
        print()
        menu()
    def Withdraw():
        global balance
        if not  logged_in:
            print('pehli login karo')
        withdraw = int(input('Enter the withdraw ammount: '))
        if withdraw <= balance:
           balance -= withdraw
           print('withdraw new balance ',balance)
        else:
            print('Not enough balance ')
            
            menu()

    def CheckBalance():
        global balance
        if not  logged_in:
            print('pehli login karo')
        print(balance)
    menu()

    



    



        








