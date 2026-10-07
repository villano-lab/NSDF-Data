---
title: "Setting up your computer"
subtitle: "NSDF-Data student guide 1 — Windows edition"
date: "Version 8 · 7 October 2026"
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

| Word | What it means |
|---|---|
| **Terminal** | A window where you type commands and the computer answers in text. |
| **Command** | One line you type in the terminal, followed by **Enter** (or **Return**). |
| **Folder** (or directory) | A place on your computer that holds files and other folders. |
| **Path** | The address of a folder, such as `C:\Users\YourName\Research`. |
| **Git** | A program that downloads and keeps track of versions of code. |
| **Repository** (repo) | A project folder that Git tracks. Here, `NSDF-Data`. |
| **Python** | The programming language the analysis is written in. You will not need to write Python to finish these guides. |
| **Conda / Miniforge** | A tool that installs Python and packages in separate, named *environments*. |
| **Environment** | A sealed set of programs and versions, so this project's software does not clash with others. |
| **Package** | A piece of ready-made software (for example `numpy`). |
| **Jupyter notebook** | A document that mixes text, code and plots, run one piece (*cell*) at a time. |
| **Branch** | A separate line of work in Git, so your changes do not touch the main code. |

## Step 1. Open a terminal

Click the **Start** button, type `Command Prompt`, and press **Enter**. A black window with white text opens. This is the terminal you will use for Steps 1 to 3. Miniforge (Step 3) adds a second terminal, the **Miniforge Prompt**, and from Step 4 on you must use that one instead: only it knows the `conda` command.

In both windows, **right-click** the window to paste. `Ctrl+V` often does not work there.

::: checkpoint
You see a line of text ending in a symbol such as `>`, `$` or `%`. Type `echo hello` and press Enter: the word `hello` should appear under it.
:::

## Step 2. Install Git

