OS = {
"windows": dict(
  NAME="Windows", FILE="windows", SHORT="Windows",
  TERMINAL="Click the **Start** button, type `Command Prompt`, and press **Enter**. A black window with white text opens. This is the terminal you will use for Steps 1 to 3. Miniforge (Step 3) adds a second terminal, the **Miniforge Prompt**, and from Step 4 on you must use that one instead: only it knows the `conda` command.",
  PASTE="In both windows, **right-click** the window to paste. `Ctrl+V` often does not work there.",
  GIT="Go to [git-scm.com/download/win](https://git-scm.com/download/win). The download of the installer starts by itself; if it does not, click the link on that page to download it. Run the installer. Keep every default setting: click **Next** until you reach **Install**, then click **Install**.\n\nWhen it finishes, **close the Command Prompt and open a new one** (the old window does not know about Git yet).",
  MINIFORGE_FILE="Miniforge3-Windows-x86_64.exe",
  MINIFORGE="Download the installer with this link: [Miniforge3-Windows-x86_64.exe](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe). It is about 150 MB, which takes less than a minute on most connections. If your browser asks whether to keep the file, choose **Keep**. (If the link ever stops working, the downloads are also listed on the [Miniforge page](https://github.com/conda-forge/miniforge).) Double-click the downloaded file and follow the installer. Click **Next** (and **I Agree** on the licence page) until you reach these choices:\n\n- When it asks who to install for, choose **Just Me**.\n- Keep the default install folder.\n- On the **Advanced Installation Options** screen, set the four boxes exactly as in the table. They are the installer's defaults, so you may not need to change anything, but check each one:\n\n| Box | Set it to |\n|---|---|\n| Create shortcuts (supported packages only) | **Ticked.** This creates the *Miniforge Prompt* you will use from Step 4. |\n| Add installation to my PATH environment variable | **Unticked.** The installer says \"not recommended\", and the Miniforge Prompt works without it. |\n| Register Miniforge3 as my default Python | **Unticked.** |\n| Clear the package cache upon completion | **Unticked.** (Ticking it also works. It only saves a little disk space.) |\n\nThen click **Install**, wait until it finishes, and click **Finish**.\n\nNow close the Command Prompt. Click **Start**, type `Miniforge Prompt`, and press **Enter**. Use this window for the rest of the guide.",
  FOLDER="%USERPROFILE%\\Research",
  CD_REPO="cd %USERPROFILE%\\Research\\NSDF-Data",
  CD_PYTHON="cd %USERPROFILE%\\Research\\NSDF-Data\\python",
  CD_NOTES="cd %USERPROFILE%\\Research\\NSDF-Data\\data_analysis\\R76\\student",
  MKDIR="mkdir %USERPROFILE%\\Research",
  LISTCMD="dir",
  CHECKIDX="dir %USERPROFILE%\\idx",
  PWDCMD="cd",
  PWDNOTE="With nothing after it, `cd` prints the folder you are in.",
  NEW_TERM="a **Miniforge Prompt** (click **Start**, type `Miniforge Prompt`, press **Enter**)",
  OPEN_TERM="a **Miniforge Prompt** (click **Start**, type `Miniforge Prompt`, press **Enter**)",
  HOME_NOTE="::: tip\n**What is `%USERPROFILE%`?** It is a shortcut that Windows understands. It stands for your own personal folder on this computer, the one named after you (for example `C:\\Users\\YourName`). Type it **exactly as written**, with the two percent signs. Do not replace it with your name: Windows fills it in for you.\n:::",
  FILEMGR="File Explorer",
  IDX="`C:\\Users\\YourName\\idx`",
  IDXPATH="%USERPROFILE%\\idx",
  GOHOME="cd %USERPROFILE%",
  OLDENV="%USERPROFILE%\\old-environment.txt",
  HOMEEX="`C:\\Users\\YourName`",
  NEWLINE_NOTE="",
  CRLF_NOTE="::: tip\n**You may see a warning about LF and CRLF.** On Windows, `git add` can print a line like this one:\n\n`warning: in the working copy of 'data_analysis/R76/student/yourname/`\\\n`first-analysis-yourname.ipynb', LF will be replaced by CRLF the next time Git touches it`\n\nThis is harmless, and your file was still added, so carry on with `git commit`. Every line of a text file ends with an invisible marker. Windows uses two characters for it (CRLF), macOS and Linux use one (LF). Git for Windows keeps LF in the repository and gives you CRLF in your own copy, so it is telling you that it will convert this file the next time it writes it.\n:::\n\n",
  CAREFUL_EXTRA="Windows may show a blue warning box when you run an installer (\"Windows protected your PC\"). Click **More info**, then **Run anyway**, only if you downloaded the file from the link in this guide.",
),
"macos": dict(
  NAME="macOS", FILE="macos", SHORT="macOS",
  TERMINAL="Press **Command + Space**, type `Terminal`, and press **Return**. A window with a text prompt opens. This is the terminal for everything in this guide.",
  PASTE="Paste with **Command + V**.",
  GIT="Type this in the Terminal and press **Return**:\n\n```\nxcode-select --install\n```\n\nA pop-up appears. Click **Install**, agree to the licence, and wait. It can take 15 minutes or more. If the message says the tools are already installed, that is fine.",
  MINIFORGE_FILE="Miniforge3-MacOSX-arm64.sh (Apple chip) or Miniforge3-MacOSX-x86_64.sh (Intel chip)",
  MINIFORGE="First find out which chip your Mac has: click the Apple menu, then **About This Mac**. If it says **Chip: Apple M**something, use the **arm64** file. If it says **Processor: Intel**, use the **x86_64** file.\n\nDownload the file into your **Downloads** folder: [Miniforge3-MacOSX-arm64.sh](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-arm64.sh) (Apple chip) or [Miniforge3-MacOSX-x86_64.sh](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-MacOSX-x86_64.sh) (Intel chip). If your browser asks whether to keep the file, choose **Keep**. Then, in the Terminal, run the command below (use the file name you downloaded):\n\n```\nbash ~/Downloads/Miniforge3-MacOSX-arm64.sh\n```\n\nPress **Return** to read the licence, type `yes` and press **Return**, accept the default location, and when it asks *\"Do you wish the installer to initialize Miniforge3 by running conda init?\"* type `yes`. Then **quit Terminal completely** (Command + Q) and open it again.",
  FOLDER="~/Research",
  CD_REPO="cd ~/Research/NSDF-Data",
  CD_PYTHON="cd ~/Research/NSDF-Data/python",
  CD_NOTES="cd ~/Research/NSDF-Data/data_analysis/R76/student",
  MKDIR="mkdir -p ~/Research",
  LISTCMD="ls",
  CHECKIDX="ls ~/idx",
  PWDCMD="pwd",
  PWDNOTE="`pwd` prints the folder you are in.",
  NEW_TERM="a **new** terminal",
  OPEN_TERM="a terminal (Step 1 of the setup guide)",
  HOME_NOTE="",
  FILEMGR="Finder",
  IDX="`~/idx`",
  IDXPATH="~/idx",
  GOHOME="cd ~",
  OLDENV="~/old-environment.txt",
  HOMEEX="`/Users/YourName`  (the `~` symbol means this folder)",
  CAREFUL_EXTRA="macOS may say an app is from an unidentified developer when you open it. You do not need to open any app in this guide, so you can ignore this.",
  CRLF_NOTE="",
),
"linux": dict(
  NAME="Linux", FILE="linux", SHORT="Linux",
  TERMINAL="Press **Ctrl + Alt + T** (on Ubuntu), or search your applications for **Terminal**. A window with a text prompt opens. This is the terminal for everything in this guide.",
  PASTE="Paste with **Ctrl + Shift + V** (plain Ctrl+V does not work in most terminals).",
  GIT="This guide uses Ubuntu or Debian commands. If you use another distribution, use its package manager instead. Type:\n\n```\nsudo apt install git\n```\n\nIt asks for your password. Nothing appears while you type it; that is normal. Press **Return**, then type `y` and press **Return** if it asks to continue.",
  MINIFORGE_FILE="Miniforge3-Linux-x86_64.sh (most PCs)",
  MINIFORGE="Check your computer type with this command, which prints one word:\n\n```\nuname -m\n```\n\n`x86_64` means the file below. `aarch64` means an ARM computer: use **Miniforge3-Linux-aarch64.sh** instead.\n\nDownload the file into your **Downloads** folder: [Miniforge3-Linux-x86_64.sh](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh), or [Miniforge3-Linux-aarch64.sh](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh) for an ARM computer. Then install it with this command (use the file name you downloaded):\n\n```\nbash ~/Downloads/Miniforge3-Linux-x86_64.sh\n```\n\nPress **Return** to read the licence, type `yes`, accept the default location, and when it asks about running `conda init`, type `yes`. Then **close the terminal and open a new one**.",
  FOLDER="~/Research",
  CD_REPO="cd ~/Research/NSDF-Data",
  CD_PYTHON="cd ~/Research/NSDF-Data/python",
  CD_NOTES="cd ~/Research/NSDF-Data/data_analysis/R76/student",
  MKDIR="mkdir -p ~/Research",
  LISTCMD="ls",
  CHECKIDX="ls ~/idx",
  PWDCMD="pwd",
  PWDNOTE="`pwd` prints the folder you are in.",
  NEW_TERM="a **new** terminal",
  OPEN_TERM="a terminal (Step 1 of the setup guide)",
  HOME_NOTE="",
  FILEMGR="Files (the file manager)",
  IDX="`~/idx`",
  IDXPATH="~/idx",
  GOHOME="cd ~",
  OLDENV="~/old-environment.txt",
  HOMEEX="`/home/yourname`  (the `~` symbol means this folder)",
  CAREFUL_EXTRA="Use `sudo` only for the one command that installs Git. Other commands in this guide must not use it.",
  CRLF_NOTE="",
),
}

