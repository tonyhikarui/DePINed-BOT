import json
import os

def convert_accounts_to_json():
    accounts = []
    
    try:
        if not os.path.exists('accounts.txt'):
            print("accounts.txt not found in current directory:", os.getcwd())
            return
            
        with open('accounts.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    email, password = line.split('|')
                    account = {
                        "Email": email.strip(),
                        "Password": password.strip()
                    }
                    accounts.append(account)
                except ValueError:
                    print(f"Skipping invalid line: {line}")
                    
        if not accounts:
            print("No valid accounts found!")
            return
            
        with open('accounts.json', 'w') as f:
            json.dump(accounts, f, indent=4)
            
        print(f"\nSuccessfully converted {len(accounts)} accounts to accounts.json")
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")

if __name__ == "__main__":
    print("Starting conversion...")
    convert_accounts_to_json()
