# IssueTitleAI

![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![AI-Powered](https://img.shields.io/badge/AI--Powered-yes-green)

A GitHub Action that uses AI to automatically improve issue titles, making them more descriptive, actionable, and discoverable.

## 🌟 Features

- **Smart Title Processing**: Analyzes GitHub issue titles and suggests improvements based on the issue body
- **AI Integration**: Works with multiple AI providers (Gemini, OpenAI, or Deepseek)
- **Label Management**: Skips issues that already have a "titled" label and adds the label after processing
- **Flexible Configuration**: Run on schedule, manually, or automatically when issues are created
- **Operation Modes**: Choose between suggestion-only or automatic update mode

## 🚀 How It Works

1. The action scans open issues in your repository
2. Skips any issues already labeled with "titled"
3. For each unlabeled issue, it:
   - Analyzes the title and description
   - Generates an improved title using AI
   - Either updates the title automatically or adds a suggestion comment
   - Adds a "titled" label to prevent re-processing in future runs

## ⚙️ Setup

> I have tested with gemini-2.0-flash and deepseek-chat models which work well for this purpose.

1. **Get an API key** from one of the supported AI providers:
   - [OpenAI's platform](https://platform.openai.com/)
   - [Google AI Studio](https://aistudio.google.com/apikey)
   - [Deepseek](https://platform.deepseek.com/api_keys)
2. **Add your API key to your repository secrets**:
   - Go to your repository > Settings > Secrets and variables > Actions
   - Add a new repository secret named `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `DEEPSEEK_API_KEY` with your API key

3. **Create a workflow file** in your repository at `.github/workflows/issue-title-ai.yml`

## 📋 Usage

Here's an example workflow configuration:

```yaml
name: Improve Issue Titles
on:
  # Run hourly
  schedule:
    - cron: '0 * * * *'
  # Allow manual trigger
  workflow_dispatch:
  # Run when issues are created
  issues:
    types: [opened]
jobs:
  improve-titles:
    runs-on: ubuntu-latest
    steps:
      - name: Improve Issue Titles
        uses: horw/issue-title-ai@v0.1.2b
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          # Choose one of these API keys based on your preference
          # openai-api-key: ${{ secrets.OPENAI_API_KEY }}
          gemini-api-key: ${{ secrets.GEMINI_API_KEY }}
          # deepseek-api-key: ${{ secrets.DEEPSEEK_API_KEY }}
          days-to-scan: 7
          auto-update: false
          max-issues: 100
          model: gemini-2.0-flash
```

Or you can check this [example](./.github/workflows/example.yml)

## ⚙️ Configuration Options

| Option             | Description                                                                                                                                                                   | Default                                                                         |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| `github-token`     | GitHub token for authentication                                                                                                                                               | Required                                                                        |
| `openai-api-key`   | OpenAI API key (if using OpenAI)                                                                                                                                              | Optional                                                                        |
| `gemini-api-key`   | Gemini API key (if using Gemini)                                                                                                                                              | Optional                                                                        |
| `deepseek-api-key` | Deepseek API key (if using Deepseek)                                                                                                                                          | Optional                                                                        |
| `days-to-scan`     | Number of days to look back for issues                                                                                                                                        | `7`                                                                             |
| `auto-update`      | Automatically update titles if `true`, otherwise just suggest                                                                                                                 | `false`                                                                         |
| `apply-to-closed`  | Process both open and closed issues if `true`. By default, only open issues are processed                                                                                     | `false`                                                                         |
| `max-issues`       | Maximum number of issues to process per run                                                                                                                                   | `100`                                                                           |
| `required-labels`  | Filter issues by specific labels (comma-separated). Only issues with at least one of the specified labels will be processed                                                   | None (process all issues)                                                       |
| `ai-provider`      | AI provider to use: 'openai', 'gemini', or 'deepseek'                                                                                                                         | Auto-detected based on provided keys                                            |
| `model`            | AI model to use                                                                                                                                                               | `gpt-4` for OpenAI, `gemini-2.0-flash` for Gemini, `deepseek-chat` for Deepseek |
| `skip-label`       | Label to mark processed issues                                                                                                                                                | `titled`                                                                        |
| `prompt`           | Custom prompt for the AI model                                                                                                                                                | [None](#Prompt and Style)                                                       |
| `style`            | Predefined prompt. To view available prompts, refer to the `styles` folder `https://github.com/horw/issue-title-ai/tree/main/styles`                                          | "summary"                                                                       |
| `verbose`          | When enabled, prints detailed information, including input, response, and token usage                                                                                         | false                                                                           |
| `strip-characters` | Allows removing unwanted characters (e.g., quotes) from the beginning and end of the response                                                                                 | ""                                                                              |
| `quiet`            | By default, auto-update adds a comment to your pull request. You can skip this behavior by setting this parameter to 'true', which will prevent the comment from being added. | `false`                                                                         |

### Prompt and Style

You can use the `style` option to apply a predefined prompt.
A few prompt styles are already available for use: `summary`, `order`, and `offense`.
For the full list, visit: [styles folder](https://github.com/horw/issue-title-ai/tree/main/styles).
Contributions are welcome—feel free to add your own prompt file and open a pull request!

By default, the `summary` style is used.

If you prefer to directly provide a custom prompt without adding it to the `styles` folder, use the `prompt` option instead.

When creating a custom prompt, you can use `{original_title}` and `{issue_body}` as placeholders to insert the relevant data.

## 🏷️ Label Management

IssueTitleAI uses a label system to track processed issues:

- Issues with the "titled" label are automatically skipped
- After processing an issue, the "titled" label is added
- This prevents duplicate processing and allows for easy filtering of processed issues

## 🧪 Testing and Development

The project uses the following development tools:

- **Ruff**: For linting and code formatting
- **pytest**: For unit tests with coverage reporting
- **pre-commit**: For automated code quality checks
- **mypy**: For static type checking

## 🔄 Running Locally

To run the tool locally for testing or development:

1. Clone the repository:

   ```bash
   git clone https://github.com/horw/issue-title-ai.git
   cd issue-title-ai
   ```

2. Install requirements:

   ```bash
   pip install -e ".[dev]"
   ```

3. Set environment variables and run the main script:

   ```bash
   export INPUT_GITHUB-TOKEN=your_github_token
   # Use one of these based on your preferred AI provider
   export INPUT_OPENAI-API-KEY=your_openai_api_key
   # export INPUT_GEMINI-API-KEY=your_gemini_api_key
   # export INPUT_DEEPSEEK-API-KEY=your_deepseek_api_key
   export GITHUB_REPOSITORY=owner/repo
   python src/main.py
   ```

## 📃 License

[MIT License](LICENSE)

## 👥 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run the tests: `pytest`
5. Commit your changes: `git commit -m 'Add my feature'`
6. Push to the branch: `git push origin feature/my-feature`
7. Open a Pull Request