GLOSSARY = """
| Word | What it means |
|---|---|
| **Terminal** | A window where you type commands and the computer answers in text. |
| **Command** | One line you type in the terminal, followed by **Enter** (or **Return**). |
| **Folder** (or directory) | A place on your computer that holds files and other folders. |
| **Path** | The address of a folder, such as `C:\\Users\\YourName\\Research`. |
| **Git** | A program that downloads and keeps track of versions of code. |
| **Repository** (repo) | A project folder that Git tracks. Here, `NSDF-Data`. |
| **Python** | The programming language the analysis is written in. You will not need to write Python to finish these guides. |
| **Conda / Miniforge** | A tool that installs Python and packages in separate, named *environments*. |
| **Environment** | A sealed set of programs and versions, so this project's software does not clash with others. |
| **Package** | A piece of ready-made software (for example `numpy`). |
| **Jupyter notebook** | A document that mixes text, code and plots, run one piece (*cell*) at a time. |
| **Branch** | A separate line of work in Git, so your changes do not touch the main code. |
"""

SETUP = """---
title: "Setting up your computer"
subtitle: "NSDF-Data student guide 1 — @NAME@ edition"
date: "Version 19 · 13 October 2026"
---

::: tip
**Who this is for.** You are starting from little or no computing experience. You will paste some commands into a terminal and read the answers. You do **not** need to know any programming. Work through the steps in order. Each step ends with a **Checkpoint**: if it does not match, stop there.
:::

## Before you start

- **Time:** about one hour. Most of it is waiting for downloads and installers.
- **You need:** an internet connection, the password for your computer, and about 3 GB of free disk space.
- **Rule of thumb:** type or paste commands **exactly** as written. Capitals and spaces matter.
- **Nothing to be afraid of:** the commands in this guide install software and make new folders. None of them deletes your files. If you are not sure what a line does, there is a short table after each group of commands.
- **When something goes wrong:** do not guess. Copy the message, note the step you were on, and ask the project lead. See *If something goes wrong* at the end.

## Words you will meet

@GLOSSARY@

## Step 1. Open a terminal

@TERMINAL@

@PASTE@

::: checkpoint
You see a line of text ending in a symbol such as `>`, `$` or `%`. Type `echo hello`{.cmd} and press Enter: the word `hello` should appear under it.
:::

## Step 2. Install Git

@GIT@

::: checkpoint
In the terminal, type `git --version`{.cmd} and press Enter. You should see a line starting with `git version`.
:::

## Step 3. Install Miniforge

Miniforge installs Python and the other packages the analysis needs. Its download file is **@MINIFORGE_FILE@**.

@MINIFORGE@

::: checkpoint
Open @NEW_TERM@ and type `conda --version`{.cmd}, then press Enter. You should see `conda` followed by a version number.
:::

::: careful
@CAREFUL_EXTRA@
:::

## Step 4. Download the NSDF-Data code

@HOME_NOTE@

Your project will live in a folder called `Research`. Create it, go into it, and download the code by running the four commands below. To run a command, type (or paste) the line into the terminal and press Enter. Wait for the prompt to come back, then do the next line:

```
@MKDIR@
cd @FOLDER@
git clone https://github.com/villano-lab/NSDF-Data.git
@CD_REPO@
```

Downloading with `git clone` does not need a GitHub account (saving your work online later does: Step 8). It makes a full copy of the project in a folder named `NSDF-Data`.

**What these lines do**

| Line starts with | What it does |
|---|---|
| `mkdir` | Makes a new folder called `Research`. |
| `cd` | Moves you into a folder. `cd` stands for *change directory*, which is the same as opening a folder in a file window. |
| `git clone` | Downloads a copy of the project from the internet into a new folder called `NSDF-Data`. |

::: checkpoint
Type `@LISTCMD@`{.cmd} and press Enter. You are now inside the `NSDF-Data` folder (your prompt mentions it), so the list shows the project's own folders and files, such as `python`, `data_analysis`, `docs` and `README.md`.
:::

## Step 5. Create your analysis environment

An environment is a sealed box of programs with fixed versions. We make one for this project, called `darkmatter_cli_env`. Type these lines one at a time, pressing Enter after each. The last line takes several minutes and prints a lot of text: wait for the prompt to come back.

```
conda create -n darkmatter_cli_env python=3.12 pip -y
conda activate darkmatter_cli_env
@CD_REPO@
python -m pip install -r requirements.txt
```

**What these lines do**

| Line | What it does |
|---|---|
| `conda create` | Makes a new, empty environment called `darkmatter_cli_env`, with Python 3.12 and the package installer `pip` inside it. |
| `conda activate` | Switches that environment on. While it is on, your prompt starts with `(darkmatter_cli_env)`. |
| `cd` | Moves you into the `NSDF-Data` folder, where the file `requirements.txt` is. |
| `pip install -r requirements.txt` | Installs every program on the project's list, at the exact versions in that file: the software that reads the detector data, numbers and plots, the test tool, and Jupyter, the notebook program you will use later. |

::: tip
`requirements.txt` is a plain text file in the project folder. It is the single list of what the project needs, so when a version changes, only that file changes. You can open it in any text editor to see the list.
:::

::: tip
Every time you open a new terminal, run `conda activate darkmatter_cli_env`{.cmd} first. When it is active, the start of each line shows `(darkmatter_cli_env)`.
:::

::: checkpoint
The last line of the output is a message, not an error, and the `(darkmatter_cli_env)` label is at the start of your prompt.
:::

## Step 6. Check that everything works

First, the tests. They use made-up data, so they need no download. Run the three commands below, one at a time: type (or paste) each line into the terminal and press Enter, and wait for the prompt to come back before the next one:

```
conda activate darkmatter_cli_env
@CD_PYTHON@
python -m pytest -q
```

::: checkpoint
The last line says `101 passed` (it can be a larger number later, which is also fine). If it says `failed`, stop and ask the project lead, and do not change any files.
:::

Then, the data tool:

```
nsdf-cli version
```

::: checkpoint
It prints `NSDF Dark Matter CLI: 0.6.0` (or a later version).
:::

Finally, the notebook program:

```
jupyter lab --version
```

::: checkpoint
It prints a version number, such as `4.4.0`. If it says `jupyter-lab` is not found, check that your prompt starts with `(darkmatter_cli_env)`, go to the `NSDF-Data` folder and run `python -m pip install -r requirements.txt`{.cmd} again.
:::

**What these commands do**

| Line | What it does |
|---|---|
| `conda activate` | Switches your environment on. Do this in every new terminal. |
| `cd` | Moves into the `python` folder of the project. |
| `python -m pytest -q` | Runs the project's built-in self-checks. The `-q` just means "keep the output short". `101 passed` means every check worked. |
| `nsdf-cli version`, `jupyter lab --version` | Each one only asks a program to say which version it is. If it answers, it is installed. |

## Step 7. Let Jupyter notebooks use your environment

Jupyter is the notebook program you will use. Register your environment with it once:

```
python -m ipykernel install --user --name darkmatter_cli_env
```

::: checkpoint
It prints a line that starts with `Installed kernelspec darkmatter_cli_env`.
:::

## Step 8. Get permission to save your work

You will not change the main project. You will save your work on your own **branch**, and for that the lead must give you access:

1. Make a free account at [github.com](https://github.com) if you do not have one.
2. Send your GitHub username to the project lead. They will add you to the project as a collaborator.
3. Once you have accepted the invitation, tell Git your name and email, so your work is labelled as yours. Use your own details:

```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

4. Sign in to GitHub from the terminal, so that GitHub lets your computer upload your work. The second line installs `gh`, GitHub's own small helper program. The third starts the sign-in:

```
conda activate darkmatter_cli_env
conda install gh -c conda-forge -y
gh auth login
```

`gh auth login` asks a few questions. Move with the arrow keys and press Enter. Choose **GitHub.com**, then **HTTPS**, then answer **Y** to "Authenticate Git with your GitHub credentials?", then choose **Login with a web browser**. It prints a short one-time code such as `ABCD-1234`. Press Enter: your web browser opens. Type the code there and click **Authorize**. Back in the terminal, check it worked:

```
gh auth status
```

::: checkpoint
It says `Logged in to github.com account` followed by your GitHub username.
:::

::: careful
Never type your GitHub password into the terminal. GitHub no longer accepts it there, and Git answers with `Password authentication is not supported` or `Invalid username or token`. If you ever see one of those messages, run `gh auth login`{.cmd} again.
:::

5. Create your personal branch (your own space to save work, separate from the main project). Use your own name, without spaces, in place of `yourname`:

```
@CD_REPO@
git checkout -b student-yourname
```

::: checkpoint
The terminal shows `Switched to a new branch 'student-yourname'`.
:::

## Rules for keeping your work safe

- **Never work on `master` or `develop`.** Those are the shared versions. Work only on your `student-` branch.
- **Never commit data.** The raw files in the `idx` folder are large external data, not part of our data analysis code in the NSDF-Data repository. Download only from your home folder, never from inside `NSDF-Data`.
- **Do not run `07221203_2025_dump1_noise.ipynb`** unless the project lead says it is fine. It overwrites a shared archive file.
- **Save often,** and commit your work when a piece is finished (see the first analysis guide).

## You are done when

- [ ] Your terminal opens and `git --version`{.cmd} prints a version.
- [ ] `conda --version`{.cmd} prints a version, in a new terminal.
- [ ] `@LISTCMD@ @FOLDER@`{.cmd} lists `NSDF-Data`.
- [ ] `python -m pytest -q`{.cmd} ends with `101 passed`. Note: first activate the environment with `conda activate darkmatter_cli_env`{.cmd} and go to the repository's `python` folder with `@CD_PYTHON@`{.cmd}, as in Step 6.
- [ ] `nsdf-cli version`{.cmd} prints a version.
- [ ] `jupyter lab --version`{.cmd} prints a version.
- [ ] `jupyter kernelspec list`{.cmd} lists `darkmatter_cli_env`.
- [ ] `gh auth status`{.cmd} says you are logged in to github.com (after access is granted).
- [ ] `git branch`{.cmd} shows `* student-yourname` (after access is granted).

**Next:** *First analysis* (the guide for @NAME@).

::: maintenance
**Your setup is not a one-time job.** The project keeps changing: new releases bring new code and guides, and sometimes a new version of Python or of the packages. **Every time the project lead announces a new release, and whenever the environment check warns you, follow [Updating your setup (@NAME@)](https://villano-lab.github.io/NSDF-Data/students/update-@FILE@.html).** It takes about 10 minutes.
:::

## If something goes wrong

1. Read the **last line** of the message. It usually says what is wrong.
2. Close the terminal, open a new one, and run `conda activate darkmatter_cli_env`{.cmd} again. Many problems are just the wrong environment.
3. Copy the command you ran and the message it printed, and send them to the project lead. A screenshot is also fine.

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include the step number, the command you typed, and the last few lines the computer printed. A screenshot helps. Nobody will be annoyed by a question about a step that did not work.

## Session Info

Guide version 19, 13 October 2026, @NAME@ edition. Written for beginners; please tell the project lead where a step was unclear, so the guide can be fixed.

## Key links

- Notes site: <https://villano-lab.github.io/NSDF-Data/>
- Repository: <https://github.com/villano-lab/NSDF-Data>
- Miniforge downloads: <https://github.com/conda-forge/miniforge>
- Git downloads: <https://git-scm.com>
"""

