# Simple Password Manager

This is a simple python script that securely manages your passwords offline. Simply remember a main password that decrypts the rest of the passwords. This tool can be set up with a command line alias to quickly retrieve your passwords through a terminal.

This tool makes it easy to access your passwords securely from a command line, and also lets you quickly generate new passwords or set comments to remember the additional information about your accounts.

## Setup Instructions

1. Clone the git repository
2. `pip install -r requirements.txt`
3. Run the `install` script, which will require sudo to set the `pw` command up. It is important that the generated file is owned by root so that it is unwriteable.

A salt will automatically be generated in the `salt` file, and the encrypted data will be stored in `pwstore`. No decrypted password data is ever written to the disk.

It's useful to make a backup of the generated `salt` file, and occasional backups of the `pwstore` file. These are not currently created automatically.

## Command list:

| Command | Description |
| - | - |
| get \<name\> | Copies the password for this site name to the clipboard |
| print \<name\> | Prints the password for this site to stdout |
| set \<name\> \<password\> | Updates the password for a site name |
| comment \<name\> \<new comment\> | Sets the comment for a site name, useful for any additional info to store |
| acomment \<name\> \<append\> | Appends to the existing comment for a site name
| rename \<old name\> \<new name\> | Renames a site entry |
| delete \<name\> | Remove a site name from password storage |
| generate \<name\> | Create a new password for a site |
| setmainpw \<new password\> | Change the main password |
| list \[search term\] | List all entered site names |

The main password must be entered first before any of these commands can be accessed.

## Example

Using `pw` as a command line alias to run passwd.py with arguments, you could do:

~~~
pw set gmail Password_Here
pw comment gmail username=you@gmail.com
~~~

The password could then be retrieved with `pw gmail` or `pw get gmail` after entering the main password