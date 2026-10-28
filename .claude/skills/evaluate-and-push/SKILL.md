---
name: evaluate-and-push
description: Review the uncommitted work, split it into separate logical commits and push them to main. Run only when the user types /evaluate-and-push.
disable-model-invocation: true
---
# Evaluate and push

Turn everything that is uncommitted in the working tree into a clean series of commits, then push them to `origin`. The user asked for this by running the command, so commit and push without asking for confirmation, unless one of the stop conditions below applies.

## 1. Gather

- Check the branch with `git branch --show-current`. If it is not `main`, stop and ask.
- if you notice any changes made by user, create a short consicise message of what they changed and in which file, and what should you do with it.
- Collect the work: `git status`, `git diff`, `git diff --cached`, and the untracked files (`git ls-files --others --exclude-standard`). Read the untracked files too, not just their names.
- Run `git fetch origin`, then `git log --oneline origin/main..HEAD` to find local commits that are not pushed yet. Leave them as they are; they go out with the push.
- If there is nothing to commit and nothing to push, say so and stop.

## 2. Evaluate

Read the whole diff before grouping it. Stop and ask the user instead of committing when you find:

- secrets: API keys, tokens, passwords, `.env` files, private personal data;
- files that don't belong in the repo: `__pycache__/`, `.DS_Store`, `node_modules/`, editor folders, logs, throwaway test scripts. Suggest a `.gitignore` entry instead;
- broken or unfinished work: merge conflict markers, syntax errors, leftover debug prints, `TODO` stubs in place of code.

Run quick checks on what changed:

- changed `.py` files: `python -m py_compile <files>`;
- changes in `Frontend/`: `npm run lint` there.

If a check fails, report the output and ask whether to commit anyway. PDFs, `.doc`/`.docx` forms and `.jpg` maps in `baza/` are git-ignored and stay local only, so they should never show up as changes.

## 3. Group into commits

- One commit per logical change, i.e. something you can describe in one sentence. Don't make one commit per file, and don't put everything into one.
- Use the prefixes from CLAUDE.md: `feat:`, `fix:`, `chore:`, and `data:` for knowledge-base content in `baza/`.
- Ommit adding line: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Put a `CLAUDE.md` or docs update that describes a code change in the same commit as that code.
- Order the commits so each one makes sense on its own (e.g. the backend change before the frontend change that uses it).
- When one file holds changes that belong to different commits, stage only the relevant hunks: write a partial patch and apply it with `git apply --cached <patch>` (interactive `git add -p` does not work here). Keep patches in the scratchpad, not in the repo.
- Before each commit, check `git diff --cached --stat` so it holds exactly what you planned.
- Write messages in English, in the style of `git log --oneline -15`: a short imperative subject after the prefix, plus a body only when the reason isn't obvious from the diff.
- before pushing, check current branches in repo and ask user whether they want their code pushed to each of branch or create a new one.pl

## 4. Push

- Before the first commit, print the plan as a short list: each message with its files.
- After committing, print out all commits with messages as table and ask user how do they want they commits pushed; if user response is default, then push them all to main.
- If the push is rejected , run `git pull --rebase origin main` and push again. On a rebase conflict, run `git rebase --abort`, stop, and tell the user.
- Never use `--force`, `--no-verify` or `git commit --amend`, and never rewrite commits that are already on `origin`.

## 5. Report

Finish with the pushed commits (short hash + message), plus anything you left uncommitted on purpose and why.