FIRST = """---
title: "Your first analysis"
subtitle: "NSDF-Data student guide 2 — @NAME@ edition"
date: "Version 19 · 13 October 2026"
---

::: tip
**What you will do.** Download one set of real detector data, open it in a notebook, look at it, and reproduce one number from an existing note. You will need the setup guide for @NAME@ finished first.
:::

## Before you start

- **Time:** about two hours.
- **You need:** the setup guide finished (your environment `darkmatter_cli_env` exists and works).
- **Check:** open @OPEN_TERM@, and run `conda activate darkmatter_cli_env`{.cmd}. The start of the line should show `(darkmatter_cli_env)`.
- **Folder:** you do not need to be in any particular folder yet. Each step below tells you where to go.

::: maintenance
**Keep your setup up to date.** The first code cell in Step 4 checks your environment against the project's current list and warns you if it is out of date. If you see a WARNING, follow [Updating your setup (@NAME@)](https://villano-lab.github.io/NSDF-Data/students/update-@FILE@.html). Do the same after every new release the project lead announces.
:::

## Words you will meet

| Word | What it means here |
|---|---|
| **Series** | One data-taking session, named like `07221203_2025`. The first two digits are the test facility (`07` is UMN, the University of Minnesota); the rest are the date and time the series started, here `221203` (year, month, day: 3 December 2022) and `2025` (20:25). A typical series lasts hours; some are shorter because they are tests. |
| **Dump** | One file set taken from a series, numbered `F0001`, `F0002`, ... |
| **Event** | One moment when the system decided something might have happened and saved a short recording from every detector. Events are numbered in time order. See **Figure 2**, and the [appendix](#appendix-what-an-event-looks-like). |
| **Detector** | In this data, a "detector" number (0, 1 or 2) means one readout electronics unit, not a separate crystal. All three units are wired to the same physical detector, S104. |
| **Channel** | One of the four sensor outputs of a readout unit, numbered 0 to 3. Each channel records its own trace. We use detector 0, channel 0 (**Figure 2**). |
| **Trace** | The recorded signal for one channel in one event: 4096 numbers, one per sample. |
| **Sample** | One reading of the readout circuit's output (usually a voltage or a current). Each sample is 1.6 microseconds long, and is the average of the output over that time. |
| **ADC counts** | The units of a sample. The analog-to-digital converter (ADC) turns each reading into a whole number (an integer), proportional to the measured voltage or current. In this dump the largest are around 8000, so they need at least 13 bits; the exact width is not stated in this guide. |
| **Baseline** | The flat level a trace sits at when nothing happens. |
| **Pretrigger window** | The first samples of a trace, used to measure the baseline. |
| **Pulse** | A sudden rise above the baseline that then slowly falls back. It is what a particle leaves in a trace. |

![](img/trace-pulse.png){width=100%}

**Figure 1.** Two traces on the same scale. Top: noise only. Bottom: a pulse.

![](img/data-structure.png){width=100%}

**Figure 2.** How the data is organised, and which part this guide follows (blue). A series is split into dumps; a dump holds events; each event has a trace from every channel of every detector; a trace is 4096 samples. The code in Step 4 picks detector 0, channel 0 from every event of dump `F0001`, so each row of the table `pulses` is one event, and `pulses[row, sample]` is one number.

## Step 1. Read two notes first (about 30 minutes)

Open the notes site at [villano-lab.github.io/NSDF-Data](https://villano-lab.github.io/NSDF-Data/) and read these, in order:

1. **Note 2**, *Noise-pulse selection*: how we pick quiet traces. It uses the same dump you will download.
2. **Note 2a**, *bstd against time*: how the baseline noise of those traces changes from event to event, in the same dump.

You do **not** need to follow every number. Just learn the words in the table above.

## Step 2. Download the data

@NAVBOX@
First go to your home folder, so the data lands in the right place. Type this, then press Enter:

```
@GOHOME@
```

Now download the data:

```
nsdf-cli download 07221203_2025_F0001
```

The download puts the data in an `idx` folder **in the folder you are in**. Because you went to your home folder first, it lands in @IDX@, inside a folder named `07221203_2025_F0001`. The data is about 34 MB. Wait until the prompt comes back.

::: careful
Never download from inside the `NSDF-Data` folder. Its `idx` folder would sit inside the project, where Git can pick it up. If you have already downloaded there, move the `idx` folder to your home folder, and tell your lead.
:::

**What these lines do:** the first one moves you to your home folder (the `cd` line). The second, `nsdf-cli download`, fetches the data set from the NSDF servers over the internet and puts it in a new `idx` folder.

::: tip
**Optional: tell `nsdf-cli` once where downloads go.** Type this one time, and every later download goes to your `idx` folder, whichever folder you are in:

```
nsdf-cli config --output-global @IDXPATH@
```

Type `nsdf-cli config` to see the setting. It is saved in a small file in your home folder (`.nexus-dm/config.json`), so you do not repeat it. Two more `nsdf-cli` options you may see: `nsdf-cli download SERIES --all` downloads **every** dump of a series (the series in this guide has 30 dumps, about 1.9 GB), so do not use `--all` unless your lead says to; and `nsdf-cli prune` removes the downloaded series from your download folder to free disk space (it shows the folder and asks before it deletes anything).
:::

::: careful
Do not move or edit the downloaded files, and do not add them to Git. They are external data, not part of our data analysis code in the NSDF-Data repository.
:::

::: tip
If the message says the folder already exists, the data may already be there. To check, type `@CHECKIDX@`{.cmd}: if the list shows a folder named `07221203_2025_F0001`, you already have it, and an error message means there is no `idx` folder yet. Ask the project lead before you delete anything.
:::

## Step 3. Open Jupyter in the right folder

Every student works in a folder of their own, inside `data_analysis/R76/student` in the project. Use the same name as in your branch name (`student-yourname`), without spaces, in place of `yourname`. In the terminal, type these lines:

```
conda activate darkmatter_cli_env
@CD_NOTES@
mkdir yourname
cd yourname
jupyter lab
```

**What these lines do:** `conda activate` switches your environment on, `cd` moves you into the folder where the students' notebooks live, `mkdir yourname` makes your own folder there (if it says the folder already exists, that is fine: you made it before), `cd yourname` moves you into it, and `jupyter lab` starts the notebook program. **Leave this terminal window open while you work**: closing it stops Jupyter.

Your web browser opens a Jupyter page. Click **File**, then **New**, then **Notebook**. If it asks which kernel to use, choose **darkmatter_cli_env**.

::: tip
A notebook is a list of boxes called **cells**. Type code in a cell and press **Shift + Enter** to run it. The result appears under the cell. Press **Enter** (without Shift) to keep typing in the same cell.
:::

Give your notebook a name: right-click its tab at the top (it says `Untitled.ipynb`) and choose **Rename Notebook**. In the box, replace `Untitled` with `first-analysis-yourname` (keep `.ipynb` at the end) and click **Rename**.

## Step 4. Load the data and count the traces

Copy this into the first cell and press **Shift + Enter**:

```python
import sys
from pathlib import Path

# Tell Python where the pulse library (the python folder) is.
# This looks upward from the notebook's folder until it finds the project,
# so it works wherever in the project your notebook is.
here = Path.cwd().resolve()
REPO = next((p for p in [here, *here.parents] if (p / "python" / "pulse_io.py").exists()), None)
assert REPO, "Start Jupyter from inside the NSDF-Data folder."
sys.path.insert(0, str(REPO / "python"))

from nsdf_dark_matter.idx import load_all_data
import pulse_io as pio

# Check that your setup is up to date (it only warns; it never stops the notebook).
import check_environment
check_environment.check()

# Open the dump you downloaded.
cdms = load_all_data(str(Path.home() / "idx" / "07221203_2025_F0001"))

# Take every trace from detector 0, channel 0, into one table.
ids, pulses = pio.load_channel_batch(
    cdms, pio.filter_by_detector(cdms.get_detector_ids(), 0), 0)

print(pulses.shape)
```

::: checkpoint
The first line says `Environment OK`, and the last is `(1517, 4096)`: 1517 traces, each with 4096 samples. If you get a different number, stop and check the dump name and the folder in Step 2. If the first line says `WARNING`, you can keep going for now, but follow *Updating your setup* soon.
:::

Want to know what every line did? See [the code, line by line (part A)](#code-step4).

## Step 5. Look at a trace

Click in the empty cell under the one you just ran: Jupyter adds one each time you press **Shift + Enter**. If there is none, click **+** in the toolbar to add one. Put this in it and run it:

```python
import matplotlib.pyplot as plt

plt.plot(pulses[0])
plt.xlabel("sample (1.6 microseconds each)")
plt.ylabel("ADC counts")
plt.show()
```

Now change the `0` to `1`, `2`, `3` and run again. Most traces look like flat noise, with a little jitter. Row 1 is a quiet trace like the top one in **Figure 1**. To see a pulse, try row `1095`. Then see the [appendix](#appendix-what-an-event-looks-like) if you want to know more about what you are looking at.

## Step 6. Reproduce a number from Note 2

Note 2 says that for this dump, a strict selection leaves **179 quiet traces**. Run this in the next empty cell (add one with **+** if there is none):

```python
from dataclasses import replace
from pulse_config import DEFAULT_CONFIG
import pulse_quantities as pq
import pulse_cuts as pc
import numpy as np

c500 = replace(DEFAULT_CONFIG, pretrigger_samples=500)
quiet = pc.excursion_band(pulses, c500) & (np.log10(pq.bstd(pulses)) < 0.5)
print(quiet.sum())
```

::: checkpoint
The output is **179**. If you see a different number, that is worth knowing. Write down the number you got and the steps you took, and tell the project lead. Do not change the project's code to make the number match.
:::

Want to know what every line did? See [the code, line by line (part B)](#code-step6).

## Step 7. Write down what you did

In Jupyter, click **+** to add a cell and change its type from *Code* to **Markdown** in the toolbar. In that cell, write a few sentences in plain English: what you loaded, what you plotted, and what number you got. Then press **Shift + Enter**.

Save with **Command + S** (macOS) or **Ctrl + S** (Windows and Linux).

Once your branch exists (setup guide, Step 8), save your notebook to Git. The first terminal is busy: it is still running Jupyter, so leave it open. Open @NEW_TERM@ for the Git commands. A new terminal starts in your home folder, so the first line below moves you into the project folder from the setup guide:

```
@CD_REPO@
git branch --show-current
git status
git add data_analysis/R76/student/yourname/first-analysis-yourname.ipynb
git commit -m "First analysis: load dump 1 and count the quiet traces"
git push -u origin student-yourname
```

**What these lines do:** the first one moves you into the project. `git branch --show-current` prints the name of the branch you are on, and `git status` lists what has changed since your last save. **Make this a habit: every time you open a terminal in a project, look at the branch and the status before you do anything else.** Then `git add` picks the file you want to save, `git commit` saves a snapshot of it with your short message, and `git push` uploads that snapshot to GitHub, to your own branch.

::: checkpoint
`git branch --show-current` prints `student-yourname` (your own branch), and `git status` starts with `On branch student-yourname` and lists your notebook under **Untracked files** (a new file) or **Changes not staged for commit** (a file you changed). If the branch is `develop` or `master`, stop and ask the project lead: do not commit there.
:::

@CRLF_NOTE@::: careful
Commit only your notebook. Check the list from `git status` before committing. If you see `.bin` files or anything from the `idx` folder, do not add them.
:::

## You are done when

- [ ] `(1517, 4096)` printed after loading the data.
- [ ] You plotted at least three traces and can say what the flat ones look like.
- [ ] You got 179 from the selection, or wrote down what you got and why you think it differs.
- [ ] Your notebook is saved, and committed to your branch if you have access.

## Common problems

| What you see | What to do |
|---|---|
| `ModuleNotFoundError: No module named 'nsdf_dark_matter'` | You are not in the environment. Run `conda activate darkmatter_cli_env`{.cmd}, then restart the notebook kernel (**Kernel**, then **Restart Kernel**). |
| `ModuleNotFoundError: No module named 'pulse_io'` | Jupyter was started from the wrong folder. Close it and start it again from your own folder in `data_analysis/R76/student` (Step 3). |
| `FileNotFoundError` on the dump folder | The download did not finish, or it went somewhere else. Check the folder in Step 2. |
| A huge spike at the very start of traces | This is a real electronics glitch in the first few samples, not a bug. It is explained in Note 2a. |
| The kernel is not `darkmatter_cli_env` | Click the kernel name at the top right and choose **darkmatter_cli_env**. |

::: careful
Do not run `07221203_2025_dump1_noise.ipynb` unless the project lead says it is fine. It overwrites a shared archive file.
:::

## Appendix: what an event looks like

You do not need this to finish the guide. It explains the words in the table at the top.

The detector system watches its sensors all the time. Whenever it decides that something may have happened, it saves a short recording from every sensor. That moment is one **event**. Events are numbered in time order, and the numbers restart in every dump, so an event number alone does not identify an event.

In Run 76 one physical detector (a silicon detector, S104) is read out by three older ("legacy") electronics units, each with four **channels**, all connected to that same detector. The software calls the units detector 0, 1 and 2, and so does this guide. One event therefore holds up to 3 x 4 = 12 recordings. Each recording is a **trace**: 4096 numbers, one per sample. In this dump, 7 of the 12 slots hold a trace and the other 5 read all zeros. We follow one channel, detector 0 channel 0, through all 1517 events.

![](img/channels.png){width=90%}

**Figure 3.** The four channels of detector 0 in one event. It is a schematic: the four sectors only stand for the channel numbers, and it does not show where the real sensors sit. The detector's own sensor layout is similar to the SuperCDMS HV detector mask, but not the same.

A trace looks like a flat line with a little jitter (the **baseline**) until something happens. The first 500 samples, the **pretrigger window**, are used to measure the baseline. If a particle deposits energy, the trace jumps up at once and then slowly falls back: a **pulse**. In **Figure 1**, the pulse in event 11108 starts just after sample 500; in this dump, many pulses start there.

The pulse trace in **Figure 1** is row 1095 of the table `pulses` from Step 4 (the row is the position in the table, not the event number). Row 1 is a quiet trace.

## Appendix: the code, line by line {#appendix-code}

You do not need this to finish the guide. It goes through the code you pasted, one line at a time: each line of code, and next to it, in red, what it does. A line that begins with `#` is a comment: Python ignores it, and it is there for people to read, so the comments are left out here.

### Part A. Step 4: load the data and count the traces {#code-step4}

::: explain
```python
import sys
from pathlib import Path
```

Bring in two tools. `sys` controls where Python looks for code. `Path` works with folder names in the same way on every kind of computer.
:::

::: explain
```python
here = Path.cwd().resolve()
```

The folder Jupyter is working in, written out in full.
:::

::: explain
```python
REPO = next((p for p in [here, *here.parents]
             if (p / "python" / "pulse_io.py").exists()), None)
```

Look at `here` and then at each folder above it, one after another, and take the first one that contains the file `python/pulse_io.py`. That folder is the whole NSDF-Data project. If there is none, `REPO` is `None`.
:::

::: explain
```python
assert REPO, "Start Jupyter from inside the NSDF-Data folder."
```

Stop with that message if the project was not found, which means Jupyter was started in the wrong place.
:::

::: explain
```python
sys.path.insert(0, str(REPO / "python"))
```

Tell Python to look in the project's `python` folder first, so that the next `import` lines can find the project's own code.
:::

::: explain
```python
from nsdf_dark_matter.idx import load_all_data
```

Bring in the function, from the NSDF software, that reads a downloaded dump.
:::

::: explain
```python
import pulse_io as pio
```

Bring in the project's helpers for traces. `as pio` gives it a short name.
:::

::: explain
```python
import check_environment
check_environment.check()
```

Bring in the project's environment check and run it. It compares your Python and your packages with the project's list (`requirements.txt`) and prints `Environment OK`, or a `WARNING` that says what differs and where to read how to fix it. It is only a warning: your notebook carries on either way.
:::

::: explain
```python
cdms = load_all_data(str(Path.home() / "idx" / "07221203_2025_F0001"))
```

Open the dump you downloaded in Step 2. `Path.home()` is your home folder, and `/ "idx" / "07221203_2025_F0001"` follows the path down to the dump, the same folder Step 2 created. The whole dump is read into the computer's memory and called `cdms`.
:::

::: explain
```python
ids, pulses = pio.load_channel_batch(
    cdms, pio.filter_by_detector(cdms.get_detector_ids(), 0), 0)
```

Read it from the inside out. `cdms.get_detector_ids()` is the list of names of every group of traces (a name holds an event number and a detector number). `pio.filter_by_detector(..., 0)` keeps only the names for detector 0. `pio.load_channel_batch(cdms, ..., 0)` takes channel 0 from each of those and stacks the traces into one table. It gives back two things: `ids`, the names in order, and `pulses`, the table, with one row for each event and one column for each sample (see **Figure 2**).
:::

::: explain
```python
print(pulses.shape)
```

Show the size of the table as (rows, columns). That is the `(1517, 4096)` you checked.
:::

### Part B. Step 6: count the quiet traces {#code-step6}

::: explain
```python
from dataclasses import replace
```

A tool for making a copy of a group of settings with one value changed.
:::

::: explain
```python
from pulse_config import DEFAULT_CONFIG
```

The project's standard settings, such as how many samples at the start of a trace count as the baseline window (1000 by default) and how many of the very first samples to skip because of the electronics glitch (10).
:::

::: explain
```python
import pulse_quantities as pq
```

Functions that work out one number for each trace, such as how much its baseline wobbles.
:::

::: explain
```python
import pulse_cuts as pc
```

Functions that answer yes or no for each trace: "keep this one?"
:::

::: explain
```python
import numpy as np
```

Tools for working with tables of numbers.
:::

::: explain
```python
c500 = replace(DEFAULT_CONFIG, pretrigger_samples=500)
```

A copy of the standard settings in which the baseline window is the first 500 samples, as in Note 2.
:::

::: explain
```python
quiet = pc.excursion_band(pulses, c500) & (
    np.log10(pq.bstd(pulses)) < 0.5)
```

Two yes-or-no tests joined by `&`, which means "and". The result, `quiet`, has one `True` or `False` for each trace. `pc.excursion_band(pulses, c500)` is `True` when the trace's largest swing after the baseline window, compared with the wobble of its own baseline, falls in the middle band chosen in Note 2. `pq.bstd(pulses)` is the wobble (the standard deviation) of each trace's baseline, and `np.log10(...) < 0.5` keeps only the traces whose baseline wobbles little: under about 3 counts.
:::

::: explain
```python
print(quiet.sum())
```

A `True` counts as 1 and a `False` as 0, so the sum is the number of traces that passed both tests. That is the 179 of the checkpoint.
:::

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include the step number, the command you typed, and the last few lines the computer printed. A screenshot helps. Nobody will be annoyed by a question about a step that did not work.

## Session Info

Guide version 19, 13 October 2026, @NAME@ edition. Written for beginners; please tell the project lead where a step was unclear.

## Key links

- Note 2: <https://villano-lab.github.io/NSDF-Data/notes/note-02-noise-selection.html>
- Note 2a: <https://villano-lab.github.io/NSDF-Data/notes/note-02a-bstd-vs-time.html>
- Note 1 (series catalog) and Note 1a (python library structure), for later: <https://villano-lab.github.io/NSDF-Data/>
- Repository: <https://github.com/villano-lab/NSDF-Data>
"""

