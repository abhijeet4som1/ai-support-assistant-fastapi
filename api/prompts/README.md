# Prompt templates

Every piece of fixed text the api sends to the model lives here, so a wording change is a
one-file diff that can be reviewed without reading TypeScript. `src/rag/prompt.ts` only
assembles these templates with the dynamic parts of a turn (retrieved sections, corrections,
history, the customer message).

| File                  | Sent as                                                    | Placeholders      |
| --------------------- | ---------------------------------------------------------- | ----------------- |
| `chat-system.md`      | System prompt of every chat turn                           | `{{companyName}}` |
| `chat-no-sections.md` | The `<guideline_sections>` block when nothing was retrieved | –                 |
| `chat-summary-ack.md` | The model turn after a `<conversation_summary>` block      | –                 |
| `summary-system.md`   | System prompt of the rolling-summary call                  | –                 |

Placeholders are `{{name}}`. Rendering fails at start-up if a template still contains a
placeholder after substitution or if a value is passed for a placeholder that does not exist,
so a typo cannot reach the model. Files are read once when the api starts; restart after editing.

These files are excluded from Prettier so the exact text, including numbering and line breaks,
is what the model receives. `src/rag/prompt.test.ts` and `src/rag/templates.test.ts` check the
rendered output; `docs/evaluation-report.md` records how prompt changes were evaluated.