Go to [git-scm.com/download/win](https://git-scm.com/download/win). The download of the installer starts by itself; if it does not, click the link on that page to download it. Run the installer. Keep every default setting: click **Next** until you reach **Install**, then click **Install**.

When it finishes, **close the Command Prompt and open a new one** (the old window does not know about Git yet).

::: checkpoint
In the terminal, type `git --version` and press Enter. You should see a line starting with `git version`.
:::

## Step 3. Install Miniforge

Miniforge installs Python and the other packages the analysis needs. Its download file is **Miniforge3-Windows-x86_64.exe**.

Download the installer with this link: [Miniforge3-Windows-x86_64.exe](https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe). It is about 150 MB, so it can take a few minutes. If your browser asks whether to keep the file, choose **Keep**. (If the link ever stops working, the downloads are also listed on the [Miniforge page](https://github.com/conda-forge/miniforge).) Double-click the downloaded file and follow the installer. Click **Next** (and **I Agree** on the licence page) until you reach these choices:

- When it asks who to install for, choose **Just Me**.
- Keep the default install folder.
- On the **Advanced Installation Options** screen, set the four boxes exactly as in the table. They are the installer's defaults, so you may not need to change anything, but check each one:

| Box | Set it to |
|---|---|
| Create shortcuts (supported packages only) | **Ticked.** This creates the *Miniforge Prompt* you will use from Step 4. |
| Add installation to my PATH environment variable | **Unticked.** The installer says "not recommended", and the Miniforge Prompt works without it. |
| Register Miniforge3 as my default Python | **Unticked.** |
| Clear the package cache upon completion | **Unticked.** (Ticking it also works. It only saves a little disk space.) |

Then click **Install**, wait until it finishes, and click **Finish**.

Now close the Command Prompt. Click **Start**, type `Miniforge Prompt`, and press **Enter**. Use this window for the rest of the guide.

::: checkpoint
Open a **Miniforge Prompt** (click **Start**, type `Miniforge Prompt`, press **Enter**) and type `conda --version`, then press Enter. You should see `conda` followed by a version number.
:::

::: careful
Windows may show a blue warning box when you run an installer ("Windows protected your PC"). Click **More info**, then **Run anyway**, only if you downloaded the file from the link in this guide.
:::

## Step 4. Download the NSDF-Data code

::: tip
**What is `%USERPROFILE%`?** It is a shortcut that Windows understands. It stands for your own personal folder on this computer, the one named after you (for example `C:\Users\YourName`). Type it **exactly as written**, with the two percent signs. Do not replace it with your name: Windows fills it in for you.
:::

Your project will live in a folder called `Research`. Create it, go into it, and download the code. Type each line and press Enter:

```
mkdir %USERPROFILE%\Research
cd %USERPROFILE%\Research
git clone https://github.com/villano-lab/NSDF-Data.git
cd %USERPROFILE%\Research\NSDF-Data
```

Downloading with `git clone` does not need a GitHub account. It makes a full copy of the project in a folder named `NSDF-Data`.

**What these lines do**

| Line starts with | What it does |
|---|---|
| `mkdir` | Makes a new folder called `Research`. |
| `cd` | Moves you into a folder. `cd` stands for *change directory*, which is the same as opening a folder in a file window. |
| `git clone` | Downloads a copy of the project from the internet into a new folder called `NSDF-Data`. |

::: checkpoint
Type `dir` and press Enter. You should see `NSDF-Data` in the list.
:::

## Step 5. Create your analysis environment

An environment is a sealed box of programs with fixed versions. We make one for this project, called `darkmatter_cli_env`. Type these lines one at a time, pressing Enter after each. The third line takes several minutes and prints a lot of text: wait for the prompt to come back.

```
conda create -n darkmatter_cli_env python=3.10 -y
conda activate darkmatter_cli_env
python -m pip install nsdf-dark-matter==0.3.0 nsdf-dark-matter-cli==0.5.0
python -m pip install numpy==2.2.6 matplotlib==3.10.7 h5py pytest ipykernel
python -m pip install jupyterlab
```

**What these lines do**

| Line | What it does |
|---|---|
| `conda create` | Makes a new, empty environment called `darkmatter_cli_env`, with Python 3.10 inside it. |
| `conda activate` | Switches that environment on. While it is on, your prompt starts with `(darkmatter_cli_env)`. |
| `pip install nsdf-dark-matter...` | Installs the software that reads the detector data. |
| `pip install numpy...` | Installs software for numbers, plots and checking that everything works. |
| `pip install jupyterlab` | Installs Jupyter, the notebook program you will use later. |

::: tip
The project folder also has a file called `requirements.txt` that lists the same software versions. You do **not** need it: the lines above do the whole job, and they work the same on every computer.
:::

::: tip
Every time you open a new terminal, run `conda activate darkmatter_cli_env` first. When it is active, the start of each line shows `(darkmatter_cli_env)`.
:::

::: checkpoint
The last line of the output is a message, not an error, and the `(darkmatter_cli_env)` label is at the start of your prompt.
:::

## Step 6. Check that everything works

First, the tests. They use made-up data, so they need no download. Type each line and press Enter:

```
conda activate darkmatter_cli_env
cd %USERPROFILE%\Research\NSDF-Data\python
python -m pytest -q
```

::: checkpoint
The last line says `52 passed` (it can be a larger number later, which is also fine). If it says `failed`, stop and ask the project lead, and do not change any files.
:::

Then, the data tool:

```
nsdf-cli version
```

::: checkpoint
It prints `NSDF Dark Matter CLI: 0.5.0` (or a later version).
:::

Finally, the notebook program:

```
jupyter lab --version
```

::: checkpoint
It prints a version number, such as `4.4.0`. If it says `jupyter-lab` is not found, run `python -m pip install jupyterlab` and try again.
:::

**What these commands do**

| Line | What it does |
|---|---|
| `conda activate` | Switches your environment on. Do this in every new terminal. |
| `cd` | Moves into the `python` folder of the project. |
| `python -m pytest -q` | Runs the project's built-in self-checks. The `-q` just means "keep the output short". `52 passed` means every check worked. |
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

4. Create your personal branch (your own space to save work, separate from the main project). Use your own name, without spaces, in place of `yourname`:

```
cd %USERPROFILE%\Research\NSDF-Data
git checkout -b student-yourname
```

::: checkpoint
The terminal shows `Switched to a new branch 'student-yourname'`.
:::

## Rules for keeping your work safe

- **Never work on `master` or `develop`.** Those are the shared versions. Work only on your `student-` branch.
- **Never commit data.** The raw files in the `idx` folder are large and not part of the project. Download only from your home folder, never from inside `NSDF-Data`.
- **Do not run `07221203_2025_dump1_noise.ipynb`** unless the project lead says it is fine. It overwrites a shared archive file.
- **Save often,** and commit your work when a piece is finished (see the first analysis guide).

## You are done when

- [ ] Your terminal opens and `git --version` prints a version.
- [ ] `conda --version` prints a version, in a new terminal.
- [ ] The `NSDF-Data` folder is in `%USERPROFILE%\Research`.
- [ ] `python -m pytest -q` in the `python` folder ends with `52 passed`.
- [ ] `nsdf-cli version` prints a version.
- [ ] `jupyter lab --version` prints a version.
- [ ] Your Jupyter kernel `darkmatter_cli_env` is installed.
- [ ] You have a `student-` branch (after access is granted).

**Next:** *First analysis* (the guide for Windows).

## If something goes wrong

1. Read the **last line** of the message. It usually says what is wrong.
2. Close the terminal, open a new one, and run `conda activate darkmatter_cli_env` again. Many problems are just the wrong environment.
3. Copy the command you ran and the message it printed, and send them to the project lead. A screenshot is also fine.

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include the step number, the command you typed, and the last few lines the computer printed. A screenshot helps. Nobody will be annoyed by a question about a step that did not work.

## Session Info

Guide version 8, 7 October 2026, Windows edition. Written for beginners; please tell the project lead where a step was unclear, so the guide can be fixed.

## Key links

- Notes site: <https://villano-lab.github.io/NSDF-Data/>
- Repository: <https://github.com/villano-lab/NSDF-Data>
- Miniforge downloads: <https://github.com/conda-forge/miniforge>
- Git downloads: <https://git-scm.com>