UPDATE = """---
title: "Updating your setup"
subtitle: "NSDF-Data student guide 7 — @NAME@ edition"
date: "Version 5 · 13 October 2026"
---

::: maintenance
**Do this regularly, not once.** The project keeps changing: new releases bring new code and guides, and sometimes a new version of Python or of the packages the notebooks use. If your setup is behind, things can fail in confusing ways. Follow this guide **whenever the project lead announces a new release**, **whenever the environment check warns you**, and **when you start a new piece of work after a long break**. It takes about 10 minutes, or 20 to 30 minutes if Python itself changed (mostly waiting).
:::

::: tip
**Who this is for.** You have finished the setup guide and the first analysis guide for @NAME@. Nothing here deletes your notebooks or your work. If you are not sure about a step, stop and ask the project lead.
:::

## Before you start

- **Time:** about 10 minutes (20 to 30 if Python changed; most of that is waiting for deleting and installing).
- **You need:** the setup guide finished, and your own work saved in Git (see Step 7 of the first analysis guide). Step 2 below checks.
- **Close Jupyter first:** in JupyterLab choose **File**, then **Shut Down**, and close the terminal that was running it. Updating files while Jupyter is open can fail, especially on Windows.
- **Where to find out what changed:** the [release notes](https://github.com/villano-lab/NSDF-Data/releases). The project lead also writes to you when a release needs something from you: look for the words "Students, please".

## Words you will meet

| Word | What it means here |
|---|---|
| **Release** | A numbered version of the whole project, such as 0.6.0. The number is in the file `VERSION`. |
| **Environment** | The sealed box of programs with fixed versions that you made in the setup guide, called `darkmatter_cli_env`. |
| **Pinned** | A package listed in `requirements.txt` with an exact version, such as `numpy==2.2.6`. |
| **Merge** | Bring the newest shared changes of the project (the branch `develop`) into your own branch. |

## Step 1. Check your setup

Open @OPEN_TERM@, and type these lines, one at a time, pressing Enter after each:

```
conda activate darkmatter_cli_env
@CD_PYTHON@
python check_environment.py
```

**What these lines do:** the first switches your environment on, the second moves you into the project's `python` folder, and the third runs the project's environment check.

::: checkpoint
If it says `Environment OK`, your environment is current: go to Step 2 anyway if a new release was announced, otherwise you are done. If it says `WARNING`, it lists what differs. A line about **Python** means Step 4. A line about a **package** means Step 3. Do Step 2 first in both cases.
:::

## Step 2. Bring the newest project changes into your branch

Your branch is your own copy of the project. The newest shared changes are on the branch `develop`. Type:

```
@CD_REPO@
git branch --show-current
git status
```

::: checkpoint
`git branch --show-current` prints `student-yourname` (your own branch), and `git status` says `nothing to commit` (or lists only files you have not added, such as your own notebook folder). If it lists changed files you want to keep, **save them first**: commit them as in Step 7 of the first analysis guide, then come back. If the branch is `develop` or `master`, stop and ask the project lead.
:::

Now bring the changes in:

```
git fetch origin
git merge --no-edit origin/develop
```

**What these lines do:** `git fetch` downloads the newest changes without touching your files, and `git merge` combines them with your branch (`--no-edit` keeps git from opening a text editor to ask for a message). It prints `Already up to date.` or a list of the files that changed.

::: careful
If git says `CONFLICT`, stop. Do not edit anything and do not try to fix it: copy the message and send it to the project lead.
:::

## Step 3. If packages changed: install the project's list again

Do this when the check named a package. Type:

```
conda activate darkmatter_cli_env
@CD_REPO@
python -m pip install -r requirements.txt
```

**What these lines do:** the last one reads `requirements.txt` and installs every package on the list at the exact version given, replacing any that differ. It prints a lot of text and can take a few minutes.

Then run the check again (Step 1). It should say `Environment OK`.

## Step 4. If Python changed: make a new environment

Do this when the check says your Python is not the version the guides use. Conda can update Python inside an existing environment, but most of this project's packages were installed with pip, which does not rebuild them for the new Python, and that can leave a broken mix. It is more reliable to remove the old environment and make a new one. Nothing you need is lost: the environment is rebuilt from `requirements.txt`, and the first lines below save a list of what the old one had, in case you installed something extra. Type each line and press Enter, and be patient: **removing the old environment takes a few minutes, and so does the final install.**

```
@GOHOME@
conda activate darkmatter_cli_env
python -m pip freeze > @OLDENV@
conda deactivate
conda env remove -n darkmatter_cli_env -y
conda create -n darkmatter_cli_env python=3.12 pip -y
conda activate darkmatter_cli_env
@CD_REPO@
python -m pip install -r requirements.txt
jupyter kernelspec remove darkmatter_cli_env -y
python -m ipykernel install --user --name darkmatter_cli_env
```

**What these lines do**

| Line | What it does |
|---|---|
| `cd` (the first line) | Moves you to your home folder, where the list of old packages is saved. |
| `conda activate` | Switches your old environment on, so the next line can read it. |
| `pip freeze > ...old-environment.txt` | Writes the names and versions of everything in the old environment into the file `old-environment.txt` in your home folder. |
| `conda deactivate` | Switches the old environment off. |
| `conda env remove` | Deletes the old environment. This takes a few minutes. |
| `conda create` | Makes a new, empty environment called `darkmatter_cli_env`, with Python 3.12 and `pip`. |
| `conda activate` | Switches the new environment on. |
| `cd` (the second one) | Moves you into the `NSDF-Data` folder, where `requirements.txt` is. |
| `pip install -r requirements.txt` | Installs the project's list of packages. It takes about five minutes. |
| `jupyter kernelspec remove` | Removes Jupyter's old entry for the environment. If it says there is no such kernel, that is fine. |
| `ipykernel install` | Tells Jupyter about the new environment. |

::: careful
If you installed anything yourself into the old environment, its name is in `old-environment.txt` in your home folder. Install it again into the new environment with `python -m pip install` and the name, if you still need it. If one of the lines above fails, do not skip it: see *If something goes wrong* below.
:::

## Step 5. Check that everything works

```
conda activate darkmatter_cli_env
@CD_PYTHON@
python check_environment.py
python -m pytest -q
```

::: checkpoint
The check says `Environment OK` and `pytest` ends with `101 passed`. If not, do not guess: copy the output and send it to the project lead.
:::

## Step 6. Start Jupyter again

```
conda activate darkmatter_cli_env
@CD_NOTES@
cd yourname
jupyter lab
```

Use the same `yourname` as in your branch name. If Jupyter asks for a kernel, choose **darkmatter_cli_env**. Open your notebook and run the first cell: it should print `Environment OK` and then `(1517, 4096)`.

## Good to know: the NSDF software changes too

The programs that download and read the data, the `nsdf-cli` command and the `nsdf_dark_matter` library, come from a separate project called **Nexus-DM** (formerly NSDF-SLAC). Its team improves it often, and our analysis depends heavily on it. So:

- **We pin its versions.** `requirements.txt` names the exact version of both packages. The project lead tests each new version here before it goes on the list, so a change upstream cannot quietly change your results. **Do not upgrade them yourself** (no `pip install --upgrade`): you could end up with a mix nobody has tested.
- **You get a new version the usual way.** When the list changes, the release notes say so, the project lead writes to you ("Students, please"), and you follow Step 3 of this guide. The environment check in Step 1 warns you when your versions differ from the list.
- **To see your versions,** type `nsdf-cli version`, and `python -m pip show nsdf-dark-matter nsdf-dark-matter-cli` (look at the `Version` lines).
- **New commands come with new versions.** Version 0.6.0 added `nsdf-cli config` (the folder that downloads go to), `nsdf-cli download ... --all` and `nsdf-cli prune`; the first analysis guide, Step 2, explains them.
- **If something behaves differently after an update,** send the project lead the output of `nsdf-cli version` and the message you saw. The lead reports problems in the NSDF software to its team; you do not need to.

What the Nexus-DM team changed in each version is in [their release notes](https://github.com/nsdf-fabric/nexus-dm/releases).

## You are done when

- [ ] `python check_environment.py`{.cmd} (in the `python` folder, with the environment on) says `Environment OK`.
- [ ] `git status`{.cmd} in the `NSDF-Data` folder shows your own branch and nothing you want to keep is unsaved.
- [ ] `python -m pytest -q`{.cmd} in the `python` folder ends with `101 passed`.
- [ ] `jupyter kernelspec list`{.cmd} lists `darkmatter_cli_env`.
- [ ] Your notebook's first cell prints `Environment OK`.

## If something goes wrong

| What you see | What to do |
|---|---|
| `python: can't open file 'check_environment.py'` or `No such file` | You are not in the `python` folder. Run the `cd` line of Step 1, and make sure Step 2 finished (the file arrives with the newest changes). |
| `EnvironmentLocationNotFound` or "not a conda environment" on `conda env remove` | There is no environment of that name any more. That is fine: carry on with the next line. |
| `CondaError: Prefix record '...' already exists` on `conda create` | Conda's download cache has a bad entry. Type `conda clean --all -y`{.cmd} and then run the `conda create` line again. |
| `conda create` complains that the folder exists, or a leftover folder `darkmatter_cli_env` is in the `envs` folder | The removal left an empty shell behind. Type `conda info --envs`{.cmd} to see where the environments live, check that the leftover `darkmatter_cli_env` folder holds no `python` file, delete that folder, and run the `conda create` line again. |
| `Python was not found; run without arguments to install from the Microsoft Store` (Windows) | Your environment is not switched on, or it was not created. Type `conda env list`{.cmd}. If `darkmatter_cli_env` is not in the list, run the `conda create` line of Step 4 again. If it is, run `conda activate darkmatter_cli_env`{.cmd}. |
| `FileExistsError` on the `ipykernel install` line | Jupyter already has a kernel of that name. Run the `jupyter kernelspec remove` line of Step 4 (the one ending `-y`), then the `ipykernel install` line again. |
| git says `CONFLICT` | Stop and send the message to the project lead. Do not edit the files. |
| A text editor opens (a window full of `~` characters, or a message starting `Merge branch`) after `git merge` | git is asking for a message for the merge. In the editor (usually Vim): press `Esc`, type `:wq`{.cmd} and press Enter. The merge finishes with git's own message. |
| The kernel is missing in Jupyter | In the environment, run the last two lines of Step 4 again, then restart Jupyter. |

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include the step number, the command you typed, and the last few lines the computer printed. A screenshot helps. Nobody will be annoyed by a question about a step that did not work.

## Session Info

Guide version 5, 13 October 2026, @NAME@ edition. Written for beginners; please tell the project lead where a step was unclear, so the guide can be fixed.

## Key links

- Release notes: <https://github.com/villano-lab/NSDF-Data/releases>
- Repository: <https://github.com/villano-lab/NSDF-Data>
- The setup guide and the first analysis guide: <https://villano-lab.github.io/NSDF-Data/>
"""

