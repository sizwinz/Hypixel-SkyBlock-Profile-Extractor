# Contributing to SkyBlock Profile Extractor

🎉 Thank you for considering contributing to the SkyBlock Profile Extractor! We welcome contributions from the community to make this tool even better.

## 🌟 Ways to Contribute

### 🐛 Bug Reports
- Use the [GitHub Issues](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues) page
- Include detailed steps to reproduce the issue
- Mention your operating system and script version
- Provide error messages if any

### 💡 Feature Suggestions
- Open a [GitHub Issue](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues) with the "enhancement" label
- Describe the feature and why it would be useful
- Consider implementation challenges

### 📝 Documentation
- Improve README clarity
- Add usage examples
- Fix typos or grammar
- Translate to other languages

### 🔧 Code Contributions
- Fix bugs
- Add new features
- Improve performance
- Add new API endpoints
- Enhance error handling

## 🚀 Getting Started

### Prerequisites
- Git
- PowerShell 5.0+ (for PowerShell development)
- Python 3.6+ (for Python development)
- Basic knowledge of Hypixel SkyBlock

### Development Setup

1. **Fork the repository**
   ```bash
   # Click the "Fork" button on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/SkyBlock-Profile-Extractor.git
   cd SkyBlock-Profile-Extractor
   ```

3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Make your changes**
   - Follow the coding standards below
   - Test your changes thoroughly
   - Update documentation if needed

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: descriptive commit message"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Provide a clear description of your changes

## 📋 Coding Standards

### PowerShell
- Use `PascalCase` for functions and parameters
- Use `$camelCase` for variables
- Include comment-based help for functions
- Use `Write-Host` with colors for user output
- Include error handling with try-catch blocks

### Python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include docstrings for functions and classes
- Use meaningful variable and function names
- Include proper error handling

### General
- Add comments for complex logic
- Keep functions focused and small
- Use consistent naming conventions
- Include unit tests when possible

## 🧪 Testing

Before submitting a pull request:

### Manual Testing
1. Test with valid usernames
2. Test with invalid usernames
3. Test with different profile configurations
4. Test error scenarios (network issues, API limits)
5. Verify all output files are created correctly

### Test Cases to Consider
- New players with minimal data
- Advanced players with full profiles
- Players with API access disabled
- Network timeout scenarios
- Invalid input handling

## 📁 Project Structure

```
SkyBlock-Profile-Extractor/
├── README.md              # Main documentation
├── CONTRIBUTING.md        # This file
├── LICENSE               # MIT license
├── extract-profile.ps1   # PowerShell version
├── extract_profile.py    # Python version
├── requirements.txt      # Python dependencies
├── .github/              # GitHub workflows and templates
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
└── docs/                 # Additional documentation
```

## 🔍 Code Review Process

1. **Automated Checks**
   - Code must pass any automated tests
   - No major security vulnerabilities
   - Follows basic style guidelines

2. **Manual Review**
   - Code quality and readability
   - Adherence to project standards
   - Proper error handling
   - Documentation completeness

3. **Testing Verification**
   - Reviewer tests the changes
   - Verifies functionality works as expected
   - Checks edge cases

## 🏷️ Commit Message Guidelines

Use clear, descriptive commit messages:

```
Type: Short description (50 chars or less)

Optional longer description explaining what and why.
Wrapped at 72 characters.
```

### Types:
- `Add:` New features or files
- `Fix:` Bug fixes
- `Update:` Changes to existing functionality
- `Remove:` Deleted features or files
- `Docs:` Documentation changes
- `Style:` Code formatting (no functional changes)
- `Refactor:` Code restructuring
- `Test:` Adding or updating tests

### Examples:
```
Add: Support for multiple profile selection
Fix: Handle API timeout errors gracefully
Update: Improve error messages for 403 responses
Docs: Add installation guide for macOS users
```

## 📞 Getting Help

If you need help while contributing:

- 💬 [GitHub Discussions](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/discussions)
- 🐛 [GitHub Issues](https://github.com/Sahaj33-op/SkyBlock-Profile-Extractor/issues)
- 📧 Contact maintainers through GitHub

## 🎯 Priority Areas

We're especially interested in contributions for:

### High Priority
- 🐛 Bug fixes for existing issues
- 📱 Cross-platform compatibility improvements
- 🔒 Enhanced error handling and validation
- 📊 Data analysis tools and examples

### Medium Priority
- 🎨 UI/UX improvements for command-line interface
- 📈 Performance optimizations
- 🌐 Internationalization (i18n) support
- 📝 Additional documentation and examples

### Future Ideas
- 🖥️ GUI version of the extractor
- 📊 Built-in data visualization
- 🤖 Integration with popular Discord bots
- 📱 Mobile app version
- 🔄 Automated profile monitoring

## 📜 Code of Conduct

We follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/0/code_of_conduct/). Please be respectful and inclusive in all interactions.

### Our Standards

✅ **Encouraged:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what's best for the community
- Showing empathy towards other community members

❌ **Not Acceptable:**
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing private information without permission
- Other conduct inappropriate in a professional setting

## 🙏 Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- README acknowledgments section

Thank you for helping make SkyBlock Profile Extractor better for everyone! 🚀
