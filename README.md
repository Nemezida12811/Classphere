## Team Git Workflow

Each team member works in their **own branch**.

⚠️ Do not develop directly in the `main` branch.

The `main` branch should contain only stable and reviewed code.

---

## 1. Create your personal branch

Each team member should create a branch using their GitLab username or name.

Example:

```bash
git switch -c your-name
```

For example:

```bash
git switch -c john
```

Then push the branch to GitLab:

```bash
git push -u origin your-name
```

This only needs to be done once.

After that, your branch will also appear on GitLab.

---

## 2. Check which branch you are currently using

Before changing any files, check your current branch:

```bash
git branch
```

Example:

```text
  main
* john
```

The `*` shows your current branch.

Make sure you are working in **your own branch**, not `main`.

To switch to your branch:

```bash
git switch your-name
```

---

## 3. Working on the project

Make your changes normally.

When you want to save your work to Git:

```bash
git status
```

Add changed files:

```bash
git add .
```

Create a commit:

```bash
git commit -m "Add temperature sensor support"
```

Push your changes to GitLab:

```bash
git push
```

Typical workflow:

```bash
git add .
git commit -m "Description of changes"
git push
```

---