NAVBOX = '::: navigate\n**Where am I, and what is here?** Two commands show you. Try both now; neither changes anything.\n\n- `@PWDCMD@`{.cmd} prints the folder you are in. The prompt also names it.\n- `@LISTCMD@`{.cmd} lists the files and folders inside it.\n\nTo move, type `cd` and a folder name from the list, or `cd ..` to go back up one level.\n:::\n'

for key, o in OS.items():
    o = dict(o)
    for kind, tpl in (("setup", SETUP), ("first-analysis", FIRST), ("update", UPDATE)):
        s = tpl.replace("@GLOSSARY@", GLOSSARY.strip()).replace("@NAVBOX@", NAVBOX)
        for k in ("NAME","TERMINAL","PASTE","GIT","MINIFORGE_FILE","MINIFORGE","CAREFUL_EXTRA","FOLDER","CD_REPO","CD_PYTHON","CD_NOTES","MKDIR","LISTCMD","IDX","GOHOME","OLDENV","IDXPATH","NEW_TERM","OPEN_TERM","HOME_NOTE","CHECKIDX","PWDCMD","CRLF_NOTE","FILE"):
            s = s.replace("@"+k+"@", o[k])
        assert "@" not in s.replace("@", "@") or True
        open(f"{kind}-{key}.md", "w", encoding="utf-8", newline="\n").write(s)
        print(kind, key, len(s))
