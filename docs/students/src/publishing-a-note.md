---
title: "Publishing a note"
subtitle: "NSDF-Data student guide 4 — for every computer"
date: "Version 2 · 6 October 2026"
---

::: tip
**This is guide 4 of 5.** It is about getting a finished note onto the site. Guide 3 covers writing the note; guide 5 covers doing this with an AI assistant.
:::

## What happens when you publish

Your note goes through four stages. You do the first two, the automatic check does the third, and your lead does the fourth:

1. **You** write the note as a `.md` file in the `notes/src/` folder, on your own branch.
2. **You** open a **pull request**: a request to add your work to the project.
3. **The check** runs at once. It lists anything wrong with the note.
4. **Your lead** reviews the note, gives it a number (S1, S2, …), and merges it. After the merge the site builds your page. This takes a few minutes.

Nothing reaches the public site until the merge.

## Before you start

- **You have write access.** Your lead adds you to the project on GitHub. You need this to push a branch.
- **Your note is written and checked** against guide 3, and the notebook it uses is committed to your branch.
- **You know your branch name.** It is `student-yourname`, from the setup guide.

## Step 1. Put your note in the right place

Your note goes in the `notes/src/` folder:

- `notes/src/your-note-name.md` is the note. Start from `_template.md` and keep the header.
- `notes/src/img/` holds the pictures. Refer to them as `img/your-picture.png`.

::: careful
The template has a line that points to `img/example.png`. Delete that line, or replace it with one of your own pictures. The check reports a missing picture otherwise.
:::

Leave `id: "TBD"` in the header. Your lead will replace it with a number.

## Step 2. Commit to your branch

In the terminal, from the `NSDF-Data` folder:

```
git checkout student-yourname
git add notes/src/your-note-name.md notes/src/img
git status
git commit -m "Add note: your title"
git push -u origin student-yourname
```

::: checkpoint
Look at the list that `git status` prints before the commit. It should contain only your note and its pictures. If it shows `.bin` files, anything from the `idx` folder, or changes to other people's notes, stop and ask your lead.
:::

## Step 3. Open the pull request

On [github.com](https://github.com), open the repository. GitHub shows a yellow banner saying your branch had recent pushes. Click **Compare & pull request**. Check that:

- the **base** is `master` and the **compare** branch is `student-yourname`;
- the title says what the note is about;
- the description says, in one sentence, what question the note answers.

Click **Create pull request**.

## Step 4. Read the check

The check starts automatically and takes less than a minute. When it finishes, click **Details** on the check, and read its messages. Each message names the file and the problem. Here are the common ones and what to do:

| Message says | What to do |
|---|---|
| `header field 'X' is missing or empty` | Fill in that line of the header. |
| `status must be one of ...` | Use exactly *In progress*, *Complete* or *Outdated*. |
| `id must look like S1, S2, or TBD` | Leave `id: "TBD"`. |
| `raw HTML tag <u>` (or `<sup>`, `<sub>`, `<span>`) | Remove the formatting and keep the words. |
| `notebook link pinned to 'master'` | Replace `master` with the commit hash you committed the notebook at. |
| `placeholder COMMIT is still in the note` | Put the real commit hash in place of `COMMIT`. |
| `picture not found` | Check the file name and that the picture is in `notes/src/img/`. |

To fix a problem: edit the file on your branch and commit again. The pull request updates itself, and the check runs again.

::: tip
If the check passes, the structure is right. It cannot tell whether your numbers are right or your reading is fair. Check those yourself, and ask your lead if you are unsure.
:::

## Step 5. Wait for review

Your lead reads the note, may comment on the pull request, and may ask you for changes. Answer each comment in the pull request. When the note is ready, your lead gives it a number and merges it.

## After the merge

- The site builds your page automatically. Check the front page after a few minutes: your note appears in the **Student notes** table at the bottom.
- The page is at `notes/student-<name>.html` on the site.

## Changing a note later

Make the change on your branch, open a new pull request (or add to the open one), and let the check run again. Update the **date** line and, if the conclusion has changed, the **Status** line. If a result was wrong, say so in the note, with the date, as guide 3 explains. Do not delete a published note to hide a mistake.

## Session Info

Guide version 2, 6 October 2026. Written for every computer. Please tell the project lead where a step was unclear.

## Where to get help

**Anthony Villano**, project lead: <anthony.villano@ucdenver.edu>

When you write, include the pull request number, the message the check gave, and the step you are stuck on.

## Key links

- Pull requests: <https://github.com/villano-lab/NSDF-Data/pulls>
- Notes site: <https://villano-lab.github.io/NSDF-Data/>
- Repository: <https://github.com/villano-lab/NSDF-Data>
