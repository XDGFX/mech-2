# Mechatronics Setup

## Setting up VSCode IDE
1. Download and install VSCode.

2. Open the mech-2 folder using `File` > `Open`.

3. Bring up the command line by dragging up from the bottom of the window. The terminal should be `bash` / `zsh` / `fish` (Jack may need to specify WSL instead of PowerShell).

4. Create a virtual environment using venv:
    Type the following commmand on the command line
    ```bash
    $ python3 -m venv .venv
    ```
    Then activate the virtual environment:
    ```bash
    $ source .venv/bin/activate
    ```

5. Install requirements for python
    ```bash
    $ pip3 install -r requirements.txt
    ```

    > WSL may need to install PIP first
    ```bash
    $ sudo apt-get update
    $ sudo apt-get -y install python3-pip
    ```

6. Install recommended VSCode extensions (search for them in the extensions sidebar)
    - Python (Microsoft)
    - Live Share (Microsoft)
    - Git Graph (mhutchie)
