import os
import shutil
import subprocess # Added for executing external commands

try:
    import readline
except ImportError:
    readline = None

class MiniDOS:
    def __init__(self):
        self.current_directory = os.getcwd() # Start in the directory where the script is run

        print("MiniDOS v0.5 - Real OS File System Access with Sudo Prefix & Cat Command")
        print(f"Starting in: {self.current_directory}")
        print("Type 'help' for available commands.")

        self._commands = [
            "exit", "echo", "dir", "create", "type",
            "cls", "ren", "del", "copy", "help",
            "cd", "mkdir", "sudo", "cat" # Added cat to the list of recognized commands
        ]
        self._setup_autocomplete()

    def _setup_autocomplete(self):
        """Sets up command history if readline is available (autocomplete remains off)."""
        if readline:
            readline.set_history_length(1000)
            print("Command History (Up/Down arrow) ENABLED. Autocomplete is DISABLED.")
        else:
            print("Readline module not found. Command history and autocomplete are unavailable.")

    def _completer(self, text, state):
        line = readline.get_line_buffer()
        parts = line.split()

        if not parts or line.endswith(' ') or text == parts[0]:
            matches = [cmd for cmd in self._commands if cmd.startswith(text)]
            try:
                return matches[state] + ' '
            except IndexError:
                return None
        return None

    def _execute_sudo_command(self, args):
        """
        Executes an external command with sudo privileges using subprocess.
        The system's sudo will handle the password prompt.
        """
        try:
            full_command = ['sudo'] + args
            print(f"Attempting to execute: {' '.join(full_command)}")
            print("You may be prompted for your password by the system's 'sudo'.")
            
            result = subprocess.run(full_command, check=True)
            if result.returncode == 0:
                print(f"Command '{' '.join(full_command)}' executed successfully.")
            else:
                print(f"Command '{' '.join(full_command)}' failed with exit code {result.returncode}.")

        except FileNotFoundError:
            print(f"Error: The command '{args[0]}' was not found in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Command '{' '.join(e.cmd)}' failed with exit code {e.returncode}.")
        except PermissionError:
             print("Error: Permission denied. This typically means you don't have sudo privileges or the command itself requires specific permissions.")
        except Exception as e:
            print(f"An unexpected error occurred during sudo command execution: {e}")


    def run(self):
        while True:
            prompt_path = os.getcwd()
            command_line = input(f"{prompt_path}> ").strip()
            if not command_line:
                continue

            parts = command_line.split()

            if not parts:
                continue

            command = parts[0].lower()
            args = parts[1:]

            if command == "exit":
                print("Exiting MiniDOS. Goodbye!")
                break
            elif command == "sudo":
                if not args:
                    print("Usage: sudo <command_to_run_with_root_privileges>")
                    continue
                self._execute_sudo_command(args)
            elif command == "echo":
                self.echo(" ".join(args))
            elif command == "dir":
                self.dir_command()
            elif command == "create":
                self.create_file(args[0] if args else "")
            elif command == "type":
                self.type_file(args[0] if args else "")
            elif command == "cat": # Added cat command handler
                self.cat_command(args)
            elif command == "cls":
                self.cls_command()
            elif command == "ren":
                self.rename_file(args[0] if len(args) > 0 else "",
                                 args[1] if len(args) > 1 else "")
            elif command == "del":
                self.delete_file(args[0] if args else "")
            elif command == "copy":
                self.copy_file(args[0] if len(args) > 0 else "",
                               args[1] if len(args) > 1 else "")
            elif command == "cd":
                self.cd_command(args[0] if args else "")
            elif command == "mkdir":
                self.mkdir_command(args[0] if args else "")
            elif command == "help":
                self.help_command()
            else:
                print(f"Unknown command: '{command}'")

    def echo(self, text):
        print(text)

    def dir_command(self):
        current_path = os.getcwd()
        print(f"\nDirectory of {current_path}")
        print("-" * (len(current_path) + 15))

        try:
            items = sorted(os.listdir(current_path))
        except PermissionError:
            print("Error: Permission denied to access this directory.")
            return
        except OSError as e:
            print(f"Error accessing directory: {e}")
            return

        if not items:
            print(" <EMPTY>")
            return

        dirs_found = []
        files_found = []

        for item in items:
            item_path = os.path.join(current_path, item)
            try:
                if os.path.isdir(item_path):
                    dirs_found.append(item)
                elif os.path.isfile(item_path):
                    files_found.append(item)
            except OSError:
                pass


        for dirname in sorted(dirs_found):
            print(f"<DIR>  {dirname}")

        for filename in sorted(files_found):
            try:
                content_size = os.path.getsize(os.path.join(current_path, filename))
                print(f"       {filename} {content_size} bytes")
            except OSError:
                print(f"       {filename} <ERROR: size unavailable>")
        print()


    def create_file(self, filename):
        if not filename:
            print("Usage: create <filename>")
            return
        
        file_path = os.path.join(os.getcwd(), filename)

        try:
            if os.path.exists(file_path):
                print(f"File '{filename}' already exists.")
                return
            
            with open(file_path, 'w') as f:
                pass
            print(f"File '{filename}' created.")
        except OSError as e:
            print(f"Error creating file '{filename}': {e}")

    def type_file(self, filename):
        """Displays the content of a single file."""
        if not filename:
            print("Usage: type <filename>")
            return
        
        file_path = os.path.join(os.getcwd(), filename)

        try:
            if not os.path.exists(file_path):
                print(f"File '{filename}' not found.")
                return
            if os.path.isdir(file_path):
                print(f"'{filename}' is a directory, not a file.")
                return

            with open(file_path, 'r') as f:
                content = f.read()
            print(f"--- Content of {filename} ---")
            print(content)
            print(f"--- End of {filename} ---")
        except FileNotFoundError: # Explicitly catch this for clearer messages
            print(f"File '{filename}' not found.")
        except PermissionError:
            print(f"Error: Permission denied to read file '{filename}'.")
        except OSError as e:
            print(f"Error reading file '{filename}': {e}")

    def cat_command(self, filenames):
        """Displays the content of one or more files."""
        if not filenames:
            print("Usage: cat <file1> [file2 ...]")
            return

        for filename in filenames:
            file_path = os.path.join(os.getcwd(), filename)

            try:
                if not os.path.exists(file_path):
                    print(f"cat: {filename}: No such file or directory")
                    continue
                if os.path.isdir(file_path):
                    print(f"cat: {filename}: Is a directory")
                    continue

                with open(file_path, 'r') as f:
                    content = f.read()
                print(content, end='') # Use end='' to prevent extra newlines between concatenated files
            except PermissionError:
                print(f"cat: {filename}: Permission denied")
            except OSError as e:
                print(f"cat: {filename}: Error reading file: {e}")
        # Add a final newline after all concatenated content if needed, though print(content) might handle it.
        # print() # Uncomment this if you want an extra newline after ALL cat output.


    def cls_command(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def rename_file(self, old_name, new_name):
        if not old_name or not new_name:
            print("Usage: ren <old_name> <new_name>")
            return

        old_path = os.path.join(os.getcwd(), old_name)
        new_path = os.path.join(os.getcwd(), new_name)

        try:
            if not os.path.exists(old_path):
                print(f"'{old_name}' not found.")
                return
            if os.path.exists(new_path):
                print(f"'{new_name}' already exists. Cannot rename.")
                return

            os.rename(old_path, new_path)
            print(f"'{old_name}' renamed to '{new_name}'.")
        except PermissionError:
            print(f"Error: Permission denied to rename '{old_name}'.")
        except OSError as e:
            print(f"Error renaming '{old_name}' to '{new_name}': {e}")

    def delete_file(self, target_name):
        if not target_name:
            print("Usage: del <filename_or_dirname>")
            return

        target_path = os.path.join(os.getcwd(), target_name)

        try:
            if not os.path.exists(target_path):
                print(f"'{target_name}' not found.")
                return

            if os.path.isfile(target_path):
                os.remove(target_path)
                print(f"File '{target_name}' deleted.")
            elif os.path.isdir(target_path):
                if not os.listdir(target_path): # Check if directory is empty
                    os.rmdir(target_path)
                    print(f"Directory '{target_name}' deleted.")
                else:
                    print(f"Directory '{target_name}' is not empty. Cannot delete non-empty directory.")
            else:
                print(f"'{target_name}' is not a file or an empty directory.")
        except PermissionError:
            print(f"Error: Permission denied to delete '{target_name}'.")
        except OSError as e:
            print(f"Error deleting '{target_name}': {e}")

    def copy_file(self, source, destination):
        if not source or not destination:
            print("Usage: copy <source_filename> <destination_filename>")
            return
        
        source_path = os.path.join(os.getcwd(), source)
        destination_path = os.path.join(os.getcwd(), destination)

        try:
            if not os.path.isfile(source_path):
                print(f"File '{source}' not found or is not a file.")
                return
            if os.path.exists(destination_path):
                if os.path.isdir(destination_path):
                    print(f"'{destination}' is a directory. Cannot overwrite directory with file.")
                    return
                print(f"File '{destination}' already exists. Overwrite? (Y/N)")
                overwrite = input().strip().lower()
                if overwrite != 'y':
                    print("Copy aborted.")
                    return

            shutil.copyfile(source_path, destination_path)
            print(f"File '{source}' copied to '{destination}'.")
        except FileNotFoundError:
            print(f"Source file '{source}' not found.")
        except PermissionError:
            print(f"Error: Permission denied to copy '{source}' to '{destination}'.")
        except OSError as e:
            print(f"Error copying '{source}' to '{destination}': {e}")


    def cd_command(self, path):
        if not path:
            print("Usage: cd <directory_path>")
            print(f"Current directory: {os.getcwd()}")
            return

        try:
            os.chdir(path)
            self.current_directory = os.getcwd() # Update our internal tracker
            print(f"Current directory: {self.current_directory}")
        except FileNotFoundError:
            print(f"Directory '{path}' not found.")
        except NotADirectoryError:
            print(f"'{path}' is not a directory.")
        except PermissionError:
            print(f"Error: Permission denied to change to '{path}'.")
        except OSError as e:
            print(f"Error changing directory to '{path}': {e}")


    def mkdir_command(self, dirname):
        if not dirname:
            print("Usage: mkdir <dirname>")
            return
        
        new_dir_path = os.path.join(os.getcwd(), dirname)

        try:
            if os.path.exists(new_dir_path):
                print(f"'{dirname}' already exists.")
                return
            
            os.mkdir(new_dir_path)
            print(f"Directory '{dirname}' created.")
        except PermissionError:
            print(f"Error: Permission denied to create directory '{dirname}'.")
        except OSError as e:
            print(f"Error creating directory '{dirname}': {e}")


    def help_command(self):
        print("Available commands:")
        print("  echo <text>   - Prints text to the console.")
        print("  dir           - Lists files and directories in the current OS directory.")
        print("  create <file> - Creates a new empty file in the current OS directory.")
        print("  type <file>   - Displays the content of a single file from the current OS directory.")
        print("  cat <file1> [file2...] - Displays the content of one or more files.")
        print("  cls           - Clears the console screen.")
        print("  ren <old> <new> - Renames a file or directory in the current OS directory.")
        print("  del <file/dir> - Deletes a file or an empty directory from the current OS directory.")
        print("  copy <src> <dst> - Copies a file within the current OS directory.")
        print("  cd <path>     - Changes the current working directory of the OS.")
        print("  mkdir <dirname> - Creates a new directory in the current OS directory.")
        print("  sudo <command> - Executes an external system command with root privileges.")
        print("                   (You will be prompted for your password by the system's 'sudo').")
        print("  help          - Shows this help message.")
        print("  exit          - Quits MiniDOS.")

if __name__ == "__main__":
    dos = MiniDOS()
    dos.run()
