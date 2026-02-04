# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Real-time WebSocket updates for sessions and logs
- Plugin system for custom dashboard tabs
- Export functionality for session transcripts
- Advanced filtering and search across all data

## [0.2.4] - 2026-02-04

### 🚀 **PUBLIC RELEASE CANDIDATE**

This version marks the feature-complete release candidate for the public launch.

### Added
- **Enhanced Cost Tracking**: Multi-model pricing support (Claude Opus/Sonnet/Haiku, GPT-4, GPT-3.5)
- **Cost Warnings**: Visual alerts for high spending ($10+ daily, $50+ weekly, $200+ monthly)
- **Usage Trends**: Monthly cost predictions based on recent spending patterns
- **CSV Export**: Download usage data for external analysis
- **Trend Indicators**: Visual arrows showing increasing/decreasing/stable usage patterns

### Improved
- More accurate cost calculations with 60/40 input/output token ratio assumptions
- Enhanced warning panels with proper error/warning styling
- Better fallback cost estimates when OTLP data unavailable

## [0.2.3] - 2026-02-04

### Added
- **Dark/Light Theme Toggle**: Full dual-theme support with smooth transitions
- **Theme Persistence**: Saves user preference in localStorage
- **CSS Variables**: Complete color system refactor for maintainability

### Improved
- Light theme with carefully chosen contrast ratios
- Moon/sun toggle button in navigation bar
- All components update smoothly with 0.3s transitions

## [0.2.2] - 2026-02-04

### Added
- **Mobile-Responsive Flow Visualization**: Touch scrolling and viewport optimization
- **Particle System Optimization**: Particle pooling for 60fps performance
- **Enhanced Animations**: Smoother trails with CSS transitions and blur effects
- **Performance Scaling**: Adaptive particle counts (3 mobile, 8 desktop)

### Improved
- Flow canvas responsiveness across all screen sizes
- Visual hierarchy with startup animation hints
- Reduced memory usage through particle recycling

## [0.2.1] - 2026-02-04

### Added
- **CONTRIBUTING.md**: Comprehensive contributor guidelines
- **Development Setup**: Clear instructions for contributors
- **Code Style Guidelines**: Python 3.8+, PEP 8 standards
- **Testing Requirements**: Auto-detection and CLI validation steps

### Improved
- Bug report and feature request templates
- PR review process documentation

## [0.2.0] - 2026-02-04

### 🎯 **PIP INSTALLABLE RELEASE**

### Added
- **setup.py**: Full pip installation support with entry points
- **Console Script**: `openclaw-dashboard` command for global access
- **requirements.txt**: Explicit Flask dependency management
- **install.sh**: One-liner installation script

### Improved
- Entry point works correctly: `openclaw-dashboard --help` 
- Same functionality as direct execution
- Proper packaging for PyPI distribution

## [0.1.9] - 2026-02-04

### Added
- **Full Auto-Detection**: Workspace, logs, and sessions discovery
- **Standalone Execution**: Works from any directory (`cd /tmp && python3 dashboard.py`)
- **Generic Paths**: No hardcoded Moltbot-specific paths
- **Enhanced CLI**: Proper argument handling with fallbacks

### Changed
- **BREAKING**: Removed all hardcoded `/home/vivek/clawd` paths
- Log directory fallback: `/tmp/openclaw` instead of `/tmp/moltbot`
- Help text shows "auto-detected" instead of hardcoded defaults

### Fixed
- Auto-detection works reliably across different execution contexts
- CLI arguments properly override auto-detected values

## [0.1.5] - 2026-02-04

### Added
- **Comprehensive README**: Badges, installation guide, feature matrix
- **Comparison Table**: vs Grafana, Datadog, custom solutions
- **Screenshots**: Flow visualization reference (flow.jpg)
- **OTLP Setup**: OpenTelemetry receiver configuration guide

### Improved
- Installation instructions with emoji formatting
- "Star this repo" call-to-action
- Feature breakdown by dashboard tab
- Quick Start section with better formatting

## [0.1.0] - 2026-02-04

### 🎉 **INITIAL RELEASE**

### Added
- **Single-File Dashboard**: Complete Flask application in `dashboard.py` (118KB)
- **Multi-Tab Interface**: Overview, Sessions, Crons, Logs, Memory, Flow
- **Auto-Detection System**: Finds OpenClaw workspace and data automatically
- **CLI Interface**: `--help`, `--port`, `--workspace` arguments
- **MIT License**: Open source licensing
- **Git Repository**: Version control with proper .gitignore

### Core Features
- **Overview Tab**: System status, usage stats, cost tracking
- **Sessions Tab**: Active and historical session management
- **Crons Tab**: Scheduled job monitoring and execution
- **Logs Tab**: Real-time log parsing with humanized timestamps
- **Memory Tab**: Clickable memory file browser with search
- **Flow Tab**: Animated SVG visualization of system architecture

### Technical
- **Zero Config**: Works out of the box with sensible defaults
- **Lightweight**: Single file, minimal dependencies (Flask only)
- **Cross-Platform**: Python 3.8+ compatibility
- **Self-Contained**: No external databases or services required

---

## Version History Summary

| Version | Date       | Major Features                                      |
|---------|------------|-----------------------------------------------------|
| 0.2.4   | 2026-02-04 | **PUBLIC RC**: Enhanced cost tracking, CSV export  |
| 0.2.3   | 2026-02-04 | Dark/light themes, persistence                     |
| 0.2.2   | 2026-02-04 | Mobile flow, particle optimization                 |
| 0.2.1   | 2026-02-04 | Contributing docs, guidelines                       |
| 0.2.0   | 2026-02-04 | **Pip installable**, console scripts               |
| 0.1.9   | 2026-02-04 | **Generic**: Auto-detection, standalone execution  |
| 0.1.5   | 2026-02-04 | Professional README, documentation                 |
| 0.1.0   | 2026-02-04 | **Initial**: Single-file dashboard, core features  |

---

## Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backward compatible)
- **PATCH** version: Bug fixes (backward compatible)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT License](LICENSE) - see LICENSE file for details.