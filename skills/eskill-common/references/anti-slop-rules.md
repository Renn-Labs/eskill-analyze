# Anti-Slop Rules (NON-NEGOTIABLE)

These rules override all other instructions during execution:

1. **Build the simplest thing that works.** No abstractions until the third time you need them. Three similar lines > one premature helper function.
2. **Don't add what wasn't asked for.** No bonus features, no "while we're here" refactors, no comments on code you didn't write, no docstrings on internal functions.
3. **No ceremony code.** No empty error handlers "just in case", no unused interfaces, no config files for one value, no feature flags for unreleased features.
4. **Read before you write.** Understand the existing patterns. Match them. Don't introduce a new pattern when one exists.
5. **One task = one thing.** If a task balloons, note the extra work as a new task. Don't scope-creep mid-task.
6. **Verify it actually works.** Run the relevant test/build/lint after each task. A committed file that breaks the build is worse than no commit.
7. **Prefer editing over creating.** Extend existing files before creating new ones. 90% of tasks should modify existing code, not generate new files.
8. **Delete > Comment.** If something is unused, remove it. Don't comment it out "for reference."
9. **No AI tells.** No "// Added for better user experience", no "Enhanced version", no "Comprehensive solution". Just write the code.
10. **Quality gate**: After each task, ask: "Would a senior engineer approve this PR?" If no, fix it before committing.
